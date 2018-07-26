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
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
# from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# Global variables
column_titles = ['Title', 'Rating', 'Review Count', 'User Reviews',
                 'Phone Number', 'Address', 'Locality', 'Country',
                 'Keywords', 'Duration', 'Price', 'Type', 'Date Generated']
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
    except:
        pass
    try:
        os.mkdir("data")
    except WindowsError as e:
        pass

    for place in queries:
        filepath = os.path.join(os.path.abspath("data"), place + "_data.csv")
        df = search(place)
        try:
            df.to_csv(path_or_buf=filepath, index_label="Index")  # , columns=column_titles)
        except PermissionError:
            filepath = filepath[:-4] + "-2" + filepath[-4:]
            df.to_csv(path_or_buf=filepath, index_label="Index")
        print(strftime("\nFinished at %H:%M:%S\n", localtime()))
        print(df)


def search(query):
    print("\nBeginning search in", query)
    # Set up browser
    chrome_options = Options()
    chrome_options.add_argument('--log-level=3')
    driver = webdriver.Chrome(chrome_options=chrome_options)
    # os.environ['MOZ_HEADLESS'] = '1'
    # binary = FirefoxBinary('C:\\Program Files\\Mozilla Firefox\\firefox.exe', log_file=sys.stdout)
    # driver = webdriver.Firefox(firefox_binary=binary)
    wait = WebDriverWait(driver, 5)

    # Navigate to trip tripadvisor
    main_url = "https://www.tripadvisor.com/"
    # This should redirect to the correct local domain as needed (ex- .com.sg) AFAIK
    driver.get(main_url)

    # Search for the place provided and click on the "Things to Do" searchbar
    try:
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "mag_glass_parent")))
        searchicon = driver.find_element_by_class_name("mag_glass_parent")
        searchicon.click()
        wait.until(EC.presence_of_element_located((By.ID, "mainSearch")))
        searchbar = driver.find_element_by_id("mainSearch")
        wait.until(EC.visibility_of(searchbar))
        searchbar.click()
        searchbar.send_keys(query)
        searchbar.send_keys(Keys.RETURN)
        try:
            search_button = driver.find_element_by_id("SEARCH_BUTTON")
            if search_button.is_displayed():
                try:
                    search_button.click()
                except ElementClickInterceptedException:
                    time.sleep(1)
                    search_button.click()
            else:
                driver.find_element_by_class_name("result-title").click()
        except StaleElementReferenceException:
            pass

    except Exception as e:
        driver.quit()
        print("Problem:", e)
        raise

    # Wait for website to load search results
    try:
        wait.until(EC.presence_of_element_located((By.ID, "HEADING")))
    except TimeoutException:
        time.sleep(1)
        wait.until(EC.presence_of_element_located((By.ID, "HEADING")))

    # Visit all pages
    try:
        total_pages = driver.find_element_by_xpath("""/html/body/div[4]/div[3]/div[1]/div[2]/div/div/div/div/div[3]/div/div/a[7]""")
        max_pages = int(total_pages.text)
        print("Found", str(max_pages), "pages of results.", end="")
    except Exception:
        print("Can't tell how many pages there are", end="")
        max_pages = 10
    driver.minimize_window()
    data = []
    for page in range(max_pages + 1):
        results = driver.find_elements_by_class_name("result")
        # results.__delitem__(0)
        partials = [r.find_element_by_class_name("result_wrap").get_attribute("onclick").split(",")[6].strip().strip("'") for r in results]
        links = ["https://www.tripadvisor.com" + p for p in partials]
        print(f"\nFound {len(links)} links on page {page+1}/{max_pages} =>", end="")
        date_gen = datetime.today().replace(microsecond=0)
        for index, url in enumerate(links):
            try:
                newrow = scrape_article(url)
            except Exception as e:
                driver.quit()
                print(e)
                return pd.DataFrame(data, columns=list(column_titles))
            newrow.append(date_gen)
            data.append(newrow)

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

    driver.quit()
    final_df = pd.DataFrame(data, columns=list(column_titles))
    return final_df


def scrape_article(url, category):
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
    description = description
    row = [title, rating, review_count, user_reviews, phone, address, local, country, keywords, rec_duration, price]
    return row


def main():
    script()


if __name__ == '__main__':
    main()
