import requests
from bs4 import BeautifulSoup as bs
import pandas as pd
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
import time
from konlpy.tag import Okt
from collections import Counter

from wordcloud import WordCloud
import matplotlib.pyplot as plt
from PIL import Image
import numpy as np
import Analysis

class naverMovie:

    def __init__(self,url):
        self.url = url

    def get_des(self):

        dict={}
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1280x1024')

        driver = webdriver.Chrome(ChromeDriverManager().install(), options=options)
        driver.get(self.url)
        time.sleep(1)
        # 주요정보 페이지에서 평점 페이지로 이동
        if "https://movie.naver.com/movie/bi/mi/basic" in self.url:
            driver.find_element_by_xpath('//*[@id="movieEndTabMenu"]/li[5]/a').click()

        raw = requests.get(self.url)
        soup1 = bs(raw.text, 'html.parser')

        net_star = soup1.find('a', {'id': 'pointNetizenPersentBasic'}).text
        sentence = soup1.find('strong', {'class': 'grp_review'}).text

        dict['네티즌평점'] = net_star
        dict['문장'] = sentence

        try:
            path = driver.find_element_by_css_selector('#actualGenderGraph > svg > path:nth-child(3)')
            if path.get_attribute('fill') == '#86c8fc':
                percen_boy = driver.find_element_by_css_selector(
                    '#actualGenderGraph > svg > text:nth-child(4) > tspan').text
                percen_girl = driver.find_element_by_css_selector(
                    '#actualGenderGraph > svg > text:nth-child(6) > tspan').text
                dict['남자 관람비율'] = percen_boy
                dict['여자 관람비율'] = percen_girl

        except:
            circle = driver.find_element_by_css_selector('#actualGenderGraph > svg > circle:nth-child(3)')
            if circle.get_attribute('fill') == '#86c8fc':
                percen_boy = driver.find_element_by_css_selector('#actualGenderGraph > svg > text > tspan').text
                dict['남자 관람비율'] = percen_boy
                dict['여자 관람비율'] = '0%'
            elif circle.get_attribute('fill') == '#ff7e5a':
                percen_girl = driver.find_element_by_css_selector('#actualGenderGraph > svg > text > tspan').text
                dict['여자 관람비율'] = percen_girl
                dict['남자 관람비율'] = '0%'

        driver.close()

        graphs = soup1.find('div', {'class': 'bar_graph'}).find_all('div', {'class': 'graph_box'})
        for graph in graphs:
            age = graph.find('strong', {'class': 'graph_legend'}).text
            percen_age = graph.find('strong', {'class': 'graph_percent'}).text
            dict[age + ' 관람비율'] = percen_age

        # 성별 만족도
        boy_star = soup1.find('div', {'class': 'grp_male'}).find('strong').text
        dict['남자 만족도'] = boy_star
        girl_star = soup1.find('div', {'class': 'grp_female'}).find('strong').text
        dict['여자 만족도'] = girl_star

        #나이별 만족도
        grp_ages = soup1.find('div', {'class': 'grp_age'}).find_all('div', {'class': 'grp_box'})
        for grp_age in grp_ages:
            age2 = grp_age.find('strong', {'class': 'graph_legend'}).text
            age2_star = grp_age.find('strong', {'class': 'graph_point'}).text
            dict[age2 + ' 만족도'] = age2_star

        # 감상포인트
        lis2 = soup1.find('div', {'class': 'grp_sty4'}).find_all('li')
        for li2 in lis2:
            point = li2.find('strong').text
            score = li2.find('span').text
            dict[point] = score
        return dict

    def no_spoiler_all(self):

        raw = requests.get(self.url)
        soup1 = bs(raw.text, 'html.parser')

        # 각 댓글의 평점, 날짜, 댓글, 공감, 비공감, 논란지수
        iframe_url = soup1.iframe['src']
        final_url = "https://movie.naver.com" + iframe_url
        url2 = final_url.replace(
            '&type=after&isActualPointWriteExecute=false&isMileageSubscriptionAlready=false&isMileageSubscriptionReject=false',
            '&type=after&onlyActualPointYn=N&onlySpoilerPointYn=N&order=sympathyScore')
        soup2 = bs(requests.get(url2).text, 'html.parser')
        cnt = soup2.select('body > div > div > div.score_total > strong > em')[0].text.replace(',', '')

        dict_7 = dict()
        count1 = 0


        for page in range(1, int(cnt) // 10 + 2):
            url3 = url2 + "&page=" + str(page)
            raw3 = requests.get(url3)
            soup3 = bs(raw3.text, 'html.parser')
            reple = soup3.select('body > div > div > div.score_result > ul > li > div.score_reple > p')
            star = soup3.select('body > div > div > div.score_result > ul > li > div.star_score > em')
            like_and_dislike = soup3.select('body > div > div > div.score_result > ul > li > div.btn_area')
            date = soup3.select('body > div > div > div.score_result > ul > li > div.score_reple > dl > dt')

            for i in range(len(reple)):
                if (reple[i].contents[3] == ' 스포일러 컨텐츠로 처리되는지 여부 '):  # 관람객
                    if (reple[i].contents[5].text.strip() == '스포일러가 포함된 감상평입니다. 감상평 보기'):
                        continue
                    else:
                        # 평점
                        rev_star = star[i].text
                        # 날짜
                        rev_date = date[0].contents[3].text.strip()[:10]
                        # 댓글
                        rev = reple[i].contents[5].text.strip()
                        # 댓글이 119자 이상일 때
                        if len(rev) >= 119:
                            try:
                                rev = reple[i].contents[5].contents[1].contents[1]['data-src']
                            except:
                                continue
                        # 좋아요
                        rev_like = like_and_dislike[i].contents[1].contents[5].text
                        # 싫어요
                        rev_dislike = like_and_dislike[i].contents[3].contents[5].text
                        # 논란지수
                        if (rev_like == '0') and (rev_dislike != '0'):
                            contro = int(rev_dislike)
                        elif rev_like != '0':
                            contro = round(int(rev_dislike) / int(rev_like), 4)

                else:  # 관람객X
                    if (reple[i].contents[3].text.strip() == '스포일러가 포함된 감상평입니다. 감상평 보기'):
                        continue
                    else:
                        # 평점
                        rev_star = star[i].text
                        # 날짜
                        rev_date = date[0].contents[3].text.strip()[:10]
                        # 댓글
                        rev = reple[i].contents[3].text.strip()
                        # 댓글이 119자 이상일 때
                        if len(rev) >= 119:
                            try:
                                rev = reple[i].contents[3].contents[1].contents[1]['data-src']
                            except:
                                continue
                        # 좋아요
                        rev_like = like_and_dislike[i].contents[1].contents[5].text
                        # 싫어요
                        rev_dislike = like_and_dislike[i].contents[3].contents[5].text
                        # 논란지수
                        if (rev_like == '0') and (rev_dislike != '0'):
                            contro = int(rev_dislike)
                        elif rev_like != '0':
                            contro = round(int(rev_dislike) / int(rev_like), 4)

                dict_7[count1] = {'평점': rev_star, '날짜': rev_date,
                                  '댓글': rev.replace('&#39;', '\'').replace('&#34;', '\"'), '공감': rev_like,
                                  '비공감': rev_dislike, '논란지수': contro}  # 전체 댓글 추출
                count1 += 1


        pd.DataFrame(dict_7).T

        return dict_7

    def no_spoiler_good(self):
        raw = requests.get(self.url)
        soup1 = bs(raw.text, 'html.parser')

        # 각 댓글의 평점, 날짜, 댓글, 공감, 비공감, 논란지수
        iframe_url = soup1.iframe['src']
        final_url = "https://movie.naver.com" + iframe_url
        url2 = final_url.replace(
            '&type=after&isActualPointWriteExecute=false&isMileageSubscriptionAlready=false&isMileageSubscriptionReject=false',
            '&type=after&onlyActualPointYn=N&onlySpoilerPointYn=N&order=sympathyScore')
        soup2 = bs(requests.get(url2).text, 'html.parser')
        cnt = soup2.select('body > div > div > div.score_total > strong > em')[0].text.replace(',', '')

        dict_7 = dict()
        count1 = 0

        dict_8 = dict()
        count2 = 0

        for page in range(1, int(cnt) // 10 + 2):
            url3 = url2 + "&page=" + str(page)
            raw3 = requests.get(url3)
            soup3 = bs(raw3.text, 'html.parser')
            reple = soup3.select('body > div > div > div.score_result > ul > li > div.score_reple > p')
            star = soup3.select('body > div > div > div.score_result > ul > li > div.star_score > em')
            like_and_dislike = soup3.select('body > div > div > div.score_result > ul > li > div.btn_area')
            date = soup3.select('body > div > div > div.score_result > ul > li > div.score_reple > dl > dt')

            for i in range(len(reple)):
                if (reple[i].contents[3] == ' 스포일러 컨텐츠로 처리되는지 여부 '):  # 관람객
                    if (reple[i].contents[5].text.strip() == '스포일러가 포함된 감상평입니다. 감상평 보기'):
                        continue
                    else:
                        # 평점
                        rev_star = star[i].text
                        # 날짜
                        rev_date = date[0].contents[3].text.strip()[:10]
                        # 댓글
                        rev = reple[i].contents[5].text.strip()
                        # 댓글이 119자 이상일 때
                        if len(rev) >= 119:
                            try:
                                rev = reple[i].contents[5].contents[1].contents[1]['data-src']
                            except:
                                continue
                        # 좋아요
                        rev_like = like_and_dislike[i].contents[1].contents[5].text
                        # 싫어요
                        rev_dislike = like_and_dislike[i].contents[3].contents[5].text
                        # 논란지수
                        if (rev_like == '0') and (rev_dislike != '0'):
                            contro = int(rev_dislike)
                        elif rev_like != '0':
                            contro = round(int(rev_dislike) / int(rev_like), 4)

                else:  # 관람객X
                    if (reple[i].contents[3].text.strip() == '스포일러가 포함된 감상평입니다. 감상평 보기'):
                        continue
                    else:
                        # 평점
                        rev_star = star[i].text
                        # 날짜
                        rev_date = date[0].contents[3].text.strip()[:10]
                        # 댓글
                        rev = reple[i].contents[3].text.strip()
                        # 댓글이 119자 이상일 때
                        if len(rev) >= 119:
                            try:
                                rev = reple[i].contents[3].contents[1].contents[1]['data-src']
                            except:
                                continue
                        # 좋아요
                        rev_like = like_and_dislike[i].contents[1].contents[5].text
                        # 싫어요
                        rev_dislike = like_and_dislike[i].contents[3].contents[5].text
                        # 논란지수
                        if (rev_like == '0') and (rev_dislike != '0'):
                            contro = int(rev_dislike)
                        elif rev_like != '0':
                            contro = round(int(rev_dislike) / int(rev_like), 4)

                dict_7[count1] = {'평점': rev_star, '날짜': rev_date,
                                  '댓글': rev.replace('&#39;', '\'').replace('&#34;', '\"'), '공감': rev_like,
                                  '비공감': rev_dislike, '논란지수': contro}  # 전체 댓글 추출

                if int(rev_star) >= 8:  # 긍정 댓글만 추출
                    dict_8[count2] = {'평점': rev_star, '날짜': rev_date,
                                      '댓글': rev.replace('&#39;', '\'').replace('&#34;', '\"'), '공감': rev_like,
                                      '비공감': rev_dislike, '논란지수': contro}
                    count2 += 1

        pd.DataFrame(dict_8).T
        return dict_8

    def no_spoiler_bad(self):

        raw = requests.get(self.url)
        soup1 = bs(raw.text, 'html.parser')

        # 각 댓글의 평점, 날짜, 댓글, 공감, 비공감, 논란지수
        iframe_url = soup1.iframe['src']
        final_url = "https://movie.naver.com" + iframe_url
        url2 = final_url.replace(
            '&type=after&isActualPointWriteExecute=false&isMileageSubscriptionAlready=false&isMileageSubscriptionReject=false',
            '&type=after&onlyActualPointYn=N&onlySpoilerPointYn=N&order=sympathyScore')
        soup2 = bs(requests.get(url2).text, 'html.parser')
        cnt = soup2.select('body > div > div > div.score_total > strong > em')[0].text.replace(',', '')

        dict_7 = dict()
        count1 = 0

        dict_8 = dict()
        count2 = 0

        for page in range(1, int(cnt) // 10 + 2):
            url3 = url2 + "&page=" + str(page)
            raw3 = requests.get(url3)
            soup3 = bs(raw3.text, 'html.parser')
            reple = soup3.select('body > div > div > div.score_result > ul > li > div.score_reple > p')
            star = soup3.select('body > div > div > div.score_result > ul > li > div.star_score > em')
            like_and_dislike = soup3.select('body > div > div > div.score_result > ul > li > div.btn_area')
            date = soup3.select('body > div > div > div.score_result > ul > li > div.score_reple > dl > dt')

            for i in range(len(reple)):
                if (reple[i].contents[3] == ' 스포일러 컨텐츠로 처리되는지 여부 '):  # 관람객
                    if (reple[i].contents[5].text.strip() == '스포일러가 포함된 감상평입니다. 감상평 보기'):
                        continue
                    else:
                        # 평점
                        rev_star = star[i].text
                        # 날짜
                        rev_date = date[0].contents[3].text.strip()[:10]
                        # 댓글
                        rev = reple[i].contents[5].text.strip()
                        # 댓글이 119자 이상일 때
                        if len(rev) >= 119:
                            try:
                                rev = reple[i].contents[5].contents[1].contents[1]['data-src']
                            except:
                                continue
                        # 좋아요
                        rev_like = like_and_dislike[i].contents[1].contents[5].text
                        # 싫어요
                        rev_dislike = like_and_dislike[i].contents[3].contents[5].text
                        # 논란지수
                        if (rev_like == '0') and (rev_dislike != '0'):
                            contro = int(rev_dislike)
                        elif rev_like != '0':
                            contro = round(int(rev_dislike) / int(rev_like), 4)

                else:  # 관람객X
                    if (reple[i].contents[3].text.strip() == '스포일러가 포함된 감상평입니다. 감상평 보기'):
                        continue
                    else:
                        # 평점
                        rev_star = star[i].text
                        # 날짜
                        rev_date = date[0].contents[3].text.strip()[:10]
                        # 댓글
                        rev = reple[i].contents[3].text.strip()
                        # 댓글이 119자 이상일 때
                        if len(rev) >= 119:
                            try:
                                rev = reple[i].contents[3].contents[1].contents[1]['data-src']
                            except:
                                continue
                        # 좋아요
                        rev_like = like_and_dislike[i].contents[1].contents[5].text
                        # 싫어요
                        rev_dislike = like_and_dislike[i].contents[3].contents[5].text
                        # 논란지수
                        if (rev_like == '0') and (rev_dislike != '0'):
                            contro = int(rev_dislike)
                        elif rev_like != '0':
                            contro = round(int(rev_dislike) / int(rev_like), 4)

                dict_7[count1] = {'평점': rev_star, '날짜': rev_date,
                                  '댓글': rev.replace('&#39;', '\'').replace('&#34;', '\"'), '공감': rev_like,
                                  '비공감': rev_dislike, '논란지수': contro}  # 전체 댓글 추출

                if int(rev_star) <= 4:  # 긍정 댓글만 추출
                    dict_8[count2] = {'평점': rev_star, '날짜': rev_date,
                                      '댓글': rev.replace('&#39;', '\'').replace('&#34;', '\"'), '공감': rev_like,
                                      '비공감': rev_dislike, '논란지수': contro}
                    count2 += 1

            pd.DataFrame(dict_8).T
            return dict_8

    def movie_stop_word(self):
        stop_word = ['절대','그냥','너희','이번','다음','지금','누가','퍼트','현재',"니들","풀어주","절대","너희들","안하","단지","어차피","걔네","하다","하게","들이","만큼","이것",
        "아", "휴", "아이구", "아이쿠", "아이고", "어", "나", "우리", "저희", "따라", "의해", "을", "를", "에", "의",
        "가", "으로", "로", "에게", "뿐이다" ,"의거하여", "근거하여", "입각하여", "기준으로", "예하면", "예를", "들면", "들자면" ,"저",
        "소인" ,"소생", "저희", "지말고", "하지마", "하지마라", "다른", "물론", "또한", "그리고", "비길수" ,"없다",
        "해서는", "안된다", "뿐만", "아니라", "만이", "아니다", "만은", "아니다", "막론하고", "관계없이",
        "그치지", "않다", "그러나", "그런데", "하지만", "든간에", "논하지", "않다", "따지지", "설사" ,"비록" ,"더라도",
        "아니면" ,"만", "못하다", "하는", "편이", "낫다", "불문하고", "향하여", "향해서" ,"향하다", "쪽으로", "틈타", "이용하여",
        "타다", "오르다", "제외하고", "외에", "밖에", "하여야", "비로소", "한다면", "몰라도", "외에도", "이곳", "여기",
        "부터", "기점으로", "따라서", "할", "생각이다", "하려고하다", "이리하여", "그리하여", "그렇게", "함으로써", "하지만",
        "일때", "할때", "앞에서", "중에서", "보는데서", "으로써", "로써", "까지", "해야한다", "일것이다", "반드시",
        "할줄알다" ,"할수있다", "할수있어", "임에", "틀림없다", "한다면", "등", "등등", "제", "겨우", "단지", "다만", "할뿐",
        "딩동", "댕그", "대해서", "대하여", "대하면", "훨씬", "얼마나", "얼마만큼", "얼마큼", "남짓", "여", "얼마간",
        "약간", "다소", "좀", "조금", "다수", "몇", "얼마", "지만" ,"하물며", "또한", "그러나", "그렇지만", "하지만", "이외에도", "대해",
        "말하자면", "뿐이다", "다음에", "반대로" ,"말하자면" ,"이와", "바꾸어서" ,"말하면", "한다면", "만약" ,"그렇지않으면",
        "까악", "삐걱거리다", "보드득", "비걱거리다", "꽈당", "응당", "해야한다", "에", "가서", "각각", "여러분",
        "각종", "각자", "제각기", "하도록하다", "그러므로", "그래서", "고로" ,"한", "까닭에", "하기", "때문에", "거니와",
        "이지만", "대하여", "관하여", "관한", "과연", "실로", "아니나다를가", "생각한대로", "진짜로", "한적이있다",
        "하곤하였다", "하하", "허허", "아하", "거바", "왜", "어째서", "무엇때문에", "어찌", "하겠는가", "무슨", "어디",
        "어느곳", "더군다나", "하물며", "더욱이는", "어느때", "언제", "이봐", "어이", "여보시오", "흐흐","헉헉",
        "헐떡헐떡", "영차", "여차", "어기여차", "끙끙" ,"아야","콸콸", "졸졸", "좍좍", "뚝뚝", "주룩주룩", "솨",
        "우르르", "그래도", "또", "그리고", "바꾸어말하면", "바꾸어말하자면", "혹은", "혹시", "답다", "및",
        "그에", "따르는", "때가", "되어", "즉", "지든지", "설령", "가령", "하더라도", "할지라도", "일지라도",
        "지든지", "몇", "거의", "하마터면", "인젠", "이젠", "된바에야", "된이상", "만큼", "어찌됏든",
        "그위에", "게다가", "점에서", "보아", "비추어", "보아", "고려하면", "하게될것이다", "일것이다", "비교적", "좀" ,"보다더", "비하면", "시키다", "하게하다",
        "할만하다", "의해서", "연이서", "이어서", "잇따라", "뒤따라", "뒤이어", "결국", "의지하여", "기대여", "통하여", "자마자", "더욱더", "불구하고", "얼마든지", "마음대로"
        ,"당연","당신","얼마","살았","하시","고통스럽","^ㅋ","ㅋㅋ","ㅋㅋㅋ","^ㅎ","ㅎㅎ","내년","어쩌","가즈","드러븐","정도","수가","이전",
        '영화', '근데', '하나', '그리고', '정도', '이것', '너무', '진짜', '본거', '그거', '스럽다', '높다', '아주', '정말', '모두', '진짜', '완전','있다','아니다','어떻다','이렇다','그렇다','같다','없다', '이다',
        '아마', '서로', '내내', '짧다', '가장', '모든']
        return stop_word
