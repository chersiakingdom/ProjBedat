from flask import Flask, render_template, jsonify, request
import requests
from pymongo import MongoClient
import get_ranking
import shopping
import news
from operator import itemgetter
import word_cloud
import Analysis
import movie
import numpy as np
import os
from konlpy.tag import Okt
from collections import Counter
import no_clean

app = Flask(__name__)

# client = MongoClient('mongodb://best:scor68@localhost', 27017) #서버에 올릴때, 서버 디비
client = MongoClient('localhost', 27017)  # 코딩할때 체킹용 디비
db = client.reply

newsdoc = {}
new_list = []
time_give = {}
top10_list = []
good_percent = 0
good_list = []
bad_list = []
one = []
two = []
three = []
four = []
five = []
num = 0
title = ""
url = ""

rate = 0.0
repurchase = 0
option_rank = {}
keys=[]
values=[]
rank_key = []
rank_value=[]
topics={}
topic_score = []
models={}

moviedoc = {}
rating=[]
time=[]
reviews=[]
good=[]
bad=[]
controversy=[]
set_time=[]
count_time=[]
topic_time=[]
topic_reviews=[]
topic_good=[]
topic_bad=[]
topic=[]
count=[]
re_num=0

## HTML 화면 보여주기
@app.route('/')
def project_reply():
    return render_template('main.html')

# 뉴스 댓글 분석 결과 창
@app.route('/newsLoading')
def news_loading():
    return render_template('news_loading.html')

@app.route('/shoppingLoading')
def shopping_loading():
    return render_template('shopping_loading.html')

@app.route('/movieLoading')
def movie_loading():
    return render_template('movie_loading.html')

# 뉴스 댓글 분석 결과 창
@app.route('/news_result')
def result01():
    return render_template('news_result.html')


# 상품후기 분석 결과창
@app.route('/shopping_result')
def result02():
    return render_template('shopping_result.html')


# 영화 리뷰 분석 결과창
@app.route('/movie_result')
def result03():
    return render_template('movie_result.html')

@app.route('/news_des_all')
def result01_1():
    return render_template('news_des_seeall.html')

@app.route('/news_des_age')
def result01_2():
    return render_template('news_des_age.html')

@app.route('/news_des_word')
def result01_3():
    return render_template('news_des_word.html')

@app.route('/news_stat_all')
def result01_4():
    return render_template('news_stat_seeall.html')

@app.route('/news_stat_pos')
def result01_5():
    return render_template('news_stat_pos.html')

@app.route('/news_stat_topic')
def result01_6():
    return render_template('news_stat_topic.html')

@app.route('/shopping_word')
def result02_1():
    return render_template('shopping_word.html')

@app.route('/shopping_Topic')
def result02_2():
    return render_template('shopping_Topic.html')

@app.route('/shopping_Item')
def result02_3():
    return render_template('shopping_Item.html')

@app.route('/movieseeAll')
def result03_1():
    return render_template('movie_des_seeall.html')

@app.route('/movieAge')
def result03_2():
    return render_template('movie_des_age.html')

@app.route('/movieGender')
def result03_3():
    return render_template('movie_des_gender.html')

@app.route('/movieWord')
def result03_4():
    return render_template('movie_des_word.html')

@app.route('/movieStat')
def result03_5():
    return render_template('movie_stat.html')

@app.route('/api/reply', methods=['GET'])
def number_reply():
    number_news = list(db.number.find({}, {'_id': False}))
    return jsonify({'result_count': number_news})


@app.route('/api/issue', methods=['GET'])
def issue_getter():
    file = './static/assets/issuecloud.png'
    if os.path.isfile(file):
        os.remove(file)

    issue = get_ranking.get_ranking()
    issue_list = issue.result()
    print("이제 각 url 크롤링 시작")
    all = []
    new_crawl = news.naverNews(issue_list[0]['src'])
    for i in range(len(issue_list)):
        result = new_crawl.hot_reply(issue_list[i]['src'])
        all.extend(result)
    topics = Analysis.Analysis_Ad(all).noun_counter()

    return jsonify({'hot_issue': issue_list,'topic':topics})


