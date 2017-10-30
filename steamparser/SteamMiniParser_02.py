import requests
from urllib.request import urlopen, Request
from urllib.parse import urlparse, parse_qs, urlunparse, urlencode
from bs4 import BeautifulSoup as bs
from bs4 import SoupStrainer
import re
import datetime, time
import gzip, json
import sys
import csv
import numpy as np
from main_02 import Application


################################################################################################
#    DECORATORS     ############################################################################
################################################################################################
def timer_d(func):
    def tmp(*args, **kwargs):
        t = time.time()
        res = func(*args, **kwargs)
        print('Time: ', time.time()-t)
        return res
    return tmp


################################################################################################
#    URLs & Tags     ###########################################################################
################################################################################################
def get_spy_url(idi):
    sheme = 'http'
    netloc = 'steamspy.com'
    path = '/api.php'
    # Query ####################################################################################
    query = urlencode({'request': 'appdetails',
                       'appid': idi})
    url = urlunparse((sheme, netloc, path, '', query, ''))
    return url

def get_url(genre_tags, n_of_players_tags, pressed=[], page='1'):
    sheme='http'
    netloc='store.steampowered.com'
    path='/search/'
    # Query ####################################################################################
    tag_list='-1'
    category3_list=''
    for category in pressed:
        try:
            tag_list += ',' + genre_tags[category]
        except: 
            category3_list += ',' + n_of_players_tags[category]
    query=urlencode({'category1': '998',
                     'category3': category3_list,
                     'sort_by': 'Released_DESC',
                     'page': page,
                     'tags': tag_list})
    url = urlunparse((sheme, netloc, path, '', query, ''))
    return url

def get_tags():
    url = 'http://store.steampowered.com/search/?category1=998&category3=&sort_by=Released_DESC&page=1&tags=-1%27'
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36',
               'Accept-encoding': 'gzip, deflate',
               'Accept-Language': 'en-US',
               'Cookie': 'timezoneOffset=10800,0'}
    req = Request(url, headers=headers)
    try:
        response = urlopen(req)
    except: print('Error while connecting to the Internet')
    bsobj = bs(gzip.decompress(response.read()), 'lxml')
    all_tags = bsobj.findAll('div', {'class': 'block_content block_content_inner'}, limit=3)
    tags = all_tags[0].findChildren('div', {'class': 'tab_filter_control '})
    category3 = all_tags[2].findChildren('div', {'class': 'tab_filter_control'})
    tags = dict((i.get('data-loc'), i.get('data-value')) for i in tags)
    category3 = dict((i.get('data-loc'), i.get('data-value')) for i in category3)
    return tags, category3


################################################################################################
#    MAIN STEAM BODY     #######################################################################
################################################################################################
@ timer_d
def get_suitable_apps(indie_bool, dates, tags, n_of_reviews=0, gui=None):
    # Inputs ###################################################################################
    print(dates)
    date_closer = int(dates[0])
    date_further = int(dates[1])
    if indie_bool:
        tags.append('Indie')
    # Dependancies #############################################################################
    genre_tags, n_of_players_tags = get_tags()
    page = '1'
    strainer = SoupStrainer('div', {'id': 'search_result_container'})
    temp_bug = 0
    temp_trigger = False
    started_trigger = False
    GameList = []
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36',
               'Accept-encoding': 'gzip, deflate',
               'Accept-Language': 'en-US',
               'Cookie': 'timezoneOffset=10800,0'}    
    i = 1
    # ProgressBar variables ####################################################################
    days = set()
    accum = 0
    done = False
    diff = date_further - date_closer
    trigger = False
    filled = 7
    gui.progress(7)
    tme = time.time()
    # Selecting games ##########################################################################
    while True:
        # Getting html #########################################################################
        url = get_url(genre_tags, n_of_players_tags, pressed = tags, page=page)
        req = Request(url, headers = headers)
        try:
            response = urlopen(req)
        except: print('Error while connecting to the Internet')
        # Soup object ##########################################################################
        soup = bs(gzip.decompress(response.read()), 'lxml', parse_only=strainer)
        # Dividing games #######################################################################
        Row = soup.find('div', {'id': 'search_result_container'}).findChildren('a')[:25]
        Row = [[item] for item in Row]
        Row, temp_bug, temp_trigger, started_trigger = add_initial_info(Row, date_closer, date_further,
                                                                        temp_bug, temp_trigger, started_trigger, n_of_reviews)
        print(i, ': ' ,len(Row))
        i+=1
        # Progress Bar #########################################################################
        for game in Row:
            if len(days) < min(7, diff):
                for game in Row:
                    days.add(game[1])
            if len(days) == min(7, diff):
                if not done:
                    days = list(days)
                    temp = [item[1] for item in (GameList+Row)]
                    for item in days:
                        filled += temp.count(item)
                    expected = filled/min(7,diff)*diff
                    filled += 100/(expected - len(GameList) - len(Row))
                    gui.progress(filled - 7)
                    #filled += (expected - len(GameList) - 7)
                    done = True
                    once = False
                    accum = 0
        if done:
            if not once:
                once = True
            else:
                accum += 100/expected*len(Row)
                if filled <= 92:
                    if accum >=1:
                        filled += accum
                        gui.progress(accum)
                        accum = 0
        # Completing target dataset ############################################################
        GameList += Row
        if temp_bug >= 3:
            break
        else: page = str(int(page)+1)
    # Completing list ##########################################################################
    first_time = time.time() - tme
    GameList = [[[i[0].find('span', {'class': 'title'}).get_text(), i[0].get('href'),i[0].get('data-ds-appid')], i[1], i[2]] for i in GameList]
    # Progress Bar #############################################################################
    gui.progress(98.999 - filled)
    try:
        print('A_E: ', expected, '\n')
    except: None
    print('Amount: ', len(GameList), '\n\n')
    # Adding Spy data ##########################################################################
    GameList = add_spy_info(GameList, first_time, gui)
    make_csv(GameList)
    return GameList


