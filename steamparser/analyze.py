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
    date_graph(date, rev)

def date_graph(dates, y=None):
    # converting vars #######################################################
    if y:
        index = [[i for i,x in enumerate(dates) if x==j] for j in set(dates)]
        weights = [sum([int(y[i]) for i in index[j]]) for j in range(len(index))]
        s_dates = list(set(dates))
        mpdates = list(map(mdates.num2date, s_dates))
    else:
        mpdates = list(map(mdates.num2date, dates))
        s_dates = list(set(dates))
        weights = None
    bins = s_dates + [s_dates[-1]+1]
    # plotting ##############################################################
    fig = plt.figure()
    ax1 = plt.subplot2grid((1,1), (0,0))
    ax1.hist(x=mpdates, weights=weights, bins=bins, rwidth=0.7, histtype='bar')
    # editing plot ##########################################################
    for label in ax1.xaxis.get_ticklabels():
        label.set_rotation(45)
    plt.xlabel('x')
    plt.ylabel('y')
    plt.subplots_adjust(bottom = 0.24)
    plt.show()
    pass

main('steamscrap_30.10.2017_13-39.csv')