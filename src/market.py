#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only

import os, requests, csv
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET

headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64)", "Accept": "application/json"}

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

def get_news(time_zone=None, time_filter='time_only', countries=None, importances=None, categories=None, from_date=None, to_date=None):
    url = 'https://www.investing.com/economic-calendar/Service/getCalendarFilteredData'
    headers = {'User-Agent': 'Mozilla/5.0', 'X-Requested-With': 'XMLHttpRequest', 'Accept': 'application/json'}
    data = {'country[]': ['4', '5', '6', '7', '10', '11', '12', '14', '17', '21', '22', '25', '26', '32', '35', '36', '37', '39', '43', '56', '63', '72', '110', '114'],
            'timeZone': '5', 'importance[]': ['2', '3'], 'timeFilter': 'timeOnly',
            'dateFrom': f'{datetime.now().strftime("%Y-%m-%d")}',
            'dateTo': f'{(datetime.now() + timedelta(days=0)).strftime("%Y-%m-%d")}',
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
    print('VIX ', get_price('^VIX')[1])
    print('SKEW', get_price('^SKEW')[1])
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

def fade_asset_managers():
    if not os.path.exists('/dev/shm/funds'):
        os.mkdir('/dev/shm/funds')
    fade_asset_manager('HFND', 'https://unlimitedetfs.com/data/TidalETF_Services.40ZZ_Holdings_HFND.csv')
    fade_asset_manager('HFGM', 'https://unlimitedetfs.wpenginepowered.com/data/TidalETF_Services.40ZZ_Holdings_HFGM.csv')
    fade_asset_manager('TFPN', 'https://blueprintip.com/wp-content/fund_files/files/wp-content/fund_files/files/BlueprintInvWeb.40T2.T2_ETF_Holdings.csv')
    fade_asset_manager('EHLS', 'https://evenherd-wix.s3.us-east-2.amazonaws.com/holdings.csv')
    fade_asset_manager('LQPE', 'https://peoalphaquestetf.com/data/TidalETF_Services.40ZZ_Holdings_LQPE.csv')
    fade_asset_manager('RORO', 'https://www.atacfunds.com/download/4421')
    fade_asset_manager('HF', 'https://daysadvisors.com/data/TidalETF_Services.40ZZ_Holdings_HF.csv')
    return

def fade_asset_manager(ticker, url):
    positions = []
    try:
        r = requests.get(url, headers=headers)
        if r.status_code != 200:
            return
        all_positions = str(r.text)
        lines = r.text.splitlines()
        new = []
        for i in lines:
            if i.count(',') < 5:
                continue
            new.append(i)
        lines = new
        reader = csv.DictReader(lines)
        for row in reader:
            positions.append(row)
        if not positions:
            return
        positions = sorted(positions, key=lambda x: float(x['Weightings'][:-1]), reverse=True)
        if len(positions) > 20:
            positions = positions[:10] + positions[-10:]
        print()
        if 'Date' in positions[0].keys():
            print(f'{ticker} as of {positions[0]["Date"]}')
        else:
            print(f'{ticker}')
        header = ["Weightings", "Ticker", "Shares", "Price", "Value", "Name"]
        print("{:<12} {:<12} {:<15} {:<10} {:<15} {}".format(*header))
        print("=" * 90)
        for i in positions:
            print("{:<12} {:<12} {:<15} {:<10} {:<15} {}".format(i['Weightings'], i['StockTicker'], i['Shares'], i['Price'], i['MarketValue'], i['SecurityName']))
        if not os.path.exists(f'/dev/shm/funds/{ticker.lower()}-{datetime.now().strftime("%Y-%m-%d")}.csv'):
            with open(f'/dev/shm/funds/{ticker.lower()}-{datetime.now().strftime("%Y-%m-%d")}.csv', 'w', newline='') as file:
                file.write(all_positions)
    except Exception as e:
        print(ticker, e)
    return

def main():
    os.system('clear')
    print_news()
    print()
    cnbc_furu_sentiment('dan-nathan')
    cnbc_furu_sentiment('guy-adami')
    cnbc_furu_sentiment('steven-grasso')
    print()
    print_market()
    print()
    print_pc_ratio()
    print()
    cnn_fear_and_greed()
    fade_asset_managers()
    return

if __name__ == '__main__':
    main()
