#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only

import os, requests
import csv, statistics
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET

headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64)", "Accept": "application/json"}

class Data:
    name: str

def get_price(ticker):
    return get_price_yahoo(ticker)

def get_price_yahoo(ticker):
    url = f'https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?&interval=1d&range=1d'
    r = requests.get(url, headers=headers)
    if r.status_code != 200:
        return None
    price = r.json()['chart']['result'][0]['meta']['regularMarketPrice']
    close = r.json()['chart']['result'][0]['meta']['chartPreviousClose']
    return [close, price]

def get_price_yahoo2(ticker, interval='1d', span='1y', period1 = None, period2 = None):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?&interval={interval}&range={span}"
    if period1 and period2:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?&period1={period1}&period2={period2}&interval={interval}"
    r = requests.get(url, headers=headers)
    if r.status_code != 200:
        return None
    data = r.json()["chart"]["result"][0]
    ret = []
    i = 0
    if 'timestamp' not in data:
        return None
    while i < len(data['timestamp']):
        t = Data()
        t.data = data
        t.fifty_two_week_high = data['meta']['fiftyTwoWeekHigh']
        t.fifty_two_week_low = data['meta']['fiftyTwoWeekLow']
        item = data['indicators']['quote'][0]
        t.open = item['open'][i]
        t.high = item['high'][i]
        t.low = item['low'][i]
        t.close = item['close'][i]
        t.volume = item['volume'][i]
        t.timestamp = data['timestamp'][i]
        i += 1
        if t.open == None:
            continue
        ret.append(t)
    return ret

def print_price(symbol, price):
    old = price[0]
    new = price[1]
    if new/old < 0.99:
        print(f'{symbol:8}', f'{new:8} ', '\033[0;31m' + f'{new / old * 100 - 100:.2f}%', end='\n')
    elif new/old > 1.01:
        print(f'{symbol:8}', f'{new:8} ', '\033[0;32m' + f'+{new / old * 100 - 100:.2f}%', end='\n')
    else:
        print(f'{symbol:8}', f'{new:8} ', end='\n')
    print('\033[0;0m', end='')
    return

def get_news(time_zone=None, time_filter='time_only', countries=None, importances=None, categories=None, from_date=None, to_date=None):
    url = 'https://www.investing.com/economic-calendar/Service/getCalendarFilteredData'
    headers = {'User-Agent': 'Mozilla/5.0', 'X-Requested-With': 'XMLHttpRequest', 'Accept': 'application/json'}
    data = {'country[]': ['4', '5', '6', '7', '10', '11', '12', '14', '17', '21', '22', '25', '26', '32', '35', '36', '37', '39', '43', '56', '63', '72', '110', '114'],
            #'categories[]': ['', ''],
            'timeZone': '5', 'importance[]': ['2', '3'], 'timeFilter': 'timeOnly',
            'dateFrom': f'{datetime.now().strftime("%Y-%m-%d")}',
            'dateTo': f'{(datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")}',
            #'currentTab': 'thisWeek',
            'submitFilters': 1, 'limit_from': 0
            }
    req = requests.post(url, headers=headers, data=data)
    data = req.json()['data'].replace('&nbsp;', '').replace('&', '&amp;')
    ret = []
    root = ET.fromstring('<root>' + data + '</root>')
    for child in root:
        if not child.attrib:
            continue
        if 'event_attr_ID' not in child.attrib:
            id_ = child.attrib['id'].split('eventRowId_')[1]
            time = child[0].text
            currency = child[1][0].attrib['title']
            importance = child[2][0].text
            event = child[3].text
            ret.append({'id': id_, 'date': None, 'time': time, 'zone': '5', 'currency': currency, 'importance': importance, 'event': event, 'actual': None, 'forecast': None, 'previous': None})
            continue
        id_ = child.attrib['event_attr_ID']
        date = child.attrib['data-event-datetime']
        time = child[0].text
        currency = child[1][0].attrib['title']
        importance = child[2].attrib['title']
        actual = child[4].text
        forecast = child[5].text
        previous = child[6][0].text
        event = child[3][0].text
        ret.append({'id': id_, 'date': date, 'time': time, 'zone': '5', 'currency': currency, 'importance': importance, 'event': event, 'actual': actual, 'forecast': forecast, 'previous': previous})
    return ret

