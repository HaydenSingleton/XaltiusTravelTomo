import os
import sys
import time
from datetime import datetime
from time import localtime, strftime

import pandas as pd
# from pandas import DataFrame
import requests
from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, WebDriverException
# from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options

# from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
# from selenium.webdriver.support import expected_conditions as EC
# from selenium.webdriver.support.ui import WebDriverWait

# Flag to shorten loop execution
testing = True


# Global variables
column_titles_h = ['Title', 'Rating', 'Review Count', 'Phone Number', 'Address', 'Locality', 'Country', 'Stars', 'User Reviews', 'Keywords', 'Date Generated']
column_titles_r = ['Title', 'Rating', 'Review Count', 'Phone Number', 'Address', 'Locality', 'Country', 'Cusines', 'Date Generated']
column_titles_a = ['Title', 'Rating', 'Review Count', 'Phone Number', 'Address', 'Locality', 'Country', 'Suggested Duration', 'Price', 'Description', 'User Reviews', 'Keywords', 'Date Generated']
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36'}
# driver_path = os.path.normpath("C:\\Users\\Hayden\\Anaconda3\\selenium\\webdriver")


def script():
    print(strftime("Starting at %H:%M:%S", localtime()))

    if len(sys.argv) < 2:
        input_list = ['singapore']
    else:
        input_list = sys.argv[1:]

    queries = [s.capitalize() for s in input_list]
    print("Searching: [" + ", ".join(queries), end="]\n")
    if testing:
        print("Testing Enabled".center(80,'-'), end="")
    try:
        os.remove("geckodriver.log")
    except OSError:
        pass
    genres = ['Hotels', 'Resturants', 'Attractions']
    for place in queries:
        try:
            folder_path = os.path.join("data", place)
            os.mkdir(folder_path)
        except OSError:
            pass
        dfs = list(search(place))
        for i, genre in enumerate(genres):
            root_path = place + "_" + genre + "_data.csv"
            filepath = os.path.join(os.path.abspath(folder_path), root_path)
            dfs[i].to_csv(path_or_buf=filepath)  # , columns=column_titles)
            print(strftime("Finished {} at %H:%M:%S\n".format(genre), localtime()))


def search(query):
    h_df, r_df, a_df = pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    try:
        print("\nBeginning search in", query)
        # Set up browser
        chrome_options = Options()
        chrome_options.add_argument('--log-level=3')
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument('--ignore-ssl-errors')
        driver = webdriver.Chrome(chrome_options=chrome_options)
        # os.environ['MOZ_HEADLESS'] = '1'
        # binary = FirefoxBinary('C:\\Program Files\\Mozilla Firefox\\firefox.exe', log_file=sys.stdout)
        # driver = webdriver.Firefox(firefox_binary=binary)
        driver.set_page_load_timeout(10)

        # Navigate to trip TripAdvisor, starting with hotels
        main_url = "https://www.tripadvisor.com/Hotels"
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

        data = get_data(driver, "Hotels")
        h_df = pd.DataFrame(data, columns=list(column_titles_h))

        driver.find_element_by_id("global-nav-restaurants").click()
        data2 = get_data(driver, "Resturants")
        r_df = pd.DataFrame(data2, columns=list(column_titles_r))

        driver.find_element_by_id("global-nav-attractions").click()
        data3 = get_data(driver, "Attractions")
        a_df = pd.DataFrame(data3, columns=list(column_titles_a))

        driver.quit()
    except WebDriverException:
        print("\nFatal Error, quiting...")
        driver.quit()
    return h_df, r_df, a_df


