from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import time
import random


def return_driver(url: str) -> webdriver.Chrome:
    """
    Initializes a Chrome WebDriver and navigates to the specified URL.

    Args:
    url (str): The URL to navigate to.

    Returns:
    webdriver.Chrome: An instance of the Chrome WebDriver.
    """
    driver = webdriver.Chrome()
    driver.get(url)
    return driver


def handle_search(driver: webdriver.Chrome, search_key: str):
    """
    Performs a search on Google Maps using the specified search key.

    Args:
    driver (webdriver.Chrome): The WebDriver instance to interact with.
    search_key (str): The search query to input into the search box.
    """
    # Find the search box element by its id
    search_box = driver.find_element(By.ID, "searchboxinput")

    # Input the search query and submit the form
    search_box.send_keys(search_key)
    search_box.send_keys(Keys.RETURN)


def return_random_number(lower_limit: int = 2, upper_limit: int = 5) -> int:
    """
    Returns a random integer between the specified lower and upper limits.

    Args:
    lower_limit (int, optional): The lower limit of the random number range. Default is 2.
    upper_limit (int, optional): The upper limit of the random number range. Default is 5.

    Returns:
    int: A random integer between lower_limit and upper_limit.
    """
    return random.randint(lower_limit, upper_limit)


def scroll(scroll_driver: webdriver.Chrome):
    """
    Scrolls the page down using the PAGE_DOWN key.

    Args:
    scroll_driver (webdriver.Chrome): The WebDriver instance to interact with.
    """
    scroll_driver.send_keys(Keys.PAGE_DOWN)


def return_links(driver: webdriver.Chrome) -> list:
    """
    Scrolls through the search results on Google Maps and collects the links.

    Args:
    driver (webdriver.Chrome): The WebDriver instance to interact with.

    Returns:
    list: A list of unique links to the search results.
    """
    scroll_div = driver.find_element(By.XPATH, """//*[@id="QA0Szd"]/div/div/div[1]/div[2]/div/div[1]/div/div/div[1]/div[1]""")
    keep_scrolling = True
    links = []

    max_scroll = 1
    count = 0
    try:
        while keep_scrolling:
            scroll(scroll_div)
            time.sleep(return_random_number())

            try:
                driver.find_element(By.CLASS_NAME, "HlvSq")
                keep_scrolling = False

            except Exception as exp:
                print(exp)
                print('---------------------------------')
                keep_scrolling = True

            links = driver.find_elements(By.CLASS_NAME, "hfpxzc")
            print(links)
            if count > max_scroll:
                keep_scrolling = False

            count += 1
    except Exception as exp:
        print(exp)

    return list(set([link.get_attribute("href") for link in links if link.get_attribute("href") is not None]))


def scrape_data(driver: webdriver.Chrome, links: list, search_key: str):
    """
    Scrapes data from the provided list of links and writes it to a text file.

    Args:
    driver (webdriver.Chrome): The WebDriver instance to interact with.
    links (list): A list of URLs to scrape data from.
    search_key (str): The search key used to name the output file.
    """
    for link in links:
        driver.get(link)
        class_ = driver.find_elements(By.CLASS_NAME, "CsEnBe")
        with open('_'.join(search_key.split(' ')) + '.txt', 'a', encoding="utf-8") as write_file:
            for classs in class_:
                arie_label = classs.get_attribute("aria-label")
                write_file.write(arie_label)
                write_file.write('\n')
            write_file.write('-' * 100)

        time.sleep(return_random_number())


def main(url: str, search_key: str):
    """
    Main function to execute the web scraping process.

    Args:
    url (str): The URL to navigate to (Google Maps).
    search_key (str): The search query to input into Google Maps.
    """
    driver = return_driver(url)

    handle_search(driver, search_key)

    time.sleep(return_random_number())

    links = return_links(driver)

    scrape_data(driver, links, search_key)


if __name__ == '__main__':
    url = 'https://www.google.com/maps'
    search_key = 'School near me'
    main(url, search_key)
