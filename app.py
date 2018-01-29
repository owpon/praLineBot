# -*- coding: utf-8 -*-
import requests  # 用來網路連線的
from flask import Flask, request, abort
from bs4 import BeautifulSoup
import time
import json
from dbModel import *
import re

# import psycopg2
# import urllib.parse as urlparse
# import os

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
# 這是單一掛載
# from linebot.models import (
#     MessageEvent, TextMessage, TextSendMessage,
# )
# 把line bot的模組impor進去
from linebot.models import *

app = Flask(__name__)

token = 'LineSecretToken的那串值'
line_bot_api = LineBotApi(token)
handler = WebhookHandler('Channel secret的那短短的値')


@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    print("這是niceBody" + body)
    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'


# 先準備要抓取的頁面的網址
def get_page_number(content):
    start_index = content.find('index')
    end_index = content.find('.html')
    page_number = content[start_index + 5: end_index]
    return int(page_number) + 1


# 準備爬該頁面所有資料
def craw_page(res, push_rate):
    soup_ = BeautifulSoup(res.text, 'html.parser')
    article_seq = []
    for r_ent in soup_.find_all(class_="r-ent"):
        try:
            link = r_ent.find('a')['href']
            if link:
                title = r_ent.find(class_="title").text.strip()
                rate = r_ent.find(class_="nrec").text
                url = 'https://www.ptt.cc' + link
                if rate:
                    rate = 100 if rate.startswith('爆') else rate
                    rate = -1 * int(rate[1]) if rate.startswith('X') else rate
                else:
                    rate = 0

                if int(rate) >= push_rate:
                    article_seq.append({
                        'title': title,
                        'url': url,
                        'rate': rate,
                    })
        except Exception as e:
            print('本文已被刪除', e)
    return article_seq


# 取得電影目錄
def movie():
    # 取得目標網址
    target_url = 'http://www.atmovies.com.tw/movie/next/0/'
    print("start parsing movie:")
    # 取得session
    rs = requests.session()
    # 取得網頁
    res = rs.get(target_url, verify=False)
    # 先設定為utf-8
    res.encoding = 'utf-8'
    # 準備爬資料
    soup = BeautifulSoup(res.text, 'html.parser')
    # 先開好要回傳的字串
    content = ""
    # 取得ul下面的filmNextListAll的所有a連結
    for index, data in enumerate(soup.select('ul.filmNextListAll a')):
        if index == 20:
            return content
        # 查出電影名稱然後把tab換成換行
        title = data.text.replace('\t', '').replace('\r', '')
        link = 'http://www.atmovies.com.tw' + data['href']
        content += '{}\n{}\n'.format(title, link)
    return content


# 抓beauty版資料
def ptt_beauty():
    target_url = 'https://www.ptt.cc/bbs/Beauty/index.html'
    rs = requests.session()
    res = rs.get(target_url, verify=False)
    soup = BeautifulSoup(res.text, 'html.parser')
    # 先找上頁的頁籤
    all_page_url = soup.select('.btn.wide')[1]['href']
    # 開始的頁面
    start_page = get_page_number(all_page_url)
    # crawler count
    page_term = 2
    # 推文數量
    push_rate = 10
    index_list = []
    article_list = []
    for page in range(start_page, start_page - page_term, -1):
        # 把取到的數字塞進去當做搜尋的網址
        page_url = 'https://www.ptt.cc/bbs/Beauty/index{}.html'.format(page)
        index_list.append(page_url)

    while index_list:
        index = index_list.pop(0)
        res = rs.get(index, verify=False)
        if res.status_code != 200:
            index_list.append(index)
            time.sleep(1)
        else:
            article_list = craw_page(res, push_rate)
            time.sleep(1)
    content = ''
    for article in article_list:
        data = '[{} push] {}\n{}\n\n'.format(article.get('rate', None), article.get('title', None),
                                             article.get('url', None))
        content += data
    return content