@app.route('/api/check', methods=['POST'])
def get_url():
    # code = 0 --> "네이버 뉴스, 스마트 스토어, 영화에 대해서만 서비스 합니다."
    # code = 1 --> "정상 URL 입니다."
    # code = 2 --> "요청한 페이지를 찾을 수 없습니다."
    # code = 3 --> "권한이 없어 접근할 수 없습니다."
    # code = 4 --> "웹 서버의 오류로 페이지가 제공되지 않습니다."

    url_recieve = request.form['url_give']  # 입력한 url 받아오기
    cleanbot = request.form['news']
    spoiler = request.form['spo']

    # URL VALIDATION CHECK
    valid_url = shopping.naverShopping(url_recieve)
    code = valid_url.Linkcheck()
    classify = -1  # 분류 : 유효하지 않은 URL일 경우에는 -1

    # 서비스 가능한 URL일 경우에는 분류코드 (0: 뉴스, 1:스마트스토어, 2: 영화)
    if (code == 1):
        db.url.drop()
        doc = {'url': url_recieve, 'cleanbot': cleanbot, 'spoiler': spoiler}
        db.url.insert_one(doc)

        # 뉴스일 경우
        if ("https://news.naver.com/" in url_recieve):
            classify = 0

        # 스마트 스토어인 경우
        elif ("https://smartstore.naver.com/" in url_recieve):
            classify = 1

        # 영화인 경우
        else:
            classify = 2

    # validation code와 분류 코드를 넘겨준다.
    return jsonify({'valid': code, 'kind': classify, 'url': url_recieve})


@app.route('/api/statics', methods=['GET'])
def give_url():
    url = list(db.url.find({}, {'_id': False}))
    url_give = url[0]['url']
    desc = news.naverNews(url_give)

    global newsdoc
    newsdoc = desc.get_des()

    return jsonify(newsdoc)


@app.route('/api/contention', methods=['GET'])
def give_contention():
    file = './static/assets/wordcloud.png'
    if os.path.isfile(file):
        os.remove(file)

    url_give = list(db.url.find({}, {'_id': False}))

    global url
    url = url_give[0]['url']
    is_cleanbot = url_give[0]['cleanbot']  # clean bot이 작동하는지 아닌지
    reply = news.naverNews(url)
    # is_cleanbot 이 true일 경우 clean 봇이 작동하는 것.

    reply_list = []
    time = []

    if (is_cleanbot == "true"):
        # clean bot이 작동하고 있는 경우
        reply_list = reply.clean_bot_reply()
        # 작성시간 분포도는 년월일시 별로 분포도를 그리도록한다. (분까지 원할경우 real_date에 hms[1]을 넣어주면 된다.
        for l in reply_list:
            tmp = l['작성시간']
            tmp = tmp[1:-6]
            tmp1 = tmp.split('T')
            date = tmp1[0].split('-')
            hms = tmp1[1].split(':')
            real_date = date[0] + date[1] + date[2] + hms[0]
            time.append(real_date)
    else:
        reply_list = no_clean.no_cleanbot(url).no_clean()

        for l in reply_list:
            tmp = l['작성시간']
            tmp1 = tmp.split(' ')
            date = tmp1[0].split('.')
            hms = tmp1[1].split(':')
            real_date = date[0] + date[1] + date[2] + hms[0]
            time.append(real_date)

    global title
    title = reply.get_title()

    global new_list
    new_list = sorted(reply_list, key=itemgetter('논란수치'), reverse=True)[0:10]
    global num
    num = len(reply_list)

    num_two = list(db.number.find({}, {'_id': False}))
    num_article = num_two[0]['article']
    num_reply = num_two[0]['reply']
    db.number.update_one({'name': 'only'}, {'$set': {'article': num_article + 1, 'reply': num_reply + num}})

    global time_give

    time_give = {}
    for t in time:
        try:
            time_give[t] += 1
        except:
            time_give[t] = 1


    time_give = sorted(time_give.items())

    db.reply.drop()
    for l in reply_list:
        tmp = l['댓글내용'][1:-1]
        doc = {'comment': tmp}
        db.reply.insert_one(doc)

    temp = ""
    temp_list = []
    for l in reply_list:
        temp += l['댓글내용'][1:-1]
        temp += " "
        temp_list.append(l['댓글내용'][1:-1])

    # print(temp)
    cloud = word_cloud.wordcloud(temp)
    image = cloud.make_cloud_image("wordcloud")
    reply.sentimental(temp_list)

    # 토픽 모델링 진행
    print("topicmodeling 전처리 시작")
    Analysis.Analysis_Ad(temp_list).extractNoun()
    reply.topicModeling()
    get_10 = Analysis.Analysis_noun(temp)
    global top10_list
    top10_list = get_10.top10()

    good_bad = list(db.goodorbad.find({}, {'_id': False}))
    good = 0
    bad = 0
    mid = 0
    good_text = []
    bad_text = []
    for i in range(len(good_bad)):
        if good_bad[i]['color'] == 'blue':
            good += 1
            good_text.append(good_bad[i]['text'])
        elif good_bad[i]['color'] == 'green':
            mid += 1
        else:
            bad += 1
            bad_text.append(good_bad[i]['text'])

    global good_percent
    good_percent = (good / (good + bad)) * 100
    # print(good_text)
    # print(bad_text)
    good_top10 = Analysis.Analysis_Ad(good_text).top10()
    bad_top10 = Analysis.Analysis_Ad(bad_text).top10()

    global good_list
    good_list = []
    for i in range(len(good_top10)):
        temp = good_top10[i]['noun']
        good_list.append(temp)

    global bad_list
    bad_list = []
    for i in range(len(good_top10)):
        temp = bad_top10[i]['noun']
        bad_list.append(temp)

    topicModeling = list(db.topicModeling.find({}, {'_id': False}))

    global one
    one = []
    for i in range(0, 5):
        doc = {'word': topicModeling[i]['term'], 'beta': topicModeling[i]['beta']}
        one.append(doc)
    print(one)

    global two
    two = []
    for i in range(5, 10):
        doc = {'word': topicModeling[i]['term'], 'beta': topicModeling[i]['beta']}
        two.append(doc)

    global three
    three = []
    for i in range(10, 15):
        doc = {'word': topicModeling[i]['term'], 'beta': topicModeling[i]['beta']}
        three.append(doc)

    global four
    four = []
    for i in range(15, 20):
        doc = {'word': topicModeling[i]['term'], 'beta': topicModeling[i]['beta']}
        four.append(doc)

    global five
    five = []
    for i in range(20, 25):
        doc = {'word': topicModeling[i]['term'], 'beta': topicModeling[i]['beta']}
        five.append(doc)

    return jsonify({'contention_reply': new_list, 'number': num, 'title': title, 'url': url,
                    'time': time_give, 'top10': top10_list, 'percent': good_percent, 'good': good_list,
                    'bad': bad_list, 'firstTopic': one, 'secondTopic': two, 'thirdTopic': three,
                    'fourthTopic': four, 'fifthTopic': five})


