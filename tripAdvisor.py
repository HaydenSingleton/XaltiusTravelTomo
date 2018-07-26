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
from selenium.common.exceptions import (ElementClickInterceptedException,
                                        StaleElementReferenceException,
                                        TimeoutException)
# from selenium.webdriver.common.by import By
# from selenium.webdriver.common.keys import Keyss
from selenium.webdriver.chrome.options import Options
# from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
# from selenium.webdriver.support import expected_conditions as EC
# from selenium.webdriver.support.ui import WebDriverWait

# Global variables
column_titles = ['Title', 'Rating', 'Review Count', 'User Reviews',
                 'Phone Number', 'Address', 'Locality', 'Country',
                 'Keywords', 'Duration', 'Price', 'Date Generated']
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36'}
# driver_path = os.path.normpath("C:\\Users\\Hayden\\Anaconda3\\selenium\\webdriver")


def script():
    print(strftime("Starting at %H:%M:%S", localtime()))

    if len(sys.argv) < 2:
        input_list = ['singapore']
    else:
        input_list = sys.argv[1:]

    queries = [s.capitalize() for s in input_list]
    print("Searching: [" + ", ".join(queries), end="]")

    try:
        os.remove("geckodriver.log")
    except OSError:
        pass
    try:
        os.mkdir("data")
    except OSError as e:
        pass
    genres = ['Hotels', 'Resturants', 'Attractions']
    for place in queries:
        dfs = list(search(place))
        for i, genre in enumerate(genres):
            root_path = place + "_" + genre + "_data.csv"
            filepath = os.path.join(os.path.abspath("data"), root_path)
            dfs[i].to_csv(path_or_buf=filepath, index_label="Index")  # , columns=column_titles)
        print(strftime("\nFinished {} at %H:%M:%S\n".format(genre), localtime()))


def search(query):
    print("\nBeginning search in", query)
    # Set up browser
    chrome_options = Options()
    chrome_options.add_argument('--log-level=3')
    driver = webdriver.Chrome(chrome_options=chrome_options)
    # os.environ['MOZ_HEADLESS'] = '1'
    # binary = FirefoxBinary('C:\\Program Files\\Mozilla Firefox\\firefox.exe', log_file=sys.stdout)
    # driver = webdriver.Firefox(firefox_binary=binary)
    driver.set_page_load_timeout(10)

    # Three types of article we grab from trip advisor
    genres = ['Hotels', 'Resturants', 'Attractions']

    # Navigate to trip TripAdvisor, starting with hotels
    main_url = "https://www.tripadvisor.com/Hotels"
    # This should redirect to the correct local domain as needed (ex- .com.sg) AFAIK
    driver.get(main_url)
    driver.find_element_by_id("global-nav-hotels").click()
    driver.find_element_by_class_name("typeahead_input").send_keys(query)
    driver.find_element_by_class_name("submit_text").click()
    time.sleep(1)

    data = get_data(driver, genres[0])
    h_df = pd.DataFrame(data, columns=list(column_titles))

    driver.find_element_by_id("global-nav-restaurants").click()

    data2 = get_data(driver, genres[1])
    r_df = pd.DataFrame(data2, columns=list(column_titles))

    driver.find_element_by_id("global-nav-attractions").click()

    data3 = get_data(driver, genres[2])
    a_df = pd.DataFrame(data3, columns=list(column_titles))

    driver.quit()
    return h_df, r_df, a_df


def get_data(driver, genre, max_pages=10):

    try:
        total_pages = driver.find_element_by_xpath("""/html/body/div[4]/div[3]/div[1]/div[2]/div/div/div/div/div[3]/div/div/a[7]""")
        max_pages = int(total_pages.text)
        print("Found", str(max_pages), "pages of results.", end="")
    except Exception:
        print("Can't tell how many pages there are", end="")

    data = []
    for page in range(max_pages + 1):

        if genre != "Resturants":
            soup = BeautifulSoup(driver.page_source, 'html5lib')
            partials = soup.find_all("div", class_="listing_title")
            links = ["https://www.tripadvisor.com" + p.a['href'] for p in partials if "http" not in p.a['href']]
        if genre == "Resturants":
            soup = BeautifulSoup(driver.page_source, 'html5lib')
            partials = soup.find_all("div", class_="title")
            links = ["https://www.tripadvisor.com" + p.a['href'] for p in partials if "http" not in p.a['href']]
        print(f"\nFound {len(links)} links on page {page+1}/{max_pages} =>", end="")

        date_gen = datetime.today().replace(microsecond=0)
        driver.minimize_window()
        for link in links:
            newrow = scrape_article(link)
            newrow.append(date_gen)
            data.append(newrow)
        driver.minimize_window()
        try:
            next_page = driver.current_url[:-1] + str(30 * (page + 1))
            try:
                driver.get(next_page)
            except Exception as e:
                time.sleep(2)
                driver.get(next_page)
        except Exception as e:
            print("\nFailed to go past page {}/{}".format(page + 1, max_pages))
            print(e)
            break
    return data


def scrape_article(url):
    print(".", end="", flush=True)
    # Get BS opbject for the article
    # headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36'}
    soup = BeautifulSoup(requests.get(url, headers=headers).text, 'html5lib')

    # Scrape data, filling missing values with None
    try:
        title = soup.find('h1', id='HEADING').text
    except Exception:
        title = None
    try:
        review_count = soup.find('span', class_='reviews_header_count').text.strip('()')
    except Exception:
        review_count = None
    try:
        rating = soup.find("span", class_="overallRating").text
    except Exception:
        rating = None
    try:
        phone = soup.find("div", class_=['phone']).text
    except Exception:
        phone = None
    try:
        address = soup.find("span", class_="street-address").text.rstrip(',')
    except Exception:
        address = None
    try:
        exaddress = soup.find("span", class_="extended-address").text
    except Exception:
        exaddress = None
    try:
        local = soup.find("span", class_="locality").text.replace(',', '')
    except Exception:
        local = None
    try:
        country = soup.find("span", class_="country-name").text
    except Exception:
        country = None
    try:
        review_containers = soup.find_all("div", class_="review-container")
        user_reviews = {ur.find("div", class_="info_text").text: ur.find("p", class_="partial_entry").text for ur in review_containers}
    except Exception:
        user_reviews = None
    try:
        description = soup.find("div", class_="AttractionDetailAboutCard__section--3ZGme").text
    except Exception:
        description = None
    try:
        rec_duration = soup.find("div", class_="AboutSection__textAlignWrapper--3dWW_").text
    except Exception:
        rec_duration = None
    try:
        price = soup.find("span", class_="fromPrice").text.rstrip('*')
    except Exception:
        price = None
    try:
        keywords_container = soup.find("div", class_="ui_tagcloud_group").text.split("\n")  # Convert to a list
        kwc = [w for w in keywords_container if w is not ""][1:]  # Remove first tag "all reviews" and empty strings
        keywords = {w.split('"')[1]: w.split()[-2] for w in kwc}  # Seperate tag and count and put into dict
    except Exception:
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
    row = [title, rating, review_count, user_reviews, phone, address, local, country, keywords, rec_duration, price]
    return row


def main():
    script()


if __name__ == '__main__':
    main()
