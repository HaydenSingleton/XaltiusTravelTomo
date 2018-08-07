import os
import sys
from datetime import datetime
import time
from urllib import parse

import pandas as pd
import requests
import sqlalchemy
from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.common.exceptions import (NoSuchElementException,
                                        WebDriverException)
from selenium.webdriver.chrome.options import Options


testing = False  # Flag to shorten loop execution
test_length = 2  # Number of pages and links per page to search during testing


# Global variables
column_titles_h = ['Title', 'Rating', 'Review Count', 'Phone Number', 'Address', 'Locality', 'Country', 'Stars', 'Keywords', 'Date Generated']
column_titles_r = ['Title', 'Rating', 'Review Count', 'Phone Number', 'Address', 'Locality', 'Country', 'Cusines', 'Date Generated']
column_titles_a = ['Title', 'Rating', 'Review Count', 'Phone Number', 'Address', 'Locality', 'Country', 'Suggested Duration', 'Price', 'Description', 'Keywords', 'Categories','Date Generated']
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36'}
# driver_path = os.path.normpath("C:\\Users\\Hayden\\Anaconda3\\selenium\\webdriver")
get_hotels, get_resturants, get_attractions = False, False, True


def main():
    print(time.strftime("Starting at %H:%M:%S", time.localtime()))

    # Get input
    if len(sys.argv) < 2:
        input_list = ['singapore']
    else:
        input_list = sys.argv[1:]
    queries = [s.capitalize() for s in input_list]
    print("Searching: [" + ", ".join(queries) + "]")

    # Set up
    genres = 'Hotels', 'Resturants', 'Attractions'
    if testing:
        print("Testing Enabled".center(80, '-'), end="")
    try:
        os.remove("geckodriver.log")
    except OSError:
        pass
    try:
        os.mkdir("data")
    except OSError:
        pass

    os.chdir("data")

    # Create sqlalchemy engine for connecting sql server
    try:
        quoted = parse.quote_plus('DRIVER={};Server={};Database={};UID={};PWD={};TDS_Version=8.0;Port=1433;'.format("ODBC Driver 13 for SQL Server", "sql-stg-sc-travel.civfwvdbx0g6.ap-southeast-1.rds.amazonaws.com", "tripAdvisor", "traveltomo", "traveltomo123"))
        engine = sqlalchemy.create_engine('mssql+pyodbc:///?odbc_connect={}'.format(quoted))
    except Exception as e:
        print("\nFailed to connect to sql server\n", e)
        exit()

    for place in queries:
        hotels_df, resturants_df, attractions_df = search(place)
        for i, df in enumerate([hotels_df, resturants_df, attractions_df]):
            root_path = place + "_" + genres[i] + "_data.csv"
            filepath = os.path.join(os.path.abspath("data"), root_path)
            try:
                df.to_csv(path_or_buf=filepath)
            except FileNotFoundError:
                filepath = os.path.join(place+"_"+genres[i]+"_data.csv")
                try:
                    df.to_csv(path_or_buf=filepath)
                except FileNotFoundError:
                    pass

        # Append collected data to the table for Hotels, Resturants, and Attractions respectively
        try:
            hotels_df.to_sql("Hotels", con=engine, if_exists="append", index=False,
                         dtype={"Title": sqlalchemy.types.NVARCHAR(200),
                                "Rating": sqlalchemy.types.NVARCHAR(200),
                                "Review Count": sqlalchemy.types.NVARCHAR(200),
                                "Phone Number": sqlalchemy.types.NVARCHAR(200),
                                "Address": sqlalchemy.types.NVARCHAR(200),
                                "Locality": sqlalchemy.types.NVARCHAR(200),
                                "Country": sqlalchemy.types.NVARCHAR(200),
                                "Stars": sqlalchemy.types.NVARCHAR(255),
                                "Keywords": sqlalchemy.types.NVARCHAR(200),
                                "Date Generated": sqlalchemy.types.NVARCHAR(200)
                                })
        except ValueError:
            print("Hotels table already found in sql database")
        except Exception as e:
            print("Error inserting to hotels:", e)

        try:
            resturants_df.to_sql("Resturants", con=engine, if_exists='fail', index=False,
                                dtype={"Title": sqlalchemy.types.NVARCHAR(200),
                                        "Rating": sqlalchemy.types.NVARCHAR(200),
                                        "Review Count": sqlalchemy.types.NVARCHAR(200),
                                        "Phone Number": sqlalchemy.types.NVARCHAR(200),
                                        "Address": sqlalchemy.types.NVARCHAR(200),
                                        "Locality": sqlalchemy.types.NVARCHAR(200),
                                        "Country": sqlalchemy.types.NVARCHAR(200),
                                        "Cusines": sqlalchemy.types.NVARCHAR(200),
                                        "Date Generated": sqlalchemy.types.NVARCHAR(200)
                                        })
        except ValueError:
            print("Resturants table already found in sql database")
        except Exception as e:
            print("Error inserting to resturants:", e)

        try:
            attractions_df.to_sql("Attractions", con=engine, if_exists="replace", index=False,
                              dtype={"Title": sqlalchemy.types.NVARCHAR(200),
                                     "Rating": sqlalchemy.types.NVARCHAR(200),
                                     "Review Count": sqlalchemy.types.NVARCHAR(200),
                                     "Phone Number": sqlalchemy.types.NVARCHAR(200),
                                     "Address": sqlalchemy.types.NVARCHAR(200),
                                     "Locality": sqlalchemy.types.NVARCHAR(200),
                                     "Country": sqlalchemy.types.NVARCHAR(200),
                                     "Suggested Duration": sqlalchemy.types.NVARCHAR(200),
                                     "Price": sqlalchemy.types.NVARCHAR(200),
                                     "Description": sqlalchemy.types.NVARCHAR(200),
                                     "Keywords": sqlalchemy.types.NVARCHAR(200),
                                     "Categories": sqlalchemy.types.NVARCHAR(200),
                                     "Date Generated": sqlalchemy.types.NVARCHAR(200),
                                     })
        except ValueError:
            print("Attractions table already found in sql database")
        except Exception as e:
            print("Error inserting to attractions:", e)

    print(time.strftime("Finished at %H:%M:%S\n", time.localtime()))