def get_data(driver, genre, max_pages=5):
    time.sleep(1)
    try:
        outersoup = BeautifulSoup(driver.page_source, 'html5lib')
        pagelinks = outersoup.find("div", class_="pageNumbers")
        total_pages = pagelinks.find_all("a")[-1]
        max_pages = int(total_pages.text)
        print("Found {} pages of {}.".format(str(max_pages), genre))
    except Exception as e:
        print("Can't tell how many pages there are, searching", max_pages, "-", e)

    # Temporary #
    if testing:
        max_pages = 5

    data = []
    date_gen = datetime.today().replace(microsecond=0)

    for page in range(max_pages):
        time.sleep(1)
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
            if i > 5 and testing:
                break
            newrow = scrape_article(link, genre)
            newrow.append(date_gen)
            data.append(newrow)
        print()

        try:
            nb = driver.find_elements_by_xpath("//*[contains(text(), 'Next')]")[-1]
            try:
                driver.get(nb.get_attribute('href'))
            except Exception as e:
                print("Failed to go past page {}/{} (Could not click next)".format(page + 1, max_pages))
                print(e)
                print(nb.get_attribute('href'))
                break
            # page_nav_links = outersoup.find("div", class_=["unified", "pagination"]).find_all("a")
            # next_page = page_nav_links[1].get("href")
            # next_page = "https://www.tripadvisor.com/" + str(next_page)
            # driver.get(next_page)
        except Exception as e:
            print("Failed to go past page {}/{} ({})".format(page + 1, max_pages, e))
            raise
    print("\nDone with", genre)
    # driver.maximize_window()
    return data


def scrape_hotel(url):
    print(".", end="", flush=True)
    # headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36'}
    soup = BeautifulSoup(requests.get(url, headers=headers).text, 'html5lib')

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
        review_containers = soup.find_all("div", class_="review-container")
        user_reviews = {ur.find("div", class_="info_text").text: ur.find("p", class_="partial_entry").text for ur in review_containers}
    except AttributeError:
        user_reviews = None

    try:
        keywords_container = soup.find("div", class_=["prw_rup prw_filters_tag_cloud","ui_tagcloud_group"]).text.split("\n")[1:]  # Convert to a list
        keywords = {w.split('"')[1]: w.split()[-2] for w in keywords_container if w.strip()}  # Seperate tag and count and put into dict
    except AttributeError:
        keywords = None
    try:
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
    row = [title, rating, review_count, phone, address, local, country, star_count, user_reviews, keywords]
    return row


def scrape_resturant(url):
    print(".", end="", flush=True)
    # headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36'}
    soup = BeautifulSoup(requests.get(url, headers=headers).text, 'html5lib')

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
    # except Exception:
    #     user_reviews = None
    # try:
    #     keywords_container = soup.find("div", class_="ui_tagcloud_group").text.split("\n")  # Convert to a list
    #     kwc = [w for w in keywords_container if w is not ""][1:]  # Remove first tag "all reviews" and empty strings
    #     keywords = {w.split('"')[1]: w.split()[-2] for w in kwc}  # Seperate tag and count and put into dict
    # except Exception:
    #     keywords = None
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


def scrape_attraction(url):
    print(".", end="", flush=True)
    # headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36'}
    soup = BeautifulSoup(requests.get(url, headers=headers).text, 'html5lib')

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
        review_containers = soup.find_all("div", class_="review-container")
        user_reviews = {ur.find("div", class_="info_text").text: ur.find("p", class_="partial_entry").text for ur in review_containers}
    except AttributeError:
        user_reviews = None
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
        keywords_container = soup.find("div", class_=["tagcloud_wrapper","ui_tagcloud_group"]).text.split("\n")[1:]  # Convert to a list
        keywords = {w.split('"')[1]: w.split()[-2] for w in keywords_container if w.strip()}  # Seperate tag and count and put into dict
    except AttributeError:
        keywords = None

    # Clean data
    if address is None:
        address = exaddress

    if phone:
        for c in phone:
            if c.isalpha():
                phone = None
                break

    # Put data into a list and return it
    row = [title, rating, review_count, phone, address, local, country, rec_duration, price, description, user_reviews, keywords]
    return row


# Implementation of a switch case to call the correct scraping function
def scrape_article(url, genre):
    switch = {
        "Hotels": scrape_hotel,
        "Resturants": scrape_resturant,
        "Attractions": scrape_attraction
    }
    func = switch.get(genre, lambda input: print("Invalid genre"))
    return func(url)


def main():
    script()


if __name__ == '__main__':
    main()
