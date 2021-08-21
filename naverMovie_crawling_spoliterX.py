import requests
from bs4 import BeautifulSoup as bs
import pandas as pd
from selenium import webdriver

url = input('url: ')
print('\n')
raw = requests.get(url)
soup1 = bs(raw.text, 'html.parser')

# 네티즌 평점, 기자/평론가 평점, 문장
dict_1 = {}

net_star = soup1.find('a', {'id': 'pointNetizenPersentBasic'}).text

report_stars = soup1.find('div', {'class':"spc_score_area"}).find_all('em')
report_star = report_stars[1].text+report_stars[2].text+report_stars[3].text+report_stars[4].text

sentence = soup1.find('strong',{'class':'grp_review'}).text

dict_1['네티즌 평점'] = net_star
dict_1['기자,평론가 평점'] = report_star
dict_1['문장'] = sentence

print(dict_1)

# 성별 관람추이

options = webdriver.ChromeOptions()
options.add_argument('--headless')
options.add_argument('--disable-gpu')
options.add_argument('--window-size=1280x1024')

driver = webdriver.Chrome('./chromedriver',options=options)
driver.get(url)

dict_2 = {}

try:
    path = driver.find_element_by_css_selector('#actualGenderGraph > svg > path:nth-child(3)')
    if path.get_attribute('fill') == '#86c8fc':
        percen_boy = driver.find_element_by_css_selector('#actualGenderGraph > svg > text:nth-child(4) > tspan').text
        percen_girl = driver.find_element_by_css_selector('#actualGenderGraph > svg > text:nth-child(6) > tspan').text
        dict_2['남자 관람비율'] = percen_boy
        dict_2['여자 관람비율'] = percen_girl
except:
    circle = driver.find_element_by_css_selector('#actualGenderGraph > svg > circle:nth-child(3)')
    if circle.get_attribute('fill') == '#86c8fc':
        percen_boy = driver.find_element_by_css_selector('#actualGenderGraph > svg > text > tspan').text
        dict_2['남자 관람비율'] = percen_boy
    elif circle.get_attribute('fill') == '#ff7e5a':
        percen_girl = driver.find_element_by_css_selector('#actualGenderGraph > svg > text > tspan').text
        dict_2['여자 관람비율'] = percen_girl
print(dict_2)

driver.close()

# 나이별 관람추이
dict_3 = {}

graphs = soup1.find('div',{'class':'bar_graph'}).find_all('div',{'class':'graph_box'})
for graph in graphs:
    age = graph.find('strong',{'class':'graph_legend'}).text
    percen_age = graph.find('strong',{'class':'graph_percent'}).text
    dict_3[age+' 관람비율'] = percen_age
print(dict_3)

# 성별 만족도
dict_4 = {}

boy_star = soup1.find('div',{'class':'grp_male'}).find('strong').text
dict_4['남자 만족도'] = boy_star
girl_star = soup1.find('div',{'class':'grp_female'}).find('strong').text
dict_4['여자 만족도'] = girl_star

print(dict_4)

#나이별 만족도
dict_5 = {}

grp_ages = soup1.find('div',{'class':'grp_age'}).find_all('div',{'class':'grp_box'})
for grp_age in grp_ages:
    age2 = grp_age.find('strong',{'class':'graph_legend'}).text
    age2_star = grp_age.find('strong',{'class':'graph_point'}).text
    dict_5[age2+' 만족도'] = age2_star
print(dict_5)

#감상포인트
dict_6 = {}

lis2 = soup1.find('div',{'class':'grp_sty4'}).find_all('li')
for li2 in lis2:
    point = li2.find('strong').text
    score = li2.find('span').text
    dict_6[point] = score
print(dict_6)

#각 댓글의 평점, 날짜, 댓글, 공감, 비공감, 논란지수
iframe_url = soup1.iframe['src']
final_url = "https://movie.naver.com"+iframe_url
url2 = final_url.replace('&type=after&isActualPointWriteExecute=false&isMileageSubscriptionAlready=false&isMileageSubscriptionReject=false','&type=after&onlyActualPointYn=N&onlySpoilerPointYn=Y&order=sympathyScore')
soup2 = bs(requests.get(url2).text, 'html.parser')
cnt = soup2.select('body > div > div > div.score_total > strong > em')[0].text.replace(',','')  # 전체 댓글 수

#데이터들을 저장할 딕셔너리 생성
dict_7 = dict()
count = 0

for page in range(1,int(cnt)//10+2 ): 
    url3 = url2+"&page="+str(page)
    raw3 = requests.get(url3)
    soup3 = bs(raw3.text,'html.parser')
    reple =  soup3.select('body > div > div > div.score_result > ul > li > div.score_reple > p')
    star = soup3.select('body > div > div > div.score_result > ul > li > div.star_score > em')
    like_and_dislike = soup3.select('body > div > div > div.score_result > ul > li > div.btn_area')
    date = soup3.select('body > div > div > div.score_result > ul > li > div.score_reple > dl > dt')

    for i in range(len(reple)):
        # 평점
        rev_star = star[i].text
        # 날짜
        rev_date = date[0].contents[3].text.strip()[:10]
        # 댓글
        if (reple[i].contents[3] == ' 스포일러 컨텐츠로 처리되는지 여부 '):
            rev = reple[i].contents[5].text.strip()   # 관람객 
        else:
            rev = reple[i].contents[3].text.strip()   # 관람객X
        if rev == "스포일러가 포함된 감상평입니다. 감상평 보기":   # 스포일러 댓글 출력X
            rev = ''
        if len(rev) >= 119 and (reple[i].contents[3] == ' 스포일러 컨텐츠로 처리되는지 여부 '):  # 댓글이 119자를 넘어갔을 때
            try:
                rev = reple[i].contents[5].contents[1].contents[1]['data-src']     # 관람객
            except:
                continue
        elif len(rev) >= 119:
            try:
                rev = reple[i].contents[3].contents[1].contents[1]['data-src']     # 관람객X
            except:
                continue
                
        # 공감/비공감/논란
        rev_like = like_and_dislike[i].contents[1].contents[5].text
        rev_dislike = like_and_dislike[i].contents[3].contents[5].text
        if (rev_like == '0') and (rev_dislike != '0'):
            contro = rev_dislike
        elif (rev_like != '0'):
            contro = round(int(rev_dislike)/int(rev_like),4)
        dict_7[count] = {'평점':rev_star,'날짜':rev_date,'댓글':rev.replace('&#39;' ,'\''),'공감':rev_like,'비공감':rev_dislike,'논란지수':contro}
        count +=1
        
pd.DataFrame(dict_7).T        