def search(query):
    h_df, r_df, a_df = pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    # try:
    print("\nBeginning search in", query)
    # Set up browser
    chrome_options = Options()
    chrome_options.add_argument('--log-level=3')
    chrome_options.add_argument('--ignore-certificate-errors')
    chrome_options.add_argument('--ignore-ssl-errors')
    driver = webdriver.Chrome(chrome_options=chrome_options)
    # os.environ['MOZ_HEADLESS'] = '1'
    # driver = webdriver.Firefox()
    driver.set_page_load_timeout(10)

    # Navigate to trip TripAdvisor, starting with hotels
    main_url = "https://www.tripadvisor.com/"
    # This should redirect to the correct local domain as needed (ex- .com.sg) AFAIK
    try:
        driver.get(main_url)
        driver.find_element_by_id("global-nav-hotels").click()
    except NoSuchElementException:
        driver.quit()
        print("Unable to access website")
        print("Are you connected to internet ?")
        exit(0)
    driver.find_element_by_class_name("typeahead_input").send_keys(query)
    driver.find_element_by_class_name("submit_text").click()
    time.sleep(0.5)

    if get_hotels:
        data = get_data(driver, "Hotels")
        h_df = pd.DataFrame(data, columns=list(column_titles_h))

    if get_resturants:
        driver.find_element_by_id("global-nav-restaurants").click()
        data2 = get_data(driver, "Resturants")
        r_df = pd.DataFrame(data2, columns=list(column_titles_r))

    if get_attractions:
        driver.find_element_by_id("global-nav-attractions").click()
        data3 = get_data(driver, "Attractions")
        a_df = pd.DataFrame(data3, columns=list(column_titles_a))

    driver.quit()
    # except Exception as e:
    #     print("\nFatal Error, quiting...")
    #     driver.quit()
    #     print(e)
    #     quit()
    return h_df, r_df, a_df