def print_market():
    print_price('VIX', get_price('^VIX'))
    print_price('SKEW', get_price('^SKEW'))
    print_price('ES', get_price('MES=F'))
    print_price('NQ', get_price('MNQ=F'))
    print_price('M2K', get_price('M2K=F'))
    print_price('USD/CAD', get_price('CAD=X'))
    print_price('USD/RUB', get_price('RUB=X'))
    print_price('BTC=F', get_price('BTC=F'))
    print_price('GC=F', get_price('GC=F'))
    print_price('CL=F', get_price('CL=F'))
    print_price('2YY=F', get_price('2YY=F'))
    print_price('10Y=F', get_price('10Y=F'))
    return

def get_cboe_data(date):
    url = f'https://cdn.cboe.com/data/us/options/market_statistics/daily/{date}_daily_options'
    ret = requests.get(url)
    return None if ret.status_code != 200 else ret.json()

def cnn_fear_and_greed():
    d = datetime.now().strftime("%Y-%m-%d")
    url = f'https://production.dataviz.cnn.io/index/fearandgreed/graphdata/{d}'
    ret = requests.get(url, headers=headers)
    fng_score = ret.json()['fear_and_greed']['score']
    fng_rating = ret.json()['fear_and_greed']['rating']
    print(f'Fear and Greed Index: {fng_score:.2f} [{fng_rating}]')
    url = f'https://www.binance.com/bapi/composite/v1/friendly/pgc/card/fearGreedHighestSearched'
    ret = requests.get(url, headers=headers)
    return

def cnbc_furu_sentiment(cnbc_furu):
    url = f'https://www.cnbc.com/{cnbc_furu}/'
    ret = requests.get(url, headers=headers)
    s = str(ret.content)
    s = s[s.find('Disclosures as of'):]
    s = s[:s.find('socialMediaInfo')]
    s = s.replace('\\\\u002F','/')
    s = s.replace(u'\\xc2\\xa0', u' ')
    print(s[:s.find('"]}')])
    s = s[s.find(':["') + 3:]
    s = s[:s.find('"')]
    print(s)
    return

def fade_twitter_furu(furu):
    #url = 'https://api.twitter.com/2/tweets/search/recent'
    return ret

def print_news():
    n = []
    for i in get_news():
        n.append([i['id'], i['time'], i['currency'], i['event'], i['actual'], i['forecast'], i['previous']])
    if not n:
        return
    header = ['id', 'time', 'currency', 'event', 'actual', 'forecast', 'previous']
    fmt ='{2:>8} {3:>16} {4:>45} {5:>9} {6:>9} {7:>9}'
    print(fmt.format('', *header))
    for i in n:
        if i[1] == None:
            i[1] = 'None'
        if i[6] == None:
            i[6] = 'None'
        if i[5] == None:
            i[5] = 'None'
        if i[4] == None:
            i[4] = 'None'
            if i[5] != 'None':
                i[4] = 'TBA'
        print(fmt.format('', *i))
    return

def print_pc_ratio():
    d = datetime.now()
    pcr = None
    i = 0
    while i < 3:
        d = datetime.now() - timedelta(days=i)
        pcr = get_cboe_data(f'{d.strftime("%Y-%m-%d")}')
        if pcr:
            break
        i = i + 1
    if not pcr:
        return
    print('CBOE ' + d.strftime('%m/%d/%y') + ':')
    try:
        for i in pcr['ratios']:
            name = i['name']
            if name == 'SPX + SPXW PUT/CALL RATIO':
                print(f'{i["name"]}: {i["value"]}')
            if name == 'EQUITY PUT/CALL RATIO':
                print(f'{i["name"]}: {i["value"]}')
    except:
        return
    return

def get_onof_url():
    url = 'https://www.globalxetfs.com/funds/onof/'
    r = requests.get(url, headers=headers)
    s = str(r.content)
    start = s.find("https://assets.globalxetfs.com/holdings/onof_full-holdings")
    s = s[start:]
    end = s.find("csv") + len("csv")
    url = s[:end]
    return url

