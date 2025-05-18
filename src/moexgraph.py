#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only

import sys, os, csv, requests
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
import plotext as plt

headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64)', 'Accept': 'application/json'}

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

def verify_consistency(positions):
    if len(positions) < 2:
        return
    prev = None
    for p in positions:
        cur = p
        if prev != None:
            if cur.oi != (prev.oi + cur.oi_change):
                print(cur.oi_change, 'should be', cur.oi - prev.oi)
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

def plot(p):
    if not p or len(p) == 0:
        return
    p.sort(key=lambda x: x.time, reverse=False)
    verify_consistency(p)
    large = []
    com = []
    small = []
    oi = []
    d = []
    for i in p:
        large.append(i.noncom_long - i.noncom_short)
        com.append(i.com_long - i.com_short)
        small.append(i.nonreport_long - i.nonreport_short)
        d.append(i.time.strftime('%m/%d'))
    plt.stacked_bar(d, [large], color = ['blue+'], labels = ['large specs'])
    plt.stacked_bar(d, [com], color = ['red+'], labels = ['commercials'])
    plt.stacked_bar(d, [small], color = ['orange+'], labels = ['small specs'])
    if p[0].name:
        plt.title(p[0].name)
    else:
        plt.title(p[len(p)-1].name + ' ' + p[len(p)-1].contract)
    plt.show()
    plt.cld()
    return

def plot_oi(p):
    if not p or len(p) == 0:
        return
    p.sort(key=lambda x: x.time, reverse=False)
    verify_consistency(p)
    oi = []
    d = []
    for i in p:
        oi.append(i.oi)
        d.append(i.time.strftime('%m/%d'))
    plt.stacked_bar(d, [oi], color = ['green+'], labels = ['open interest'])
    if p[0].name:
        plt.title(p[0].name)
    else:
        plt.title(p[len(p)-1].name + ' ' + p[len(p)-1].contract)
    plt.show()
    plt.cld()
    return

def fetch_file(url):
    r = requests.get(url, headers=headers)
    if r.status_code != 200:
        return None
    return r.text

def load_file(file_name):
    ret = []
    data = None
    if not os.path.exists('../db/moex'):
        url = f'https://raw.githubusercontent.com/rustylife/trading/main/db/moex/{file_name}.txt'
        data = fetch_file(url)
    else:
        with open(f'../db/moex/{file_name}.txt', 'r') as f:
            data = f.read()
    if not data:
        return
    reader = csv.reader(data.split('\n'), delimiter=',')
    for row in reader:
        if not row:
            continue
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
        ret.append(p)
    return ret

def main():
    os.system('clear')
    plt.theme('dark')
    years = [2023, 2024, 2025]
    tickers = ['NASD', 'SPYF', 'MXI', 'MIX', 'RTS', 'Si', 'USDRUBTOM', 'ED', 'RGBI', 'GL', 'GOLD', 'GLDRUBTOM', 'SILV', 'Eu', 'EURRUBTOM', 'BR']
    positions = []
    for year in years:
        positions = positions + load_file(year)
    for ticker in tickers:
        p = []
        for i in positions:
            if i.contract == ticker:
                p.append(i)
        plot(p)
        plot_oi(p)
    return

if __name__ == '__main__':
    main()