################################################################################################
#    ADDING INITIAL DATA     ###################################################################
################################################################################################
def add_initial_info(Row, date_closer, date_further, temp, temp_trigger, started, reviews_min):
    life = None
    to_remove = set()
    for game in Row:
        # Life Create ##########################################################################
        date = game[0].find('div', {'class': 'col search_released responsive_secondrow'}).get_text()
        life = convert_date(date)
        game.append(life)
        # Reviews ##############################################################################
        try:
            raw_review = game[0].find('div', {'class': 'col search_reviewscore responsive_secondrow'}).span
            if raw_review == None:
                raise Exception(NoneType)
            reviews = convert_review(raw_review)
        except:
            reviews = ['0%', 0]
        if reviews[1] < reviews_min:
            to_remove.add(Row.index(game))
            continue
        game.append(reviews)
    # Life Fix #################################################################################
    i = 1
    for game in Row:
        if not game[1]:
            try:
                while not game[1]:
                    game[1] = Row[Row.index(game)-i][1]
                    i += 1
            except:
                i = 1
                while not game[1]:
                    game[1] = Row[Row.index(game)+i][1]
                    i += 1
    # Select By Date ###########################################################################
    for game in Row:
        if check_date(game[1], date_closer, date_further):
            if not started:
                to_remove.add(Row.index(game))
                continue
            else:
                if temp_trigger == 1:
                    temp += 1
                else:
                    temp = 1
                    temp_trigger = 1
                to_remove.add(Row.index(game))
                continue
        else:
            started = True
            temp_trigger = 0
            temp = 0
            continue
    to_remove = list(to_remove)
    to_remove = [Row[i] for i in to_remove]
    for item in to_remove:
        Row.remove(item)
    return Row, temp, temp_trigger, started

def check_date(date, date_closer, date_further):
    diff = (datetime.date.today() - date).days
    if diff >= date_closer and diff <= date_further:
        return False
    else: return True


################################################################################################
#    ADDING SPY DATA     #######################################################################
################################################################################################
@timer_d
def add_spy_info(GameList, tme, gui):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 \
                (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36',
               'Accept-encoding': 'gzip',
               'Accept-Language': 'en-US'}
    # ProgressBar data #########################################################################
    accum = 0
    t = time.time()
    percent = 1/len(GameList)*100
    filled = False
    calculated = False
    for game in GameList:
        # ProgressBar data #####################################################################
        accum += percent
        if accum >= 1:
            gui.progress(accum)
            accum = 0
        # # Getting game data ####################################################################
        idi = game[0][2]
        url = get_spy_url(idi)
        req = Request(url, headers=headers)
        temp = 0
        while not temp:
            try:
                response = urlopen(req)
                temp = 1
            except: continue
        data = gzip.decompress(response.read())
        info = json.loads(data.decode())
        # Adding game data #######################################################################
        game.append(list(info.items()))
    return GameList