def fade_asset_managers():
    if not os.path.exists('/dev/shm/funds'):
        os.mkdir('/dev/shm/funds')
    fade_asset_manager('HFND', 'https://unlimitedetfs.com/data/TidalETF_Services.40ZZ_Holdings_HFND.csv')
    fade_asset_manager('RORO', 'https://www.atacfunds.com/download/4421')
    fade_asset_manager('JOJO', 'https://www.atacfunds.com/download/4415')
    fade_asset_manager('EHLS', 'https://evenherd-wix.s3.us-east-2.amazonaws.com/holdings.csv')
    fade_asset_manager('SHRT', 'https://gothametfs.com/shrt/DownloadHoldings')
    fade_asset_manager('ONOF', get_onof_url())
    fade_asset_manager('ISMF', 'https://www.blackrock.com/us/individual/products/342102/fund/1464253357814.ajax?fileType=csv&fileName=ISMF_holdings&dataType=fund')
    return

def fade_asset_manager(ticker, url):
    positions = []
    try:
        r = requests.get(url, headers=headers)
        if r.status_code != 200:
            return
        all_positions = str(r.text)
        lines = r.text.splitlines()
        date = ''
        new = []
        for i in lines:
            if i.startswith('Fund Holdings as of'):
                date = i[21:-1]
                continue
            if ",,," in i:
                continue
            if i.count(',') < 5:
                continue
            if 'The content contained herein' in i:
                break
            new.append(i)
        lines = new
        reader = csv.DictReader(lines)
        for row in reader:
            positions.append(row)
        if not positions:
            return
        if ticker == 'ONOF':
            positions = sorted(positions, key=lambda x: float(x['% of Net Assets']), reverse=True)
        elif ticker == 'ISMF':
            positions = sorted(positions, key=lambda x: float(x['Notional Value'].replace(',','')), reverse=True)
        elif ticker == 'SHRT':
            positions = sorted(positions, key=lambda x: float(x['Percentage of Net Assets'][:-1]), reverse=True)
        else:
            positions = sorted(positions, key=lambda x: float(x['Weightings'][:-1]), reverse=True)
        if len(positions) > 20:
            positions = positions[:10] + positions[-10:]
        print()
        if date:
            print(f'{ticker} as of {date}')
        elif 'Date' in positions[0].keys():
            print(f'{ticker} as of {positions[0]["Date"]}')
        elif 'As Of Date' in positions[0].keys():
            print(f'{ticker} as of {positions[0]["As Of Date"]}')
        else:
            print(f'{ticker}')
        header = ["Weightings", "Ticker", "Shares", "Price", "Value", "Name"]
        print("{:<12} {:<12} {:<15} {:<10} {:<15} {}".format(*header))
        print("=" * 90)
        for i in positions:
            if ticker == 'ONOF':
                print("{:<12} {:<12} {:<15} {:<10} {:<15} {}".format(i['% of Net Assets'] + '%', i['Ticker'], i['Shares Held'], i['Market Price ($)'], i['Market Value ($)'], i['Name']))
            elif ticker == 'ISMF':
                print("{:<12} {:<12} {:<15} {:<10} {:<15} {}".format(i['Weight (%)'] + '%', i['Ticker'], i['Shares'], i['Price'], i['Notional Value'], i['Name']))
            elif ticker == 'SHRT':
                if len(i['Ticker']) > 10:
                    i['Ticker'] = i['Ticker'][:9]
                print("{:<12} {:<12} {:<15} {:<10} {:<15} {}".format(i['Percentage of Net Assets'], i['Ticker'], i['Shares Held'], "0", i['Market Value'], i['Name']))
            else:
                if len(i['Price']) > 8:
                    i['Price'] = i['Price'][:8]
                print("{:<12} {:<12} {:<15} {:<10} {:<15} {}".format(i['Weightings'], i['StockTicker'], i['Shares'], i['Price'], i['MarketValue'], i['SecurityName']))
        if not os.path.exists(f'/dev/shm/funds/{ticker.lower()}-{datetime.now().strftime("%Y-%m-%d")}.csv'):
            with open(f'/dev/shm/funds/{ticker.lower()}-{datetime.now().strftime("%Y-%m-%d")}.csv', 'w', newline='') as file:
                file.write(all_positions)
            pass
    except Exception as e:
        print(ticker, e)
        pass
    return