@app.route('/api/static_shopping', methods=['GET'])
def basic_shopping():
    # url 가져옴
    url = list(db.url.find({}, {'_id': False}))
    url_give = url[0]['url']

    content = shopping.naverShopping(url_give)

    doc = content.AllreviewScore()
    global num
    num = doc['리뷰수']

    global rate
    rate = doc['평점']

    num_two = list(db.number.find({}, {'_id': False}))
    num_article = num_two[0]['article']
    num_reply = num_two[0]['reply']
    db.number.update_one({'name': 'only'}, {'$set': {'article': num_article + 1}})

    # 각 주제에 대한 토픽모델링 진행
    topic_doc = content.AlltopicWords()

    global models
    models = content.topicModeling(topic_doc)

    print("models: ", models)

    global topic_score
    topic_score = topic_doc['평점']


    topic_score = np.round(topic_score, 0).tolist()
    print("topic_score: ", topic_score)
    reviews = content.AllwordsTime()

    global repurchase
    repurchase = reviews['재구매횟수']
    global option_rank
    option_rank = reviews['옵션순위']
    global rank_key
    rank_key = []

    global rank_value
    rank_value = []
    for i in range(len(option_rank)):
        rank_key.append(option_rank[i][0])
        rank_value.append(option_rank[i][1])

    option_rate = reviews['옵션평점']

    global keys
    keys = list(option_rate.keys())

    global values
    values = list(option_rate.values())


    values = np.round(values, 0).tolist()
    print(values)
    date_list = reviews['작성시간']
    _date = []
    for date in date_list:
        new = ""
        temp = date.split('.')
        new = int(temp[0] + temp[1] + temp[2])
        _date.append(new)

    global time_give
    time_give = {}
    for t in _date:
        try:
            time_give[t] += 1
        except:
            time_give[t] = 1
    time_give = sorted(time_give.items())
    print("시간: ", time_give)
    cloud = word_cloud.shopping_cloud(reviews['review'][0:100])
    cloud.make_cloud_image("wordcloud")

    print("return every info.")
    global topics
    topics= topic_doc['topic']

    return jsonify(
        {'num_review': num, 'rate': rate, 'repurchase': repurchase, 'option_rank': option_rank, 'option_key': keys,
         'option_value': values, 'rank_key': rank_key, 'rank_value': rank_value,
         'topics': topics, 'topic_score': topic_score, 'time': time_give, 'modeling': models})


@app.route('/api/movie_statics', methods=['GET'])
def movie_stat():
    url = list(db.url.find({}, {'_id': False}))
    url_give = url[0]['url']
    desc = movie.naverMovie(url_give)

    global moviedoc
    moviedoc = desc.get_des()
    print(moviedoc)
    return jsonify(moviedoc)