def get_data(driver, genre, max_pages=10):
    time.sleep(0.1)
    try:
        outersoup = BeautifulSoup(driver.page_source, 'html5lib')
        pagelinks = outersoup.find("div", class_="pageNumbers")
        total_pages = pagelinks.find_all("a")[-1]
        max_pages = int(total_pages.text)
        print("Found {} pages of {}".format(str(max_pages), genre))
        max_pages = 20
    except Exception as e:
        print("Can't tell how many pages there are, searching", max_pages, "--", e)

    # Temporary #
    if testing:
        max_pages = test_length

    date_gen = datetime.today().replace(microsecond=0)
    data = []
    try:
        for page in range(max_pages):
            time.sleep(0.1)
            try:
                nb = driver.find_elements_by_xpath("//*[contains(text(), 'Next')]")[-1]
                next_page_loc = nb.get_attribute('href')
            except Exception:
                next_page_loc = ""

            soup = BeautifulSoup(driver.page_source, 'html5lib')
            if genre is "Hotels":
                results = soup.find("div", class_="relWrap")
                partials = results.find_all("div", class_="listing_title")

            elif genre is "Resturants":
                results = soup.find("div", id="EATERY_SEARCH_RESULTS")
                places = results.find_all("div", class_="listing")
                partials = [p.find("div", class_="title") for p in places]

            else:
                results = soup.find("div", id="FILTERED_LIST")
                partials = results.find_all("div", class_="listing_title")

            links = []
            for p in partials:
                try:
                    if "http" not in p.a['href']:
                        links.append("https://www.tripadvisor.com" + p.a['href'])
                    else:
                        links.append(p.a['href'])
                except AttributeError:
                    continue
            print(f"Found {len(links)} links on page {page+1}/{max_pages} =>", end="")

            # driver.minimize_window()
            for i, link in enumerate(links):
                if (i == test_length) and testing:
                    break
                time.sleep(0.1)
                try:
                    newrow = scrape_article(link, genre)
                except StopIteration:
                    continue

                newrow.append(date_gen)
                data.append(newrow)
            print()

            try:
                driver.get(next_page_loc)
            except Exception as e:
                print("Error: could not click next -)")
                print(e)
                break

        print("\nDone with", genre)
        # driver.maximize_window()
    except WebDriverException as e:
        print("STOPPING EARLY BC:", e, e.__class__)
    return data

# Implementation of a switch case to call the correct scraping function
def scrape_article(url, genre):
    try:
        soup = BeautifulSoup(requests.get(url, headers=headers).text, 'html5lib')
    except ConnectionError:
        print("Connection error".center(80, '='))
        time.sleep(10)
        try:
            soup = BeautifulSoup(requests.get(url, headers=headers).text, 'html5lib')
        except ConnectionError:
            time.sleep(10)
            raise StopIteration
            # Script is being blocked, wait and then raise and error back in get_data function

    switch = {
        "Hotels": scrape_hotel,
        "Resturants": scrape_resturant,
        "Attractions": scrape_attraction
    }
    func = switch.get(genre, lambda input: print("Invalid genre"))
    return func(url, soup)

def scrape_hotel(url, soup):
    print(".", end="", flush=True)
    # Scrape data, filling missing values with None
    try:
        title = soup.find('h1', id='HEADING').text
    except AttributeError:
        title = None
    try:
        review_count = soup.find('span', class_='reviews_header_count').text.strip('()')
    except AttributeError:
        review_count = None
    try:
        rating = soup.find("span", class_="overallRating").text
    except AttributeError:
        rating = None
    try:
        phone = soup.find("div", class_=['phone']).text
    except AttributeError:
        phone = None
    try:
        address = soup.find("span", class_="street-address").text.rstrip(',')
    except AttributeError:
        address = None
    try:
        exaddress = soup.find("span", class_="extended-address").text
    except AttributeError:
        exaddress = None
    try:
        local = soup.find("span", class_="locality").text.replace(',', '')
    except AttributeError:
        local = None
    try:
        country = soup.find("span", class_="country-name").text
    except AttributeError:
        country = None
    # try:
    #     review_containers = soup.find_all("div", class_="review-container")
    #     user_reviews = {ur.find("div", class_="info_text").text: ur.find("p", class_="partial_entry").text for ur in review_containers}
    # except AttributeError:
    #     user_reviews = None

    try:
        keywords_container = soup.find("div", class_=["prw_rup prw_filters_tag_cloud", "ui_tagcloud_group"]).text.split("\n")[1:]  # Convert to a list
        keywords = {w.split('"')[1]: w.split()[-2] for w in keywords_container if w.strip()}  # Seperate tag and count and put into dict
    except AttributeError:
        keywords = None
    try:
        try:
            star_count = soup.find("div", class_="starRatingWidget").text.split(".")[1]
        except IndexError:
            star_count = soup.find("div", class_="starRatingWidget").text
    except AttributeError:
        star_count = None

    # Clean data
    if address is None:
        address = exaddress

    if phone:
        for c in phone:
            if c.isalpha():
                phone = None
                break

    # Put data into a list and return it
    row = [title, rating, review_count, phone, address, local, country, star_count, str(keywords)]
    return row


