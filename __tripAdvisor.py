import sys
import os
from datetime import datetime
import pandas as pd
# from pandas import DataFrame
import time
from time import localtime, strftime
from selenium import webdriver
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
# from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup

# Global variables
column_titles = ['Title', 'Rating', 'Review Count', 'User Reviews', 'Phone Number', 'Address', 'Locality', 'Country', 'Date Generated', 'Keywords', 'Duration', 'Price']
# headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36'}
driver_path = os.path.normpath("C:\\Users\\Hayden\\Anaconda3\\selenium\\webdriver")


def search(query):
    print("Beginning search in", query)
    data = []
    # Set up browser
    # chrome_options = Options()
    # chrome_options.add_argument('--log-level=3')
    # driver = webdriver.Chrome(chrome_options=chrome_options)

    # # os.environ['MOZ_HEADLESS'] = '1'
    binary = FirefoxBinary('C:\\Program Files\\Mozilla Firefox\\firefox.exe', log_file=sys.stdout)
    driver = webdriver.Firefox(firefox_binary=binary)

    wait = WebDriverWait(driver, 5)
    # Navigate to trip tripadvisor
    main_url = "https://www.tripadvisor.com/"  # Should redirect to the correct local domain as needed (ex- .com.sg) AFAIK
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
        search_button = driver.find_element_by_id("SEARCH_BUTTON")
        search_button.click()
    except TimeoutException as e:
        print("Website not responding")
        driver.quit()
        print(e)
        exit(1)

    # Wait for website to load search results
    try:
        wait.until(EC.presence_of_element_located((By.ID, "HEADING")))
    except TimeoutException:
        print("Failed to load page")
        exit(1)

    # Visit all pages
    page_num = 0
    try:
        total_pages = driver.find_element_by_xpath("""/html/body/div[4]/div[3]/div/div[2]/div/div/div/div[3]/div/div/a[7]""")
        print("found", str(total_pages.text), "pages of results.")
        pages_to_scrape = int(total_pages.text)
        pages_to_scrape //= 3
    except Exception:
        pages_to_scrape = 1
        print("found", str(pages_to_scrape), "pages of results.")
    # pages_to_scrape = 10

    date_gen = datetime.today().replace(microsecond=0)

    while page_num < pages_to_scrape:
        page_num += 1

        # Find all search results
        allresults = driver.find_element_by_class_name("all-results")
        results = allresults.find_elements_by_class_name("result")
        links = ["https://www.tripadvisor.com" + r.find_element_by_class_name("result_wrap").get_attribute("onclick").split(",")[6].strip().strip("'") for r in results]
        numlinks = len(links)
        print(f"\nFound {numlinks} links on page {page_num}/{pages_to_scrape}-")

        try:
            next_page = main_url + BeautifulSoup(driver.page_source, 'html5lib').find("a", class_="next").get('href')
        except AttributeError:
            next_page = None

        # numlinks //= 10 # For testing
        # print(f"\nSearching only {numlinks}...")

        for i in range(numlinks):
            print(str(i) + ".", end="", flush=True)
            # Visit each page
            driver.get(links[i])

            # Scrape data
            soup = BeautifulSoup(driver.page_source, 'html5lib')
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
                for c in phone:
                    if c.isalpha():
                        phone = None
                        break
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

            if address is None:
                address = exaddress

            description = description
            newrow = [title, rating, review_count, user_reviews, phone, address, local, country, date_gen, keywords, rec_duration, price]
            data.append(newrow)

        print()

        if next_page:
            driver.get(next_page)
        else:
            print("No more pages")
            break

    driver.quit()
    final_df = pd.DataFrame(data, columns=list(column_titles))
    return final_df


def main():
    print(strftime("Starting at %H:%M:%S", localtime()))
    if len(sys.argv) < 2:
        destinations = ['malaysia']
    else:
        destinations = sys.argv[1:]

    try:
        savefolder = "data"
        os.mkdir(savefolder)
    except Exception:
        pass

    print("Searching:", end="")
    [print(" " + p.capitalize(), end="") for p in destinations]
    print()

    start = time.perf_counter()
    for place in destinations:
        place = place.capitalize()
        # os.path.join(os.getcwd(), "data")
        filepath = os.path.join(os.path.abspath(savefolder), place + "_data.csv")
        df = search(place)
        try:
            df.to_csv(path_or_buf=filepath, index_label="Index", columns=column_titles)
        except PermissionError:
            for i in range(9):
                try:
                    filepath = filepath[:-4] + str(i) + filepath[-4:]
                    break
                except PermissionError:
                    pass
            else:
                print("File could not be saved")
        print(strftime("\nFinished at %H:%M:%S\n", localtime()))
        print(df.head())
    finish = time.perf_counter()
    disp_program_duration(finish, start)


def disp_program_duration(finish, start):
    execution_time = (finish - start)
    if execution_time >= 60:
        print("\n" + "Searching took {:.2f} minutes to complete".format(execution_time / 60))
    else:
        print("\n" + "Searching took {:.1f} seconds to complete".format(execution_time))


if __name__ == '__main__':
    main()