def find_move(data):
    if not data:
        return None, None
    c = []
    for i in data:
        c.append(max(i.open, i.low, i.high, i.close) - min(i.open, i.low, i.high, i.close))
    m = sorted(c)[-20:][0]
    return m, statistics.median(c)

def get_tickers():
    tickers = []
    url = f'https://www.sec.gov/files/company_tickers.json'
    r = requests.get(url, headers=headers)
    for i, j  in r.json().items():
        tickers.append(j['ticker'])
    return tickers

def find_volume(data):
    v = []
    if not data:
        return None, None, None
    for i in data:
        v.append(i.volume)
    high = max(v)
    low = min(v)
    return high, low, statistics.median(sorted(v))

def find_52w_high_or_low(data):
    result = []
    for ticker in data.keys():
        p = data[ticker]
        cur = p[0][-1]
        if cur.open >= cur.fifty_two_week_high or cur.open <= cur.fifty_two_week_low:
            result.append(f'{ticker} o: {cur.open:g} 52w_h: {cur.fifty_two_week_high:g} 52w_l: {cur.fifty_two_week_low:g} v: {cur.volume:,}')
    if result:
        print('new highs/lows:')
        for i in result:
            print(i)
    return

def find_high_volume(data):
    result = []
    for ticker in data.keys():
        p = data[ticker]
        cur = p[0][-1]
        v1 = p[2]
        v2 = p[3]
        if v1 and v2 and (v1 > v2*7 or v2 > v1*7):
            result.append(f'{ticker} {cur.close:g} new median v: {int(v1):,} old median v: {int(v2):,}')
    if result:
        print('\nhigh volume change:')
        for i in result:
            print(i)
    return

def find_high_relative_volume(data):
    return

def find_strength(data):
    result = []
    for ticker in data.keys():
        p = data[ticker]
        continue
    if result:
        print('\nstrength/weakness on down/up days:')
        for i in result:
            print(i)
    return

def find_gappers(data):
    result = []
    for ticker in data.keys():
        p = data[ticker]
        cur = p[0][-1]
        prev = p[0][-2]
        v1 = p[2]
        if cur.volume < 500000:
            continue
        if cur.close/prev.close > 1.09:
            result.append(f'+{int((cur.close/prev.close - 1) * 100)}% {ticker} prev c: {prev.close:g} o: {cur.open:g} c: {cur.close:g} v: {cur.volume:,} median v: {int(v1):,}')
        if cur.close/prev.close < 0.91:
            result.append(f'-{int((1 - cur.close/prev.close) * 100)}% {ticker} prev c: {prev.close:g} o: {cur.open:g} c: {cur.close:g} v: {cur.volume:,} median v: {int(v1):,}')
    if result:
        print('\ngappers:')
        for i in result:
            print(i)
    return

def screen_stocks():
    p = {}
    tickers = get_tickers()
    print(f'Getting price and volume for {len(tickers)} tickers..')
    for ticker in tickers:
        try:
            start = int(datetime.now().timestamp()) - 9 * 30 * 24 * 3600
            end = start + 30 * 24 * 3600
            new = get_price_yahoo2(ticker, '1d', '1mo')
            if len(new) < 2:
                continue
            cur = new[-1]
            prev = new[-2]
            if (cur.close < 7):
                continue
            old = get_price_yahoo2(ticker, '1d', None, start, end)
            high, low, v1 = find_volume(new)
            high, low, v2 = find_volume(old)
            if max(v1, v2) < 3000000:
                continue
            p[ticker] = [new, old, v1, v2]
        except Exception as e:
            pass
    print(f'{len(p)} tickers to analyze..')
    find_52w_high_or_low(p)
    find_gappers(p)
    find_high_volume(p)
    find_strength(p)
    return

def get_news_failure():
    return

def get_etf_flows():
    return

def main():
    os.system('clear')
    print_news()
    print()
    cnbc_furu_sentiment('dan-nathan')
    cnbc_furu_sentiment('guy-adami')
    print()
    print_market()
    print()
    print_pc_ratio()
    print()
    cnn_fear_and_greed()
    print()
    fade_asset_managers()
    print()
    screen_stocks()
    print()
    get_news_failure()
    return

if __name__ == '__main__':
    main()