# 抓joke版資料
def joke():
    target_url = 'https://www.ptt.cc/bbs/joke/index.html'
    rs = requests.session()
    res = rs.get(target_url, verify=False)
    soup = BeautifulSoup(res.text, 'html.parser')
    # 先找上頁的頁籤
    all_page_url = soup.select('.btn.wide')[1]['href']
    # 開始的頁面
    start_page = get_page_number(all_page_url)
    # crawler count
    page_term = 2
    # 推文數量
    push_rate = 10
    index_list = []
    article_list = []
    for page in range(start_page, start_page - page_term, -1):
        # 把取到的數字塞進去當做搜尋的網址
        page_url = 'https://www.ptt.cc/bbs/joke/index{}.html'.format(page)
        index_list.append(page_url)

    while index_list:
        index = index_list.pop(0)
        res = rs.get(index, verify=False)
        if res.status_code != 200:
            index_list.append(index)
            time.sleep(1)
        else:
            article_list = craw_page(res, push_rate)
            time.sleep(1)
    content = ''
    for article in article_list:
        data = '[{} push] {}\n{}\n\n'.format(article.get('rate', None), article.get('title', None),
                                             article.get('url', None))
        content += data
    return content


# 學習講話
def learnWord(event):
    # 學習只出現一次，冒號":"只出現一次，第一個冒號後面不出現冒號跟分號，第二個冒號後面也是這樣
    pattern = re.compile(
        r'學習{1}:{1}[^;:][\u4e00-\u9fa5\u3105-\u3129\w\sA-Za-z0-9*+/?!%$#@`_.,。，、"-]{0,}:{1}[^;:][\u4e00-\u9fa5\u3105-\u3129\w\sA-Za-z0-9*+/?!%$#@`_.,。，、"-]{0,}')
    # 輸入的字串
    inputText = event.message.text
    # 把全形的冒號換成半形的
    input = inputText.replace('：', ':')
    # 符合格式的話
    matchFormat = pattern.match(input)
    print('pattern格式', matchFormat)
    # 去切割字串
    if matchFormat:
        key = matchFormat.group().split(':')[1]
        value = matchFormat.group().split(':')[2]
        if len(key) <= 255 and len(value) < 255:
            # 取得資料庫的搜尋出來的第一筆
            data_Words = Add_New_Word.query.filter_by(input_word=key).first()
            print(type(data_Words))
            if data_Words is not None:
                aa = Add_New_Word.query.filter_by(input_word=key).update({'input_word': key, 'output_word': value})
                db.session.commit()
                print(aa)
                return '好喔好喔，把舊的詞update了'
            else:
                add_word = Add_New_Word(
                    input_word=key,
                    output_word=value
                )
                db.session.add(add_word)
                db.session.commit()
                print('學習結束')
                return '好喔好喔，又學到新的詞了'
        else:
            return '你的太長了，阿嘶~'
    else:
        return '機器人圈中只有我是真性情，每個人都想搞我!'


def closeBot(event, type):
    botConfig.query.filter_by(GroupId=type).update({'Status': 'False'})
    db.session.commit()
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text='好喔好喔，關閉聊天'))


def openBot(event, type):
    botConfig.query.filter_by(GroupId=type).update({'Status': 'True'})
    db.session.commit()
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text='好喔好喔，開始聊天'))


# 設定回話
def reply(event):
    content = event.message.text
    data_Words = Add_New_Word.query.filter_by(input_word=content).first()
    reply_Content = data_Words.output_word
    print(reply_Content)
    return reply_Content


