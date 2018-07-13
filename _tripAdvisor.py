from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
# import pandas as pd
from pandas import DataFrame
from bs4 import BeautifulSoup, SoupStrainer
import time
import csv
from selenium.common.exceptions import NoSuchElementException

# print('Pandas version:', pd.__version__)
df = DataFrame()
column_titles = ['Title', 'Rating', 'Review Count', 'Phone', 'Address']

count = 0
headers = {}
headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36'


def search(query):
    # Set up browser
    browser = webdriver.Chrome()
    # browser.minimize_window()
    # Navigate to trip tripadvisor
    main_url = 'https://www.tripadvisor.com/Attractions'
    site_url = "https://www.tripadvisor.com"
    # Should redirect to the correct local domain as needed (ex- .sg) AFAIK
    browser.get(main_url)

    # Search for the place provided and click on the "Things to Do" searchbar
    wait = WebDriverWait(browser, 1)
    wait.until(EC.presence_of_element_located((By.CLASS_NAME, "typeahead_input")))
    browser.find_element_by_class_name("typeahead_input").send_keys(query)
    time.sleep(1)
    browser.find_element_by_id("SUBMIT_THINGS_TO_DO").click()

    # Wait for page load
    wait = WebDriverWait(browser, 1)
    wait.until(EC.presence_of_element_located((By.CLASS_NAME, "listing_title")))

    # Visit all pages of results until "Next" button dissappears
    page_num = 1
    data = []
    try:
        while page_num < 10:
            print("Visiting results page: {}".format(page_num))
            page_num += 1
            # Grab the current url for later returning to this page
            current_page = browser.current_url
            # Get each attraction
            # resp = requests.get(current_page, headers=headers).text
            # listings = SoupStrainer('div', {'class': 'listing_title '})
            soup = BeautifulSoup(browser.page_source, "html5lib")
            attractions = soup.find_all("div", {"class": "listing_title "})
            links = [site_url + item.a['href'] for item in attractions if "Attraction_Review" in item.a['href']]

            data = []
            links_found = len(links)
            print("\t" + str(links_found), "Visiting..")  # , end="")
            for i in range(links_found):
                print(str(i) + "..", end="")
                # Visit each page
                browser.get(links[i])

                # soup = BeautifulSoup(requests.get(links[i], headers=headers).text, 'html5lib')
                # Scrape data
                try:
                    title = browser.find_element_by_id('HEADING').text.strip().split('\u200e')[0]
                except Exception as e:
                    print(e)
                    title = ""
                try:
                    reviews = browser.find_element_by_class_name('reviews_header_count').text.strip('()')
                except Exception as e:
                    print(e)
                    reviews = -1
                try:
                    rating = browser.find_element_by_class_name("overallRating").text
                except Exception as e:
                    print(e)
                    rating = -1.0
                try:
                    phone = browser.find_element_by_class_name("phone").text
                except Exception as e:
                    print(e)
                    phone = ""
                try:
                    address = browser.find_element_by_class_name("street-address").text
                except NoSuchElementException:
                    try:
                        address = browser.find_element_by_class_name("locality").text.rstrip(',')
                    except NoSuchElementException:
                        address = None
                # locality = browser.find_element_by_class_name("locality").text.rstrip(',')
                # country = browser.find_element_by_class_name("country-name").text

                newrow = [title, rating, reviews, phone, address]
                data.append(newrow)

            browser.get(current_page)
            try:
                block = soup.find("a", class_="next")
                next_page = site_url + block.get('href')
                browser.get(next_page)
            except NoSuchElementException as e:
                print("Failed to get next page.")
                break

        browser.quit()
    except Exception as e:
        print(e)

    return data


def store_to_csv(data, filename):
    data = list(data)
    with open(filename, 'w', newline='') as f:
        wr = csv.writer(f)
        wr.writerow(column_titles)
        for row in data:
            wr.writerow(row)


def main():
    destinations = ['Singapore']
    for place in destinations:
        filename = place + '_data(ByRow).csv'
        data = search(place)
        store_to_csv(data, filename)


if __name__ == '__main__':
    main()
