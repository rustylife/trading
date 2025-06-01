#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only

import os, requests, statistics
from datetime import datetime, timedelta

headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64)", "Accept": "application/json"}

class Data:
    name: str

def get_price_yahoo(ticker, interval='1d', span='1y', period1 = None, period2 = None):
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

def find_move(data):
    if not data:
        return None, None
    c = []
    for i in data:
        c.append(max(i.open, i.low, i.high, i.close) - min(i.open, i.low, i.high, i.close))
    m = sorted(c)[-10:][0]
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

def find_strength(data):
    result = []
    voo = get_price_yahoo('VOO', '1d', '5d')
    if len(voo) < 2:
        return
    cur = voo[-1].close
    prev = voo[-2].close
    for ticker in data.keys():
        ticker_cur = data[ticker][0][-1].close
        ticker_prev = data[ticker][0][-2].close
        if prev/cur > 1.00:
            if ticker_prev/ticker_cur < 0.96:
                result.append(f'{ticker} up {int((ticker_cur/ticker_prev*100)-100)}% on the down day')
        else:
            if ticker_prev/ticker_cur > 1.04:
                result.append(f'{ticker} down {int((ticker_cur/ticker_prev*100)-100)}% on the up day')
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

def set_sma(data):
    for i in range(len(data) - 10):
        window = data[i:i + 10]
        sma = sum(c.close for c in window) / 10
        data[i + 10].sma_10 = sma
    for i in range(len(data) - 20):
        window = data[i:i + 20]
        sma = sum(c.close for c in window) / 20
        data[i + 20].sma_20 = sma
    return

def get_trades(data):
    result = []
    for ticker in data.keys():
        p = data[ticker]
        if len(p[0]) < 30:
            continue
        set_sma(p[0])
        prev = p[0][-2]
        cur = p[0][-1]
        m = p[4]
        if cur.sma_10 - cur.sma_20 >= 0 and prev.sma_10 - prev.sma_20 < 0:
            result.append(f'wedge pop for {ticker} prev c: {prev.close:g} c: {cur.close:g}')
        if cur.sma_10 - cur.sma_20 < 0 and prev.sma_10 - prev.sma_20 >= 0:
            result.append(f'wedge drop for {ticker} prev c: {prev.close:g} c: {cur.close:g}')
        if (cur.high - prev.close) > m and cur.close < prev.close:
            result.append(f'exhaustion extension down for {ticker} prev c: {prev.close:g} c: {cur.close:g}')
        if (prev.close - cur.low) > m and cur.close > prev.close:
            result.append(f'exhaustion extension up for {ticker} prev c: {prev.close:g} c: {cur.close:g}')
    if result:
        print('\ntrade signals:')
        for i in result:
            print(i)
    return

def skip_ticker(ticker):
    p = get_price_yahoo(ticker, '1d', '3d')
    if not p or len(p) < 1:
        return True
    if (p[-1].close < 7):
        return True
    _, _, v = find_volume(p)
    if v < 5000000:
        return True
    return False

def screen_stocks():
    p = {}
    tickers = get_tickers()
    print(f'Getting price and volume for {len(tickers)} tickers..')
    for ticker in tickers:
        try:
            if skip_ticker(ticker):
                continue
            start = int(datetime.now().timestamp()) - 9 * 30 * 24 * 3600
            end = start + 30 * 24 * 3600
            new = get_price_yahoo(ticker, '1d', '40d')
            _, _, v1 = find_volume(new)
            if len(new) < 2:
                continue
            cur = new[-1]
            prev = new[-2]
            old = get_price_yahoo(ticker, '1d', None, start, end)
            _, _, v2 = find_volume(old)
            m, _ = find_move(new)
            p[ticker] = [new, old, v1, v2, m]
        except Exception as e:
            print(ticker, e)
    print(f'{len(p)} tickers to analyze..')
    find_52w_high_or_low(p)
    find_gappers(p)
    find_high_volume(p)
    find_strength(p)
    get_trades(p)
    return

def main():
    os.system('clear')
    screen_stocks()
    return

if __name__ == '__main__':
    main()