def scrape_resturant(url, soup):
    print(".", end="", flush=True)
    # Scrape data, filling missing values with None
    try:
        title = soup.find('h1', id='HEADING').text
    except AttributeError:
        title = None
    try:
        review_count = soup.find('span', class_='reviews_header_count').text.strip('()')
    except AttributeError:
        review_count = None
    try:
        rating = soup.find("span", class_="overallRating").text
    except AttributeError:
        rating = None
    try:
        phone = soup.find("div", class_=['phone']).text
    except AttributeError:
        phone = None
    try:
        address = soup.find("span", class_="street-address").text.rstrip(',')
    except AttributeError:
        address = None
    try:
        exaddress = soup.find("span", class_="extended-address").text
    except AttributeError:
        exaddress = None
    try:
        local = soup.find("span", class_="locality").text.replace(',', '')
    except AttributeError:
        local = None
    try:
        country = soup.find("span", class_="country-name").text
    except AttributeError:
        country = None
    try:
        rap = soup.find("div", class_="rating_and_popularity")
        cuisines = rap.find("span", class_="header_links").text.strip('"').strip()
    except AttributeError:
        cuisines = None

    # Clean data
    if address is None:
        address = exaddress

    if phone:
        for c in phone:
            if c.isalpha():
                phone = None
                break

    # Put data into a list and return it
    row = [title, rating, review_count, phone, address, local, country, cuisines]
    return row


def scrape_attraction(url, soup):
    print(".", end="", flush=True)
    # Scrape data, filling missing values with None
    try:
        title = soup.find('h1', id='HEADING').text
    except AttributeError:
        title = None
    try:
        review_count = soup.find('span', class_='reviews_header_count').text.strip('()')
    except AttributeError:
        review_count = None
    try:
        rating = soup.find("span", class_="overallRating").text
    except AttributeError:
        rating = None
    try:
        phone = soup.find("div", class_=['phone']).text
    except AttributeError:
        phone = None
    try:
        address = soup.find("span", class_="street-address").text.rstrip(',')
    except AttributeError:
        address = None
    try:
        exaddress = soup.find("span", class_="extended-address").text
    except AttributeError:
        exaddress = None
    try:
        local = soup.find("span", class_="locality").text.replace(',', '')
    except AttributeError:
        local = None
    try:
        country = soup.find("span", class_="country-name").text
    except AttributeError:
        country = None
    # try:
    #     review_containers = soup.find_all("div", class_="review-container")
    #     user_reviews = {ur.find("div", class_="info_text").text: ur.find("p", class_="partial_entry").text for ur in review_containers}
    # except AttributeError:
    #     user_reviews = None
    try:
        rec_duration = soup.find("div", class_="detail_section duration").text.split(':')[1].strip()
    except AttributeError:
        rec_duration = None
    try:
        description = soup.find("div", class_=["description", "overflow"])
        description = description.find("div", class_="text").text.strip('"')
    except AttributeError:
        description = None
    try:
        price = soup.find("span", class_="fromPrice").text.rstrip('*')
    except AttributeError:
        price = None
    try:
        keywords_container = soup.find("div", class_=["tagcloud_wrapper", "ui_tagcloud_group"]).text.split("\n")[1:]  # Convert to a list
        keywords = {w.split('"')[1]: w.split()[-2] for w in keywords_container if w.strip()}  # Seperate tag and count and put into dict
    except AttributeError:
        keywords = None
    try:
        tags = soup.find("span", class_="attraction_details").text.replace('\n', ' ')
    except AttributeError:
        tags = None


    # Clean data
    if address is None:
        address = exaddress

    if phone:
        for c in phone:
            if c.isalpha():
                phone = None
                break

    # Put data into a list and return it
    row = [title, rating, review_count, phone, address, local, country, rec_duration, price, description, keywords, tags]
    return row


if __name__ == '__main__':
    main()