@app.route('/api/movie_reviews', methods=['GET'])
def movie_rev():
    url = list(db.url.find({}, {'_id': False}))
    url_give = url[0]['url']
    desc = movie.naverMovie(url_give)
    doc = desc.no_spoiler_all()
    print(doc)

    global rating
    rating = []

    global time
    time = []

    global reviews
    reviews = []

    global good
    good = []

    global bad
    bad = []

    global controversy
    controversy = []

    for i in range(len(doc)):
        rating.append(doc[i]['평점'])
        time.append(doc[i]['날짜'])
        reviews.append(doc[i]['댓글'])
        good.append(doc[i]['공감'])
        bad.append(doc[i]['비공감'])
        controversy.append(doc[i]['논란지수'])

    # 토픽 모델링
    clean_reviews = []
    clean_reviews_str = ''
    for i in reviews:
        temp = i.replace('[^ㄱ-ㅎㅏ-ㅣ가-힣]', '')
        clean_reviews.append(temp)
        clean_reviews_str += ' ' + temp
    # print(clean_reviews_str)

    nlpy = Okt()
    sentences_tag = []
    for sentence in clean_reviews:
        morph = nlpy.pos(sentence, norm=True, stem=True)
        sentences_tag.append(morph)

    noun_adj_list = []
    for sentence in sentences_tag:
        for word, tag in sentence:
            if tag in ['Noun', 'Adjective'] and word not in desc.movie_stop_word() and len(word) >= 2:
                noun_adj_list.append(word)

    counts = Counter(noun_adj_list)
    top_10 = counts.most_common(10)
    global topic
    topic = [x[0] for x in top_10]

    global count
    count = [x[1] for x in top_10]

    # 토픽 관련 댓글
    topic_Index = []
    for num in range(10):
        j = 0
        index = [i for i in range(len(clean_reviews)) if topic[num] in clean_reviews[i]][j]
        while True:
            if index not in topic_Index:
                topic_Index.append(index)
                break
            index = [i for i in range(len(clean_reviews)) if topic[num] in clean_reviews[i]][j]
            j += 1
    global topic_time
    global topic_reviews
    global topic_good
    global topic_bad
    topic_time = []
    topic_reviews = []
    topic_good = []
    topic_bad = []
    for i in range(10):
        topic_time.append(time[topic_Index[i]])
        topic_reviews.append(reviews[topic_Index[i]])
        topic_good.append(good[topic_Index[i]])
        topic_bad.append(bad[topic_Index[i]])
    print('개수',len(topic_reviews))
    # 날짜
    global set_time
    global count_time
    set_time = sorted(list(set(time)))
    count_time = []
    for i in set_time:
        count_time.append(time.count(i))

    global re_num
    re_num = len(reviews)
    # 워드 클라우드
    cloud = word_cloud.wordcloud(clean_reviews_str)
    cloud.movie_cloud_image("wordcloud")

    num_two = list(db.number.find({}, {'_id': False}))
    num_article = num_two[0]['article']
    num_reply = num_two[0]['reply']
    db.number.update_one({'name': 'only'}, {'$set': {'article': num_article + 1, 'reply': num_reply + len(reviews)}})
    return jsonify({'평점': rating, '날짜': time, '댓글': reviews, '공감': good, '비공감': bad, '논란지수': controversy,
                    'set_time': set_time, 'count_time': count_time, 'topic': topic, 'count': count,
                    '댓글num': re_num, 'topic_time': topic_time, 'topic_reviews': topic_reviews,
                    'topic_good': topic_good, 'topic_bad': topic_bad})

@app.route('/api/newsdata1', methods=['GET'])
def news_data1():
    print(newsdoc)
    return jsonify(newsdoc)

@app.route('/api/newsdata2', methods=['GET'])
def news_data2():

    return jsonify({'contention_reply': new_list, 'number': num, 'title': title, 'url': url,
                    'time': time_give, 'top10': top10_list, 'percent': good_percent, 'good': good_list,
                    'bad': bad_list, 'firstTopic': one, 'secondTopic': two, 'thirdTopic': three,
                    'fourthTopic': four, 'fifthTopic': five})

@app.route('/api/shoppingdata', methods=['GET'])
def shopping_data():

    return jsonify(
        {'num_review': num, 'rate': rate, 'repurchase': repurchase, 'option_rank': option_rank, 'option_key': keys,
         'option_value': values, 'rank_key': rank_key, 'rank_value': rank_value,
         'topics': topics, 'topic_score': topic_score, 'time': time_give, 'modeling': models})

@app.route('/api/moviedata1', methods=['GET'])
def movie_data1():

    return jsonify(moviedoc)


@app.route('/api/moviedata2', methods=['GET'])
def movie_data2():
    return jsonify({'평점': rating, '날짜': time, '댓글': reviews, '공감': good, '비공감': bad, '논란지수': controversy,
                    'set_time': set_time, 'count_time': count_time, 'topic': topic, 'count': count,
                    '댓글num': re_num, 'topic_time': topic_time, 'topic_reviews': topic_reviews,
                    'topic_good': topic_good, 'topic_bad': topic_bad})

if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)
