from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium import webdriver
from bs4 import BeautifulSoup as bs, element
import pandas as pd
import time


#  initializations
ser = Service("./chromedriver")
op = webdriver.ChromeOptions()
driver = webdriver.Chrome(service=ser, options=op)
df = pd.DataFrame(columns=['Park', 'Availability_Date', 'Availability_Time', 'Availability_Day', 'Opens', 'Data_Collected_at'])


# constants
PARK_NUM = 25


def collect_opens():

    # click months
    months = driver.find_elements(By.XPATH, "//img[contains(@name, 'monthGif')]")
    for i in range(len(months)):
        months[i].click()

        # pick days
        days = driver.find_elements(By.XPATH, "//img[contains(@name, 'weektype')]")
        for i in range(len(days)):
            days[i].click()

        # pick sports
        navigate_click("//img[@alt='種目']")
        driver.find_element(By.LINK_TEXT, "テニス（人工芝）").click()
        time.sleep(2)
        
        for i in range(0, PARK_NUM, 2):
            driver.find_elements(By.XPATH, "//img[@alt='選択']")[i].click()
            
            if i + 1 <= PARK_NUM - 1:
                driver.find_elements(By.XPATH, "//img[@alt='選択']")[i + 1].click()

            # click search
            navigate_click("//img[@alt='検索開始']")

            # =======this is where I get the data=======
            if i + 1 < PARK_NUM - 1:    #这个逻辑不是很漂亮，因为这样要多做一个函数
                get_data1()
            else:
                get_data2()

            if i >= PARK_NUM - 1:
                break
            else:
                # click back
                navigate_click("//img[@alt='もどる']")
                
                # reclick the previous ones to cancel
                driver.find_elements(By.XPATH, "//img[@alt='選択']")[i].click()
                driver.find_elements(By.XPATH, "//img[@alt='選択']")[i + 1].click()
                time.sleep(1)
            


def get_data1():
    element = driver.find_element_by_css_selector('td:nth-child(1) center > table table td:nth-child(1)')  # 我这里的n想取一共有多少行，可能会有点麻烦，不知道有没有更好的写法可以一下子获得有多少行
    td_content_date = element.find_elements_by_tag_name("td") 
    lst = []
    for td in td_content_date:
        lst.append(td.text)
    n = len(lst)-1  #n在这里能得到最大行数


    lst_temp = []  # 暂时存一下.之后应该是直接储存到DataFrame

    for i in range(0,n):
        element_date = driver.find_element_by_css_selector(' td:nth-child(1) center > table table td:nth-child(1) tr:nth-child('+str(2+i)+')')  # Column date
        element_parkA = driver.find_element_by_css_selector(' td:nth-child(1) center > table table td:nth-child(2) tr:nth-child('+str(3+i)+')')  # Column park A
        element_parkB = driver.find_element_by_css_selector(' td:nth-child(1) center > table table td:nth-child(3) tr:nth-child('+str(3+i)+')')  # Column park B
    
    # 提取表格内容td
        td_content_date = element_date.find_elements_by_tag_name("td") 
        td_content_parkA = element_parkA.find_elements_by_tag_name("td")
        td_content_parkB = element_parkB.find_elements_by_tag_name("td")

        for td in td_content_date:
            lst_temp.append(td.text)
        for td in td_content_parkA:
            lst_temp.append(td.text)
        for td in td_content_parkB:
            lst_temp.append(td.text)
    print(lst_temp) # 输出表格内容

def get_data2():
    element = driver.find_element_by_css_selector('td:nth-child(1) center > table table td:nth-child(1)')  # 我这里的n想取一共有多少行，可能会有点麻烦，不知道有没有更好的写法可以一下子获得有多少行
    td_content_date = element.find_elements_by_tag_name("td") 
    lst = []
    for td in td_content_date:
        lst.append(td.text)
    n = len(lst)-1  #n在这里能得到最大行数


    lst_temp = []  # 存储为list,之后再改

    for i in range(0,n):
        element_date = driver.find_element_by_css_selector(' td:nth-child(1) center > table table td:nth-child(1) tr:nth-child('+str(2+i)+')')  # Column date
        element_parkA = driver.find_element_by_css_selector(' td:nth-child(1) center > table table td:nth-child(2) tr:nth-child('+str(3+i)+')')  # Column park A
    
    # 提取表格内容td
        td_content_date = element_date.find_elements_by_tag_name("td") 
        td_content_parkA = element_parkA.find_elements_by_tag_name("td")

        for td in td_content_date:
            lst_temp.append(td.text)
        for td in td_content_parkA:
            lst_temp.append(td.text)
    print(lst_temp) # 输出表格内容

def navigate_click(xpath):
    ele = driver.find_element(By.XPATH, xpath)
    driver.execute_script("arguments[0].click();", ele)
    time.sleep(1)
    return ele


def show_cur_page():
    html = driver.page_source
    soup = bs(html)
    print(soup.prettify())


def pretty_print(ele):
    soup = bs(ele)
    print(soup.prettify())


def main():

    # open the link and navigate to filter page
    driver.get("https://yoyaku.sports.metro.tokyo.lg.jp/web/index.jsp")
    driver.switch_to.frame("pawae1002")

    navigate_click(xpath="//img[@alt='施設の空き状況']/..")
    navigate_click(xpath="//img[@alt='検索']/..")

    collect_opens()

    driver.close()


if __name__ == "__main__":
    main()