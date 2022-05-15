from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium import webdriver
from bs4 import BeautifulSoup as bs, element
import chromedriver_binary
import time
import psycopg2
import os
from dotenv import load_dotenv


class Scraper:
    #  initializations
    driver = webdriver.Chrome()
    conn = None
    cur = None

    # constants
    PARK_NUM = 25

    # constructor and connect to db
    def __init__(self):
        try:
            # load the .env file
            load_dotenv()

            # connect to the PostgreSQL server
            self.conn = psycopg2.connect(
                host=os.environ['HOST'],
                database=os.environ['DATABASE'],
                user=os.environ['DB_USER'],
                password=os.environ['PASSWORD']
            )
            
            self.cur = self.conn.cursor()

        except (Exception, psycopg2.DatabaseError) as error:
            print(error)
            print('exiting the program with status -1')
            self.driver.close()
            exit(-1)


    # collect current open slots for each park
    def collect_opens(self):

        # click months
        months = self.driver.find_elements(By.XPATH, "//img[contains(@name, 'monthGif')]")
        for i in range(len(months)):
            months[i].click()

            # pick days
            days = self.driver.find_elements(By.XPATH, "//img[contains(@name, 'weektype')]")
            for i in range(len(days)):
                days[i].click()

            # pick sports
            self.navigate_click("//img[@alt='種目']")
            self.driver.find_element(By.LINK_TEXT, "テニス（人工芝）").click()
            time.sleep(2)
            
            for i in range(0, self.PARK_NUM, 2):
                self.driver.find_elements(By.XPATH, "//img[@alt='選択']")[i].click()
                
                if i + 1 <= self.PARK_NUM - 1:
                    self.driver.find_elements(By.XPATH, "//img[@alt='選択']")[i + 1].click()

                # click search
                self.navigate_click("//img[@alt='検索開始']")

                # =======this is where I get the data=======
                self.get_data()

                if i >= self.PARK_NUM - 1:
                    break
                else:
                    # click back
                    self.navigate_click("//img[@alt='もどる']")
                    
                    # reclick the previous ones to cancel
                    self.driver.find_elements(By.XPATH, "//img[@alt='選択']")[i].click()
                    self.driver.find_elements(By.XPATH, "//img[@alt='選択']")[i + 1].click()
                    time.sleep(1)


    def get_data(self):
        
        #  get year and dates
        year = int(self.driver.find_element(By.XPATH, "//tr[@height='74']").text[:-1])
        dates = self.driver.find_elements(By.XPATH, "//td[@bgcolor='#e0ffff']")
        row_count = int(len(dates))

        # accquire park names
        parks = self.driver.find_elements(By.XPATH, "//td[@valign='middle' and @nowrap]")
        for i in range(1, len(parks)):
            parks[i] = parks[i].text
        parks = parks[1:]

        # accquire time data
        opens = self.driver.find_elements(By.XPATH, "//tr[@height='39' and @align='center' and @bgcolor='#ffffff']")  # open slots data
        opens_parkA = opens[:row_count]
        opens_parkB = opens[row_count:]
        parkA_col_num = len(opens[0].text.split(' '))
        parkB_col_num = len(opens[row_count].text.split(' ')) if len(parks) == 2 else 0  # don't set the ParkB column number if only one park is being searched
        time_intervals = self.driver.find_elements(By.XPATH, "//td[@align='left' and @width='70px']")  # accquire time intervals for each park

        # traverse each row and start collecting open slots data for each park
        for idx, date in enumerate(dates):
            
            # park A
            for col in range(parkA_col_num):
                self.get_data_helper(idx, col, parks[0], opens_parkA, time_intervals, date, year)

            # park B if there is any on the page
            if len(parks) == 2:
                for col in range(parkB_col_num):
                    self.get_data_helper(idx, col, parks[1], opens_parkB, time_intervals, date, year)

            self.conn.commit()


    # Helper method for get_data to execute SQL command and insert data
    def get_data_helper(self, idx, col, park_name, opens, time_intervals, date, year):
        val = opens[idx].text.split(" ")[col]
        if val == '－':  # if the status is "-" means that time it is not available
            val = -1
        elif val == '×':  # if the status is "x" means that time it is full. 
            val = 0
        else:
            val = int(val)

        day = date.text[-2]
        if day == '月':
            day = 'Mon'
        elif day == '火':
            day = 'Tue'
        elif day == '水':
            day = 'Wed'
        elif day == '木':
            day = 'Thu'
        elif day == '金':
            day = 'Fri'
        elif day == '土':
            day = 'Sat'
        else:
            day = 'Sun'
        
        # upsert the data into DB
        self.cur.execute("""
            INSERT INTO availables (park_name, date_availability, start_time, end_time, week_of_day, opens, collected_at)
            VALUES ('{}', '{}', '{}', '{}', '{}', {}, NOW())
            ON CONFLICT (park_name, date_availability, start_time) 
            DO UPDATE SET 
                opens = {},
                collected_at = NOW();"""
            .format(
                park_name, 
                str(year) + "/" + date.text[:-3], 
                time_intervals[col].text[:5], 
                time_intervals[col].text[-5:],
                day, val, val
            )
        )


    def navigate_click(self, xpath):
        ele = self.driver.find_element(By.XPATH, xpath)
        self.driver.execute_script("arguments[0].click();", ele)
        time.sleep(1)
        return ele


    def show_cur_page(self):
        html = self.driver.page_source
        soup = bs(html)
        print(soup.prettify())


    def pretty_print(ele):
        soup = bs(ele)
        print(soup.prettify())


def main():

    scraper = Scraper()

    # open the link and navigate to filter page
    scraper.driver.get("https://yoyaku.sports.metro.tokyo.lg.jp/web/index.jsp")
    scraper.driver.switch_to.frame("pawae1002")
    scraper.navigate_click(xpath="//img[@alt='施設の空き状況']/..")
    scraper.navigate_click(xpath="//img[@alt='検索']/..")
    scraper.collect_opens()

    # closing connections to db and close winodws 
    scraper.cur.close()
    scraper.conn.close()
    scraper.driver.close()


if __name__ == "__main__":
    main()