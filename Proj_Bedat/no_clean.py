from bs4 import BeautifulSoup
import requests
import re
import os
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager

import numpy as np


class no_cleanbot:
    def __init__(self, url):
        self.url = url

    def no_clean(self):
        List = []  # 댓글 리스트

        url = self.url

        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1280x1024')

        driver = webdriver.Chrome(ChromeDriverManager().install(),options=options)  # () 안에는 chromedriver.exe 위치
        driver.implicitly_wait(30)
        driver.get(url)

        # 뉴스창에서 댓글창으로 넘어가기
        btn_more = driver.find_element_by_css_selector('a.u_cbox_btn_view_comment')
        btn_more.click()

        btn_clean = driver.find_element_by_css_selector('a.u_cbox_cleanbot_setbutton')
        btn_clean.click()
        clean_bot = driver.find_element_by_css_selector('div.u_cbox_layer_cleanbot2_description').text

        if (clean_bot == '욕설 뿐 아니라 모욕적인 표현이 담긴 댓글까지 AI 기술로 감지하여 자동으로 숨겨줍니다.'):  # 활성화 상태면
            btn_check_clean = driver.find_element_by_id('cleanbot_dialog_checkbox_cbox_module')
            btn_check_clean.click()

        btn_done_clean = driver.find_element_by_css_selector('div.u_cbox_layer_cleanbot2_extra')
        btn_done_clean.click()

        # 댓글 펼치기
        while True:
            try:
                btn_more_reply = driver.find_element_by_css_selector('a.u_cbox_btn_more')
                btn_more_reply.click()
                # time.sleep(1)
            except:
                break

        # 기술 통계
        per = driver.find_elements_by_css_selector('span.u_cbox_chart_per')

        # 댓글 모으기
        html = driver.page_source
        soup = BeautifulSoup(html, 'lxml')
        divs = soup.find_all("div", {"class": "u_cbox_area"})

        for div in divs:

            time = div.find("span", {"class": "u_cbox_date"}).get_text(strip=True)

            try:
                dic = {}

                reply = int(div.find("span", {"class": "u_cbox_reply_cnt"}).get_text(strip=True))
                comment = div.find("span", {"class": "u_cbox_contents"}).get_text(strip=True)
                sympathy = int(div.find("em", {"class": "u_cbox_cnt_recomm"}).get_text(strip=True))
                anti = int(div.find("em", {"class": "u_cbox_cnt_unrecomm"}).get_text(strip=True))

                dic['댓글내용'] = comment
                dic['대댓글 수'] = reply
                dic['작성시간'] = time
                dic['공감수'] = sympathy
                dic['비공감수'] = anti

                if (sympathy != 0 or anti != 0):
                    if (sympathy > anti):
                        argu_rate = anti / sympathy
                    else:
                        argu_rate = sympathy / anti
                else:
                    argu_rate = 0
                dic['논란수치'] = argu_rate

                List.append(dic)

            except:
                comment = np.nan
                sympathy = np.nan
                anti = np.nan
        print("댓글 개수:",len(List))
        return List
