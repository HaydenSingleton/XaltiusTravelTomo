import os
import sys
import time
from datetime import datetime
from urllib import parse

import pandas as pd
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import (NoSuchElementException,
                                        WebDriverException)
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By

## Global variables

# Flag to shorten loop execution
testing = True  

# Number of pages and links per page to search during testing
test_length = 2

genres = 'Hotels', 'Resturants', 'Attractions'

column_titles_h = ['Title', 'Rating', 'Review Count', 'Phone Number', 'Address', 'Locality', 'Country', 'Stars', 'Keywords', 'Date Generated']
column_titles_r = ['Title', 'Rating', 'Review Count', 'Phone Number', 'Address', 'Locality', 'Country', 'Cusines', 'Date Generated']
column_titles_a = ['Title', 'Rating', 'Review Count', 'Phone Number', 'Address', 'Locality', 'Country', 'Suggested Duration', 'Price', 'Description', 'Keywords', 'Date Generated']

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36'}


def main():
    print(time.strftime("Starting at %H:%M:%S", time.localtime()))

    if testing:
        print("Testing Enabled".center(80, '-'), end="")

    try:
        os.remove("geckodriver.log")
    except FileNotFoundError:
        pass

    place = 'local'

    folder_path = os.path.join("data", place)
    try:
        os.mkdir(folder_path)
    except OSError:
        pass

    dfs = search(place)
    for i, genre in enumerate(genres):
        root_path = place + "_" + genre + "_data.csv"
        filepath = os.path.join(os.path.abspath(folder_path), root_path)
        try:
            dfs[i].to_csv(path_or_buf=filepath)
        except PermissionError:
            pass

    print(time.strftime("Finished at %H:%M:%S\n", time.localtime()))


def search(query):
    h_df, r_df, a_df = pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    print("\nBeginning search in", query)
    # Set up browser
    chrome_options = Options()
    chrome_options.add_argument('--log-level=3')
    chrome_options.add_argument('--ignore-certificate-errors')
    chrome_options.add_argument('--ignore-ssl-errors')
    driver = webdriver.Chrome(options=chrome_options)
    driver.set_page_load_timeout(10)
    try:

        # Navigate to trip TripAdvisor, starting with hotels
        main_url = "https://www.tripadvisor.com/Hotels"
        # This should redirect to the correct local domain as needed (ex- .com.sg) AFAIK
        try:
            driver.get(main_url)
            nav = driver.find_element(By.ID,"global-nav-no-refresh-1").click()
        except NoSuchElementException:
            print("global-nav-no-refresh-1 not found")
            exit(1)

        nav.send_keys(query)
        nav.send_keys(Keys.RETURN)


        data = get_data(driver, "Hotels")
        h_df = pd.DataFrame(data, columns=list(column_titles_h))

        driver.find_element_by_id("global-nav-restaurants").click()
        data2 = get_data(driver, "Resturants")
        r_df = pd.DataFrame(data2, columns=list(column_titles_r))

        driver.find_element_by_id("global-nav-attractions").click()
        data3 = get_data(driver, "Attractions")
        a_df = pd.DataFrame(data3, columns=list(column_titles_a))

        driver.quit()
    except StopAsyncIteration as e:
        print("\nFatal Error, quiting...")
        driver.quit()
        print(e)
    return h_df, r_df, a_df


def get_data(driver, genre, max_pages=30):
    time.sleep(1)
    try:
        outersoup = BeautifulSoup(driver.page_source, 'html5lib')
        pagelinks = outersoup.find("div", class_="pageNumbers")
        total_pages = pagelinks.find_all("a")[-1]
        max_pages = int(total_pages.text)
        print("Found {} pages of {}".format(str(max_pages), genre))
    except Exception as e:
        print("Can't tell how many pages there are, searching", max_pages, ":", e)

    # Temporary #
    if testing:
        max_pages = test_length

    date_gen = datetime.today().replace(microsecond=0)
    data = []
    # try:
    pages_to_get = 10
    for page in range(pages_to_get):
        time.sleep(1)
        try:
            nb = driver.find_elements_by_xpath("//*[contains(text(), 'Next')]")[-1]
            next_page_loc = nb.get_attribute('href')
        except IndexError:
            next_page_loc = ""

        soup = BeautifulSoup(driver.page_source, 'html5lib')
        if genre == "Hotels":
            results = soup.find("div", class_="relWrap")
            partials = results.find_all("div", class_="listing_title")

        elif genre == "Resturants":
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
        print(f"Found {len(links)} links on page {page+1}/{pages_to_get} =>", end="")

        # driver.minimize_window()
        for i, link in enumerate(links):
            if (i == test_length) and testing:
                break
            time.sleep(1)
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
            print("Failed to go past page {}/{} (Could not click next)".format(page + 1, max_pages))
            print("href:", nb.get_attribute('href'))
            print("next_page_link:", next_page_loc, type(next_page_loc))
            break

    print("\nDone with", genre)

    return data


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
        star_count = soup.find("div", class_="starRatingWidget").text.split(".")[1]
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

    # Clean data
    if address is None:
        address = exaddress

    if phone:
        for c in phone:
            if c.isalpha():
                phone = None
                break

    # Put data into a list and return it
    row = [title, rating, review_count, phone, address, local, country, rec_duration, price, description, str(keywords)]
    return row


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

    # Implementation of a switch case to call the correct scraping function
    switch = {
        "Hotels": scrape_hotel,
        "Resturants": scrape_resturant,
        "Attractions": scrape_attraction
    }
    func = switch.get(genre, lambda input: print("Invalid genre"))
    return func(url, soup)


if __name__ == '__main__':
    main()
