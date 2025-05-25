#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only

import sys, os, csv, requests
from dataclasses import dataclass, asdict
from datetime import datetime, date, timedelta
from decimal import Decimal

@dataclass
class Position:
    name: str
    time: datetime
    contract: str
    oi: int = 0
    oi_change: int = 0
    #positions
    noncom_long: int = 0
    noncom_short: int = 0
    com_long: int = 0
    com_short: int = 0
    nonreport_long: int = 0
    nonreport_short: int = 0
    #change in positions
    noncom_long_change: int = 0
    noncom_short_change: int = 0
    com_long_change: int = 0
    com_short_change: int = 0
    nonreport_long_change: int = 0
    nonreport_short_change: int = 0
    price: Decimal = 0

def load_file(file_name):
    ret = {}
    with open(f'{file_name}.txt', 'r') as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        for row in reader:
            name = row[0]
            time = datetime.strptime(row[1], '%Y-%m-%d')
            contract = row[2].strip()
            oi = int(row[3])
            oi_change = int(row[4])
            noncom_long = int(row[5])
            noncom_short = int(row[6])
            com_long = int(row[7])
            com_short = int(row[8])
            nonreport_long = int(row[9])
            nonreport_short = int(row[10])
            noncom_long_change = int(row[11])
            noncom_short_change = int(row[12])
            com_long_change = int(row[13])
            com_short_change = int(row[14])
            nonreport_long_change = int(row[15])
            nonreport_short_change = int(row[16])
            price = int(row[17])
            p = Position(name, time, contract, oi, oi_change, noncom_long, noncom_short, com_long, com_short, nonreport_long, nonreport_short, noncom_long_change, noncom_short_change, com_long_change, com_short_change, nonreport_long_change, nonreport_short_change, price)
            if contract not in ret.keys():
                ret[contract] = []
            ret[contract].append(p)
    return ret

def get_moex_positions(ticker, date):
    url = f"https://iss.moex.com/iss/statistics/engines/futures/markets/forts/openpositions/{ticker}.json"
    params = {'date': date}
    ret = requests.get(url, params=params)
    return None if ret.status_code != 200 else ret.json()

def get_moex_positions2(ticker, date):
    url = f"https://www.moex.com/api/contract/OpenOptionService/{date}/F/{ticker}/json"
    ret = requests.get(url)
    return None if ret.status_code != 200 else ret.json()

def verify_consistency(positions):
    if len(positions) < 2:
        return
    prev = None
    for p in positions:
        cur = p
        if prev != None:
            if cur.oi != (prev.oi + cur.oi_change):
                print(cur.oi_change, 'should be', cur.oi - prev.oi)
                print(cur)
                print(prev)
                sys.exit('check open interest')
            if cur.com_long != (prev.com_long + cur.com_long_change):
                print(cur.com_long_change, 'should be', cur.com_long - prev.com_long)
                sys.exit('check commercials longs')
            if cur.com_short != (prev.com_short + cur.com_short_change):
                print(cur.com_short_change, 'should be', cur.com_short - prev.com_short)
                sys.exit('check commercials shorts')
            if cur.nonreport_long != (prev.nonreport_long + cur.nonreport_long_change):
                print(cur.nonreport_long_change, 'should be', cur.nonreport_long - prev.nonreport_long)
                sys.exit('check small speculators longs')
            if cur.nonreport_short != (prev.nonreport_short + cur.nonreport_short_change):
                print(cur.nonreport_short_change, 'should be', cur.nonreport_short - prev.nonreport_short)
                sys.exit('check small speculators shorts')
            if cur.noncom_long != (prev.noncom_long + cur.noncom_long_change):
                sys.exit('check large speculators longs')
            if cur.noncom_short != (prev.noncom_short + cur.noncom_short_change):
                sys.exit('check large speculators shorts')
        prev = cur
    return

def load_moex_position(data):
    if not data or len(data) != 2:
        return
    com = None
    nonreport = None
    if data[0][2] == 0:
        if data[1][2] == 1:
            com = data[0]
            nonreport = data[1]
    if data[0][2] == 1:
        if data[1][2] == 0:
            com = data[1]
            nonreport = data[0]
    name = com[1] + ' - MOEX'
    time = datetime.strptime(com[0], '%Y-%m-%d')
    contract = com[1].strip()
    oi = int(com[5]) + int(com[6]) + int(nonreport[5]) + int(nonreport[6])
    oi_change = int(com[7]) + int(com[8]) + int(nonreport[7]) + int(nonreport[8])
    noncom_long = 0
    noncom_short = 0
    com_long = int(com[5])
    com_short = int(com[6])
    nonreport_long = int(nonreport[5])
    nonreport_short = int(nonreport[6])
    noncom_long_change = 0
    noncom_short_change = 0
    com_long_change = int(com[7])
    com_short_change = int(com[8])
    nonreport_long_change = int(nonreport[7])
    nonreport_short_change = int(nonreport[8])
    p = Position(name, time, contract, oi, oi_change, noncom_long, noncom_short, com_long, com_short, nonreport_long, nonreport_short, noncom_long_change, noncom_short_change, com_long_change, com_short_change, nonreport_long_change, nonreport_short_change)
    return p

def get_positions(tickers):
    ret = {}
    d1 = date.today() - timedelta(days=4)
    d2 = date.today()
    days = [d1 + timedelta(days=x) for x in range((d2-d1).days + 1)]
    for ticker in tickers:
        p = []
        for day in days:
            r = get_moex_positions(ticker, day)
            r = r['open_positions']['data']
            if r:
                print(r)
            i = load_moex_position(r)
            if i:
                p.append(i)
        ret[ticker] = p
    return ret

def save_file(cur, year):
    if not cur:
        return
    with open(f"{year}.txt", "w", newline="") as file:
        for ticker in cur.keys():
            for i in cur[ticker]:
                writer = csv.writer(file)
                p = list(asdict(i).values())
                p[1] = p[1].strftime("%Y-%m-%d")
                l = []
                l.append(p)
                writer.writerows(l)

def merge_positions(new, cur):
    for ticker in new.keys():
        for i in new[ticker]:
            found = 0
            for j in cur[ticker]:
                if i.time == j.time:
                    found = 1
                    if i.com_long_change != j.com_long_change or i.nonreport_long_change != j.nonreport_long_change or i.com_long != j.com_long:
                        sys.exit("check pulled data")
            if found == 0:
                print("adding ", i)
                cur[ticker].append(i)
    return cur

def main():
    if not os.path.exists('../db/moex'):
        print('cannot find ../db/moex folder, cd to src directory and run it again')
        return
    os.chdir('../db/moex')
    year = date.today().year
    tickers = ['NASD', 'SPYF', 'MXI', 'MIX', 'RTS', 'Si', 'USDRUBTOM', 'ED', 'RGBI', 'GL', 'GOLD', 'GLDRUBTOM', 'SILV', 'Eu', 'EURRUBTOM', 'BR']
    cur = load_file(year)
    for ticker in tickers:
        verify_consistency(cur[ticker])
    new = get_positions(tickers)
    cur = merge_positions(new, cur)
    save_file(cur, year)
    return

if __name__ == '__main__':
    main()
