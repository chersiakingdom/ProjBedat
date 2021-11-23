from bs4 import BeautifulSoup
import requests
import re
import os
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
import rpy2.robjects as robjects
from pymongo import MongoClient

from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
from tensorflow.keras.layers import Embedding, Dense, LSTM, Dropout
from tensorflow.keras.models import Sequential
from tensorflow.keras.models import load_model
from konlpy.tag import Okt
import re
import pandas as pd
import numpy as np
from tqdm import tqdm







client = MongoClient('localhost', 27017)  # 코딩할때 체킹용 디비
db = client.reply


# articleTitle
class naverNews:

    def __init__(self, url):
        self.url = url
        self.List = []  # 댓글 리스트
        self.des_statics = {}  # 기술 통계

    def get_title(self):
        header = {
            "User-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36",
            "referer": self.url,
        }
        resp = requests.get(self.url, headers=header)
        soup = BeautifulSoup(resp.text, "html.parser")
        title = soup.select_one('#articleTitle').text
        return title

    # 기술 통계를 가져오는 부분
    # 남성 비율, 여성 비율, 10대 비율, 20대 비율, 30대 비율, 40대 비율, 50대 비율, 60대 이상 비율

    def get_des(self):

        options = webdriver.ChromeOptions()
        options.add_argument('headless')
        options.add_argument('window-size=1920x1080')
        options.add_argument("disable-gpu")

        driver = webdriver.Chrome(ChromeDriverManager().install(), chrome_options=options)  # () 안에는 chromedriver.exe 위치
        driver.implicitly_wait(30)
        driver.get(self.url)

        # 뉴스창에서 댓글창으로 넘어가기
        btn_more = driver.find_element_by_css_selector('a.u_cbox_btn_view_comment')
        btn_more.click()

        per = driver.find_elements_by_css_selector('span.u_cbox_chart_per')
        if (len(per) == 0):
            return 0

        male = per[0].text  # 남자 성비
        female = per[1].text  # 여자 성비

        ten = per[2].text  # 10대
        twenty = per[3].text  # 20대
        thirty = per[4].text  # 30대
        forty = per[5].text  # 40대
        fifty = per[6].text  # 50대
        sixty_up = per[7].text  # 60대 이상

        self.des_statics['남성 비율'] = male
        self.des_statics['여성 비율'] = female
        self.des_statics['10대 비율'] = ten
        self.des_statics['20대 비율'] = twenty
        self.des_statics['30대 비율'] = thirty
        self.des_statics['40대 비율'] = forty
        self.des_statics['50대 비율'] = fifty
        self.des_statics['60대 이상'] = sixty_up

        driver.close()
        return self.des_statics

    # 여러 리스트들을 하나로 묶어 주는 함수입니다.
    def flatten(self, l):
        flatList = []
        for elem in l:
            # if an element of a list is a list
            # iterate over this list and add elements to flatList
            if type(elem) == list:
                for e in elem:
                    flatList.append(e)
            else:
                flatList.append(elem)
        return flatList

    def hot_reply(self,link):
        oid = link.split("oid=")[1].split("&")[0]  # 422
        aid = link.split("aid=")[1]  # 0000430957
        count = 0
        page = 1
        header = {
            "User-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36",
            "referer": link,
        }
        list = []
        while True:
            c_url = "https://apis.naver.com/commentBox/cbox/web_neo_list_jsonp.json?ticket=news&templateId=default_society&pool=cbox5&_callback=jQuery1707138182064460843_1523512042464&lang=ko&country=&objectId=news" + oid + "%2C" + aid + "&categoryId=&pageSize=20&indexSize=10&groupId=&listType=OBJECT&pageType=more&page=" + str(
                page) + "&refresh=false&sort=FAVORITE"
            # 파싱하는 단계입니다.
            r = requests.get(c_url, headers=header)

            cont = BeautifulSoup(r.content, "html.parser")

            total_comm = str(cont).split('comment":')[1].split(",")[0]

            match = re.findall('"contents":([^\*]*),"userIdNo"', str(cont))

            for i in range(len(match)):
                list.append(match[i])
                if i>100:
                    break

            if len(list) > 300 :
                break
        return list

    def clean_bot_reply(self):

        oid = self.url.split("oid=")[1].split("&")[0]  # 422
        aid = self.url.split("aid=")[1]  # 0000430957

        page = 1
        header = {
            "User-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36",
            "referer": self.url,
        }

        while True:
            c_url = "https://apis.naver.com/commentBox/cbox/web_neo_list_jsonp.json?ticket=news&templateId=default_society&pool=cbox5&_callback=jQuery1707138182064460843_1523512042464&lang=ko&country=&objectId=news" + oid + "%2C" + aid + "&categoryId=&pageSize=20&indexSize=10&groupId=&listType=OBJECT&pageType=more&page=" + str(
                page) + "&refresh=false&sort=FAVORITE"
            # 파싱하는 단계입니다.
            r = requests.get(c_url, headers=header)

            cont = BeautifulSoup(r.content, "html.parser")

            total_comm = str(cont).split('comment":')[1].split(",")[0]

            match = re.findall('"contents":([^\*]*),"userIdNo"', str(cont))
            replyCount = re.findall('"replyAllCount":([^\*]*),"replyPreviewNo"', str(cont))  # 답글 개수
            regTime = re.findall('"modTime":([^\*]*),"modTimeGmt"', str(cont))  # 시간
            sympathyCount = re.findall('"sympathyCount":([^\*]*),"antipathyCount"', str(cont))  # 공감수
            antipathyCount = re.findall('"antipathyCount":([^\*]*),"hideReplyButton"', str(cont))  # 비공감수
            hiddenByCleanbot = re.findall('"hiddenByCleanbot":([^\*]*),"score"', str(cont))  # 클린봇 감지 여부

            for i in range(len(match)):
                dic = {}
                dic['댓글내용'] = match[i]
                dic['대댓글 수'] = replyCount[i]
                dic['작성시간'] = regTime[i]
                dic['공감수'] = sympathyCount[i]
                dic['비공감수'] = antipathyCount[i]
                dic['논란수치'] = 0
                if (int(sympathyCount[i]) != 0 or int(antipathyCount[i] != 0)):
                    if (int(sympathyCount[i]) > int(antipathyCount[i])):
                        dic['논란수치'] = int(antipathyCount[i]) / int(sympathyCount[i])
                    elif (int(antipathyCount[i]) > int(sympathyCount[i])):
                        dic['논란수치'] = int(sympathyCount[i]) / int(antipathyCount[i])

                else:
                    dic['논란수치'] = 0

                dic['감지여부'] = hiddenByCleanbot[i]

                self.List.append(dic)

            # 한번에 댓글이 20개씩 보이기 때문에 한 페이지씩 몽땅 댓글을 긁어 옵니다.
            if int(total_comm) <= ((page) * 20):
                break
            else:
                page += 1

        allComments = self.flatten(self.List)

        return allComments

    def sentimental(self, list):
        print("sentimental 시작")
        list = pd.Series(list)
        self.sentiment_predict(list)
        # db.goodorbad.drop()
        #
        # for sentence in list:
        #     doc={}
        #
        #     result = self.sentiment_predict(sentence)
        #     if result == 1:
        #         doc = {'text':sentence,'color':'blue'}
        #     elif result == -1:
        #         doc = {'text':sentence,'color':'red'}
        #     else:
        #         doc = {'text': sentence, 'color': 'green'}
        #
        #     db.goodorbad.insert_one(doc)


    def clean_bot_off(self):

        options = webdriver.ChromeOptions()
        options.add_argument('headless')
        options.add_argument('window-size=1920x1080')
        options.add_argument("disable-gpu")

        driver = webdriver.Chrome(ChromeDriverManager().install(),chrome_options=options)  # () 안에는 chromedriver.exe 위치
        driver.implicitly_wait(30)
        driver.get(self.url)

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

        # 전체 댓글 목록 펼치기
        while True:
            try:
                btn_more_reply = driver.find_element_by_css_selector('a.u_cbox_btn_more')
                btn_more_reply.click()
                # time.sleep(1)
            except:
                break

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

                self.List.append(dic)

            except:
                comment = np.nan
                sympathy = np.nan
                anti = np.nan

            finally:

                driver.close()
                return self.List

    def topicModeling(self):
        rQuery = """ 
            pkg_fun <- function(pkg) {
  if (!require(pkg, character.only = TRUE)) {
    install.packages(pkg)
    library(pkg, character.only = TRUE)
  }
}

Sys.setlocale("LC_CTYPE", ".1251")

pkg_fun("readr")
pkg_fun("dplyr")
pkg_fun("stringr")
pkg_fun("textclean")
pkg_fun("mongolite")
pkg_fun("tidytext")
pkg_fun("tm")
pkg_fun("topicmodels")
pkg_fun("reshape2")


newdb <- mongo(collection = "nouns",
               db = "reply",
               url = "mongodb://localhost",
               verbose = TRUE)
test <- newdb$find() %>% filter(str_count(word)>1) %>% group_by(id) %>% distinct(word,.keep_all=T)%>%ungroup() %>% select(id,word)


count_word <- test %>% add_count(word) %>% add_count(n <= 200) %>% select(-n)

count_word_doc <- count_word %>% count(id,word,sort=T)

dtm_comment <- count_word_doc %>% cast_dtm(document=id,term = word, value=n)

LDA_models <- LDA(dtm_comment,k=5,method="Gibbs",control=list(seed= 1234))


term_topic <- tidy(LDA_models,matrix="beta")

top_term_topic <- term_topic %>% group_by(topic) %>% slice_max(beta,n=5,with_ties = F)

result <- as.data.frame(top_term_topic)

con <- mongo(collection = "topicModeling",
               db = "reply",
               url = "mongodb://localhost",
               verbose = TRUE)

if(con$count() > 0) con$drop()
con$insert(result)"""
        robjects.r(rQuery)

    def sentiment_predict(self,new_sentence):
        db.goodorbad.drop()
        okt = Okt()
        stopwords = ['의', '가', '이', '은', '들', '는', '좀', '잘', '걍', '과', '도', '를', '으로', '자', '에', '와', '한', '하다']
        max_len = 35

        dfset = pd.read_csv("sentimental_train_data.csv")
        npset = dfset.to_numpy()

        dataset = []
        for sentence in npset:
            nan_removed_sentence = [word for word in sentence if str(word) != 'nan']
            dataset.append(nan_removed_sentence)

        tokenizer = Tokenizer()
        tokenizer.fit_on_texts(dataset)

        vocab_size = 24749

        tokenizer = Tokenizer(vocab_size)
        tokenizer.fit_on_texts(dataset)

        ########################################

        loaded_model = load_model('best_model.h5')

        new_sentence = new_sentence.str.replace("[^ㄱ-ㅎㅏ-ㅣ가-힣 ]", "")

        predictset = []
        for sentence in tqdm(new_sentence):
            tokenized_sentence = okt.morphs(sentence, stem=True)  # 토큰화
            stopwords_removed_sentence = [word for word in tokenized_sentence if not word in stopwords]  # 불용어 제거
            predictset.append(stopwords_removed_sentence)
        ###

        predictset = np.array(predictset)

        encoded = tokenizer.texts_to_sequences(predictset)  # 정수 인코딩

        pad_new = pad_sequences(encoded, maxlen=max_len)  # 패딩
        score = loaded_model.predict(pad_new)  # 예측

        for i in range(len(new_sentence)):
            doc={}
            if (float(score[i])>0.55):

                doc = {'text':new_sentence[i],'color':'blue','rate':float(score[i]) * 100}
            elif (float(score[i]) < 0.45):
                rate = 1- (float(score[i]) * 100)
                doc = {'text': new_sentence[i], 'color': 'red','rate':rate}
            else:
                doc = {'text': new_sentence[i], 'color': 'green','rate':float(score[i]) * 100}

            db.goodorbad.insert_one(doc)