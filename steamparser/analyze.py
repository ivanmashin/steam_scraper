import sys
import csv
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

def datestr2num(frm, encoding='utf-8'):
    strconverter = mdates.strpdate2num(frm)
    return strconverter

def main(csv_file):
    # reading file ##########################################################
    lst = []
    with open (csv_file, newline='') as csv_file:
        reader = csv.reader(csv_file, delimiter=';', lineterminator='\n')
        for row in reader:
            lst.append(row)
    gamelist = lst[4:]
    gamelist = list(map(list, zip(*gamelist)))
    gamelist[2] = list(map(datestr2num('%Y-%m-%d'), gamelist[2]))
    title, url, date, price, perc, rev, own, p_for, m_for, av_for = gamelist[:10]
    print(p_for)
    # graphs ################################################################
    date_graph(date, av_for)

def date_graph(date, y):
    # converting vars #######################################################
    index = [[i for i,x in enumerate(date) if x==j] for j in set(date)]
    weights = [sum([int(y[i]) for i in index[j]]) for j in range(len(index))]
    s_dates = list(set(date))
    mpdates = list(map(mdates.num2date, s_dates))
    # plotting ##############################################################
    fig = plt.figure()
    ax1 = plt.subplot2grid((1,1), (0,0))
    ax1.hist(x=mpdates, weights=weights, histtype='stepfilled')
    # editing plot ##########################################################
    for label in ax1.xaxis.get_ticklabels():
        label.set_rotation(45)
    plt.xlabel('date')
    plt.ylabel('y')
    plt.subplots_adjust(bottom = 0.24)
    plt.show()
    pass

main('steamscrap_30.10.2017_13-39.csv')