# 加入群組的時候寫入資料庫
def configuration(event, type):
    if type != -1:
        # 到資料庫查看看有沒有這個groupid
        groupId = botConfig.query.filter_by(GroupId=type).first()
        print('groupId', groupId)
        # roomId = botConfig.query.filter_by(GroupId=event.source.room_id).first()
        # 如果有的話查出他的status
        if groupId is not None:
            gid = botConfig.query.filter_by(GroupId=type).first()
            print('gid', gid)
            botStatus = gid.Status
            print('botStatus', botStatus)
            # 如果設定是true就給機器人說話
            if botStatus == 'True':
                reply_Content = reply(event)
                return reply_Content
        # 如果沒有的話，新增一筆資料，並且把status設定為true
        elif groupId is None:
            botConversationStatus = botConfig(GroupId=type, Item='Conversation', Status='True')
            # botCrawlStatus = botConfig(GroupId=type, Item='Craw', Status='True')
            print('機器人說話狀態', botConversationStatus.Status)
            # print('機器人爬蟲狀態', botCrawlStatus.Status)
            db.session.add(botConversationStatus)
            db.session.commit()
            return '把這群組加入資料庫囉~'


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    print("event.reply_token:", event.reply_token)
    print("event.message.text:", event.message.text)

    # 介紹
    if event.message.text == '呵呵':
        buttons_template_message = TemplateSendMessage(
            alt_text='目錄',
            template=ButtonsTemplate(
                thumbnail_image_url='https://i.imgur.com/YTcwkEC.jpg?2',
                title='選擇服務',
                text='亨利家有60坪欸',
                actions=[
                    MessageTemplateAction(
                        label='開始使用',
                        text='開始使用'
                    )
                ]
            )
        )
        line_bot_api.reply_message(event.reply_token, buttons_template_message)

    # 分類項目
    if event.message.text == '近期上映電影':
        content = movie()
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=content))
        return 0

    if event.message.text == '正妹':
        content = ptt_beauty()
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=content))
        return 0

    if event.message.text == '笑話':
        content = joke()
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=content))
        return 0
    # 離開群組
    if event.message.text == '離開':
        if event.source.type == 'group':
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text='好吧...我走...就不要想起我~'))
            line_bot_api.leave_group(event.source.group_id)
        elif event.source.type == 'room':
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text='好吧...我走...就不要想起我~'))
            line_bot_api.leave_room(event.source.room_id)
        return 0
    # 學習單字
    if '學習' in event.message.text:
        content = learnWord(event)
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=content))
        return 0

    if event.message.text == '聊天關閉':
        if event.source.type == 'group':
            print('聊天關閉的groupId', event.source.group_id)
            closeBot(event, event.source.group_id)
        elif event.source.type == 'room':
            print('聊天關閉的groupId', event.source.room_id)
            closeBot(event, event.source.room_id)
        return 0

    if event.message.text == '聊天開啟':
        if event.source.type == 'group':
            print('聊天開啟的groupId', event.source.group_id)
            openBot(event, event.source.group_id)
        elif event.source.type == 'room':
            print('聊天開啟的groupId', event.source.room_id)
            openBot(event, event.source.room_id)
        return 0

    if event.message.text == '開始使用':
        buttons_template = TemplateSendMessage(
            alt_text='目錄',
            template=ButtonsTemplate(
                thumbnail_image_url='https://i.imgur.com/0UJbeHQ.jpg',
                title='選擇服務',
                text='請選擇',
                actions=[
                    MessageTemplateAction(
                        label='近期上映電影',
                        text='近期上映電影',
                    ),
                    MessageTemplateAction(
                        label='正妹',
                        text='正妹'
                    ),
                    MessageTemplateAction(
                        label='笑話',
                        text='笑話'
                    )
                ]
            )
        )
        line_bot_api.reply_message(event.reply_token, buttons_template)
        return 0

    # 針對是哪種類型的狀態去回話
    if event.message.text != -1:
        print(type(event.source.type))
        # 先判斷是否有加入群組或是房間
        if event.source.type == 'group':
            print(type(event.source.group_id))
            reply_Content = configuration(event, event.source.group_id)
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=reply_Content))
        elif event.source.type == 'room':
            print('這是房間的', event.source.room_id)
            reply_Content = configuration(event, event.source.room_id)
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=reply_Content))
        elif event.source.type == 'user':
            print('這是個人的', event.source.user_id)
            reply_Content = reply(event)
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=reply_Content))


if __name__ == "__main__":
    app.run(debug=True)
