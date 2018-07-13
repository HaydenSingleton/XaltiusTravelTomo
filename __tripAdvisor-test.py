import sys
import pandas as pd
import time
from selenium import webdriver
# from selenium.webdriver.chrome.options import Options
# from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
# from pandas import DataFrame
from bs4 import BeautifulSoup

# Global variables
column_titles = ['Title', 'Rating', 'Review Count', 'Phone Number', 'Address', 'Locality', 'Country']  # , 'Opening Hours']
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36'}


def search(query):
    # Set up browser
    # chrome_options = webdriver.ChromeOptions()
    # chrome_options.add_argument("--enable-fast-unload")
    # browser = webdriver.Chrome(chrome_options=chrome_options, port=443)
    browser = webdriver.Chrome()
    # Navigate to trip tripadvisor
    main_url = 'https://www.tripadvisor.com/Attractions'
    site_url = "https://www.tripadvisor.com"
    # Should redirect to the correct local domain as needed (ex- .sg) AFAIK
    browser.get(main_url)

    # Search for the place provided and click on the "Things to Do" searchbar
    wait = WebDriverWait(browser, 1)
    wait.until(EC.presence_of_element_located((By.CLASS_NAME, "typeahead_input")))
    searchbar = browser.find_element_by_class_name("typeahead_input")
    searchbar.send_keys(query)
    # searchbar.send_keys(Keys.RETURN)
    browser.find_element_by_id("SUBMIT_THINGS_TO_DO").click()

    # Wait for page load
    try:
        wait = WebDriverWait(browser, 1)
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "listing_title")))
    except TimeoutException:
        time.sleep(1)

    # Visit all pages of results until "Next" button dissappears
    page_num = 0
    pages_to_scrape = 4
    data = []

    while page_num < pages_to_scrape:
        page_num += 1

        # print("Visiting results page: {}".format(page_num))
        # Grab the current url for later returning to this page
        # current_page = browser.current_url

        # Get each attraction
        soup = BeautifulSoup(browser.page_source, "html5lib")
        attractions = soup.find_all("div", {"class": "listing_title "})
        links = [site_url + item.a['href'] for item in attractions if "Attraction_Review" in item.a['href']]
        numlinks = len(links)
        print(f"\nFound {numlinks} links on page {page_num} of {pages_to_scrape}..", end="")

        try:
            next_page = site_url + soup.find("a", class_="next").get('href')
        except AttributeError:
            next_page = None

        for i in range(numlinks):

            print(str(i) + ".", end="")
            # Visit each page
            browser.get(links[i])

            # Scrape data
            soup = BeautifulSoup(browser.page_source, 'html5lib')
            try:
                title = soup.find('h1', id='HEADING').text  # .split('\u200e')[0]
            except Exception:
                title = None
            try:
                reviews = soup.find('span', class_='reviews_header_count').text.strip('()')
            except Exception:
                reviews = None
            try:
                rating = soup.find("span", class_="overallRating").text
            except Exception:
                rating = None
            try:
                phone = soup.find("div", class_=['detail_section', 'phone']).text
            except Exception:
                phone = None
            try:
                address = soup.find("span", class_="street-address").text
            except Exception:
                try:
                    address = soup.find("span", class_="extended-address").text
                except Exception:
                    address = None
            try:
                local = soup.find("span", class_="locality").text
            except Exception:
                local = None
            try:
                country = soup.find("span", class_="country-name").text
            except Exception:
                country = None

            # try:
            #     hours = None  # TODO
            # except Exception as e:
            #     print("Hours failed- ", end="")
            #     print(e)
            #     hours = None

            if "Add" in phone:
                phone = None

            newrow = [title, rating, reviews, phone, address, local, country]  # , hours]
            data.append(newrow)

        if next_page:
            browser.get(next_page)
        else:
            print("No more pages")
            break

    browser.quit()
    final_df = pd.DataFrame(data, columns=list(column_titles))
    return final_df


def main():
    if len(sys.argv) < 2:
        destinations = ['cambodia', 'japan']
    else:
        destinations = sys.argv[1:]
    for place in destinations:
        place = place.capitalize()
        filename = place + '_data.csv'
        print("Beginning search in", place)
        df = search(place)
        print(df.head())
        df.to_csv(path_or_buf=filename, index_label="Index", columns=column_titles)


if __name__ == '__main__':
    main()