################################################################################################
#    Converters    #############################################################################
################################################################################################
def convert_date(date):
    months = {'Jan': [1,31], 'Feb': [2,28], 'Mar': [3,31],
              'Apr': [4,30], 'May': [5,31], 'Jun': [6,30],
              'Jul': [7,31], 'Aug': [8,31], 'Sep': [9,30],
              'Oct': [10,31], 'Nov': [11,30], 'Dec': [12,31]}
    p = re.compile(r',\s|\s')
    date = p.split(date)
    if len(date) == 2:
        return False
    date[1] = months[date[1]][0]
    date = [int(item) for item in date]
    today = datetime.date.today()
    released = datetime.date(date[2], date[1], date[0])
    return released

def convert_review(raw):
    reviews = raw.attrs['data-store-tooltip']
    regex_p = re.search(r'(\D?)+(Mixed<br>|Positive<br>|Negative<br>)\d+', reviews)
    percent = regex_p.group().split('<br>')[1]
    p = r'\d+ user'
    dir(re.search(p, reviews))
    number = re.search(p, reviews).group().split(' ')[0]
    return [percent+'%', int(number)]

def clean_list(to_clean):
    # Clean GameList ###########################################################################
    target_list = []
    for item in to_clean:
        lst = [i for i in item[0]][:-1] #title, url
        lst.append(item[1]) # date
        if item[3][16][1]:
            lst.append(item[3][16][1]) # price
        else: lst.append(0)
        lst.append(item[2][0]) # % positive
        lst.append(str(item[2][1])) # reviews
        lst.append(item[3][5][1]) # owners
        lst.append(item[3][7][1]) # players forever
        lst.append(item[3][13][1]) # median forever
        lst.append(item[3][11][1]) # average forever
        lst.append(' ')
        lst.append(item[3][2][1]) # developer
        lst.append(item[3][3][1]) # publisher
        lst.append(item[3][6][1]) # owners variance
        lst.append(item[3][8][1]) # players forever variance
        lst.append(item[3][9][1]) # players 2 week
        lst.append(item[3][10][1]) # -//- variance
        lst.append(item[3][12][1]) # average 2 weeks
        lst.append(item[3][14][1]) # median 2 weeks
        lst.append(item[3][15][1]) # ccu
        target_list.append(lst)
    return(target_list)

def make_csv(GameList):
    GameList = clean_list(GameList)
    tGameList = list(map(list, zip(*GameList)))
    date = time.strftime('%d.%m.%Y')
    tme = time.strftime('%H-%M')
    filename = 'steamscrap_{}_{}.csv'.format(date, tme)
    # Addintional heading info #################################################################
    amount = len(GameList)
    av_price = sum(list(map(lambda x: int(x), tGameList[3])))/amount
    av_review = sum(list(map(lambda x: int(x[:-1]), tGameList[4])))/amount
    all_owners = sum(list(map(lambda x: int(x), tGameList[6])))
    all_players = sum(list(map(lambda x: int(x), tGameList[7])))
    med_playtime = list(map(lambda x: int(x), tGameList[8]))       # эта характеристика получается очень кривой и вполне лишняя
    med_playtime.sort()                                            # 
    med_playtime = med_playtime[int(len(med_playtime)/2)]          #
    av_playtime = sum(list(map(lambda x: int(x), tGameList[9])))/amount
    fr_headers = ['Build date', 'Inputs', 'Amount of games', 'Average price', 'Average % of positive reviews',
                  'Owners whole', 'Players whole', 'Median playtime', 'Average playtime']
    firstrow = [date, 'INPUTS', amount, round(av_price,2), round(av_review,2),
                all_owners, all_players, med_playtime, round(av_playtime,2)]     # заменить инпутс инпутами в main.py
    header = ['Title', 'URL', 'Date', 'Price', '% of positive reviews', 'Reviews', 'Owners', 'Players Forever',
              'Median forever', 'Average forever', ' ', 'Developer', 'Publisher', 'Owners variance', 
              'Players forever variance', 'Players 2 weeks', 'Players 2 weeks variance', 'Average 2weeks', 
              'Median 2weeks', 'CCU']
    with open(filename, 'w', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile, delimiter=';', lineterminator='\n')
        writer.writerow(fr_headers)
        writer.writerow(firstrow)
        writer.writerow('')
        writer.writerow(header)
        for item in GameList:
            try:
                writer.writerow(item)
            except: print(item)
    return GameList