
'''
사용자 총 평점 -
전체 리뷰 갯수 -
각 리뷰의 작성 시간 -
전체 리뷰 내용 -
주제(카테고리)
주제에 맞는 댓글(밑줄친부분)

총 6 개 크롤링 해오기

+ "재구매", "각 주문별 옵션"  추가 크롤링
'''

from urllib.request import urlopen
from urllib.error import HTTPError
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.keys import Keys
import time

print("START")

wordset = []
optionset = []

class naverShopping:
    def __init__(self, link):
        self.link = link
        self.code = 0
    
    # 올바른 링크인지 확인
    def Linkcheck(self):
        if "https://smartstore.naver.com/" not in self.link:
            print("smartstore의 url만 입력이 가능합니다.")          
        else:
            try:
                res = urlopen(self.link)
                if res.status==200:
                    self.code = res.status
                    print("정상 URL 입니다.")
            except HTTPError as e:
                err = e.read()
                code = e.getcode()
                if code == 404:
                    print("요청한 페이지를 찾을 수 없습니다.")
                elif code == 403:
                    print("권한이 없어 접근할 수 없습니다.")
                elif code == 500:
                    print("웹 서버의 오류로 페이지가 제공되지 않습니다.")

        

    # 전체 리뷰 수, 총 평점
    def AllreviewScore(self):
        try:
            driver = webdriver.Chrome(ChromeDriverManager().install())
            driver.get(self.link)
            time.sleep(5)
            allre = driver.find_elements_by_css_selector("strong._2pgHN-ntx6")
            allrevie = allre[0].text
            score = allre[1].text.split('\n')
            print("전체 리뷰 수: ", allrevie)
            print("총 평점 : ", score[0])
        except:
            print("정보가 조회되지 않습니다.")
        driver.close()



    #전체 댓글 내용, 댓글 작성 시각, 재구매 유무
    def AllwordsTime(self):
        try:
            driver = webdriver.Chrome(ChromeDriverManager().install())
            driver.get(self.link)
            time.sleep(6)
            arti = driver.find_elements_by_css_selector('div.YEtwtZFLDz')
            time.sleep(3)
            date = driver.find_elements_by_css_selector('div._2FmJXrTVEX span._3QDEeS6NLn')
            time.sleep(3)
            options = driver.find_elements_by_css_selector("div._38yk3GGMZq span._3QDEeS6NLn")
            time.sleep(3)
            reviewnum = int(driver.find_element_by_css_selector("span.q9fRhG-eTG").text)
            time.sleep(3)

            pagenum = (reviewnum // 20) +1 
            print(pagenum)
            print(reviewnum)
            
            count = 1
            k=2

            #while(k-1 <= pagenum and count <= reviewnum): #최대(or전체) pagenum
            while(True):
                time.sleep(1)
                if count %20 ==1 and count != 1: 
                    k +=1 
                    print("next")
                    driver.find_element_by_xpath('//*[@id="REVIEW"]/div/div[3]/div/div[2]/div/div/a['+str(k)+']').click()
                    time.sleep(5)
                    arti = driver.find_elements_by_css_selector('div.YEtwtZFLDz')
                    time.sleep(3)
                    date = driver.find_elements_by_css_selector('div._2FmJXrTVEX span._3QDEeS6NLn')
                    time.sleep(3)
                    options = driver.find_elements_by_css_selector("div._38yk3GGMZq span._3QDEeS6NLn")
                    time.sleep(3)

                
                for ar, da, op in zip(arti, date, options):    
                    article = ar.text
                    datenum = da.text
                    option = op.text
                    print("[",k-1,"page," ,count,"]", datenum, "\n", option, "\n", article)
                    wordset.append(article)
                    optionset.append(option)
                    
                    count +=1
                    
                    if count >= reviewnum or count %20==1:
                        break
                    
                    
        
        except:
            print("다음 페이지가 존재하지 않습니다.")
            
        driver.close()
            


    # 전체 주제, 각 주제별 밑줄 댓글
    def AlltopicWords(self):
        try:
            driver = webdriver.Chrome(ChromeDriverManager().install())
            driver.get(self.link)
            time.sleep(7)
            alltopic = driver.find_elements_by_css_selector("#topic_div")
            time.sleep(4)
            
        
            num = 0
            count2 = 1
            k2 = 2
            
            alltop = alltopic[0].text.split("\n")
        
            for i in range(len(alltop)-1): #토픽 넘어갈때마다
                topic = alltop[i+1]
                num +=1
                count2 = 1
                k2 = 2
                print(num,":",topic)
                driver.find_element_by_xpath('//*[@id="topic_ul"]/li[' + str(i+2) + ']/a').send_keys(Keys.ENTER)
                time.sleep(3)
                topicwords = driver.find_elements_by_css_selector("em._2_otgorpaI")
                time.sleep(3)
                reviewnum = int(driver.find_element_by_css_selector("span.q9fRhG-eTG").text)
                time.sleep(2)
                pagenum = (reviewnum // 20) +1 #각 topic 별 리뷰의 총 갯수와 page 갯수
                #page = k2-1
                
                while(k2-1 <= pagenum and count2 <= reviewnum): #최대 몇페이지, 페이지 넘어갈때마다
                    if count2 % 20 ==1 and count2 !=1:
                        print("next")
                        driver.find_element_by_xpath('//*[@id="REVIEW"]/div/div[3]/div/div[2]/div/div/a['+str(k2)+']').click()
                        time.sleep(3)
                        topicwords = driver.find_elements_by_css_selector("em._2_otgorpaI")
                        time.sleep(3)

                    for word in topicwords:
                        word = word.text
                        print("[", topic ,"]", k2-1,"page," ,count2, "\n", word)
                        count2 +=1
                        
                        if count2 >= reviewnum or count2 %20==1:
                            k2 +=1
                            break
                        
            
        except:
            print("세부 주제가 존재하지 않습니다.")           
        
        driver.close()
            
        
    
    #시작함수    
    def Start(self):
        self.Linkcheck()
        if self.code ==200:
            #self.AllreviewScore()
            self.AllwordsTime()
            #self.AlltopicWords()
            
        else:
            print("다른 URL을 입력해주십시오.")
            
   
print("END 코드 무결성 확인")

# link = input("댓글을 가져올 URL을 입력하세요. (네이버 스마트스토어만 가능): ")

#Testlink1 = "https://smartstore.naver.com/vanera/products/401437851?NaPm=ct%3Dkrqwfg40%7Cci%3D294c74352bca580307f0ac437cee9ab359fdea69%7Ctr%3Dslsl%7Csn%3D174893%7Chk%3D559ee02d272234ac109281d87c10a94c2127492f"
# ㄴ 리뷰 n만개 링크 : 기본적인 크롤링 및 페이지 넘김, 토픽 넘김 등 검사 : OK
#Testlink2 = "https://smartstore.naver.com/bazig/products/100598948?NaPm=ct%3Dkrrdd5yg%7Cci%3D0b43f79af7bf98343fd58f850cdbb6cdd6a802ed%7Ctr%3Dslsl%7Csn%3D158724%7Chk%3D956cb2a10e428fd86b1bd7b9b5deef169e0aa71d"
# ㄴ 리뷰 n천개 링크 : 각 토픽별 크롤링 중 다음페이지가 없을시 다음 토픽으로 넘겨 크롤링하기 검사 : OK
Testlink3 = "https://smartstore.naver.com/the-people/products/344686106?NaPm=ct%3Dkrrfqnw0%7Cci%3Dd804bb5ae9f45cf154e492360c5eafd40f151773%7Ctr%3Dslsl%7Csn%3D156754%7Chk%3D12d0b0ffeec743ceaefed2dbcc641b0659d61b11"
# ㄴ 리뷰 n십개 링크 : 기본 페이지 넘김에서 다음페이지가 없을시 리뷰 갯수만큼의 정상 종료후 토픽 크롤링으로 넘어가는지 검사 : OK
#Testlink4 = "https://smartstore.naver.com/sneakeroff/products/5641028211?NaPm=ct%3Dkrrfpp60%7Cci%3Dcfa088c108f28a686816cf6a1b09096d7e1ac800%7Ctr%3Dslsl%7Csn%3D2909031%7Chk%3D6f71d8163787e790f8954ed497b4e2dd5fd150d2"
# ㄴ 리뷰 12개 링크 : 1page 미만일때 정상 종료 후 작동 검사
#Testlink5 = "https://smartstore.naver.com/jemsnewyork/products/5456806874?NaPm=ct%3Dksbn7j9s%7Cci%3D4add5e08580071a21a6639049a211c0b74b9d84c%7Ctr%3Dplac%7Csn%3D631904%7Chk%3Da80e4aef11dde3d9274663f2ef00e877316bafca"
# ㄴ 리뷰 n백개 링크 : 재구매 및 옵션 확인
exam1 = naverShopping(Testlink3)
exam1.Start()

'''
웹페이지 모듈 : 
총 리뷰 갯수, 사용자 총 평점, 재구매율, 토픽별 평점, 제품/옵션별 평점,
토픽분석, 제품/옵션별 구매순위, 댓글작성시간분포, 워드클라우드(주제X)

우선 만들 모듈:
재구매율, 토픽별 평점, 제품/옵션별 평점, 구매순위, 댓글작성시간그래프

'''
# 재구매 횟수 확인 
re_count = 0
for i in range(len(wordset)):
    re_num = wordset[i][0:3]
    re_num2 = wordset[i][5:8]
    if re_num == "재구매":
        re_count+=1
    if re_num2 == "재구매":
        re_count+=1
        
print("재구매 횟수: ", re_count)


