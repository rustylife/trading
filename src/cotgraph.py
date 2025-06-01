#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only

import csv, os, io, requests, zipfile
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from contextlib import closing
import plotext as plt

@dataclass
class Position:
    name: str
    time: datetime
    contract: str
    oi: int = 0
    noncom_long: int = 0
    noncom_short: int = 0
    com_long: int = 0
    com_short: int = 0
    nonreport_long: int = 0
    nonreport_short: int = 0
    price: Decimal = 0

def load_file(filename, contracts, ret):
    with open(filename, 'r') as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        for row in reader:
            name = row[0]
            if name == 'Market and Exchange Names':
                continue
            time = datetime.strptime(row[2], '%Y-%m-%d')
            contract = row[3].strip()
            oi = int(row[7])
            noncom_long = int(row[8])
            noncom_short = int(row[9])
            com_long = int(row[11])
            com_short = int(row[12])
            nonreport_long = int(row[15])
            nonreport_short = int(row[16])
            if contract in contracts:
                p = Position(name, time, contract, oi, noncom_long, noncom_short, com_long, com_short, nonreport_long, nonreport_short)
                ret.append(p)

def load_contract(positions, contract):
    ret = []
    if not positions:
        return
    for i in positions:
        if i.contract in contract:
            ret.append(i)
    return ret

def plot(p, name = ''):
    if not p or len(p) == 0:
        return
    p.sort(key=lambda x: x.time, reverse=False)
    large = []
    com = []
    small = []
    oi = []
    d = []
    for i in p:
        large.append(i.noncom_long - i.noncom_short)
        com.append(i.com_long - i.com_short)
        small.append(i.nonreport_long - i.nonreport_short)
        d.append(i.time.strftime("%m/%y"))
    plt.stacked_bar(d, [large], color = ["blue+"], labels = ["large specs"])
    plt.stacked_bar(d, [com], color = ["red+"], labels = ["commercials"])
    plt.stacked_bar(d, [small], color = ["orange+"], labels = ["small specs"])
    if name:
        plt.title(name)
    else:
        plt.title(p[len(p)-1].name + ' ' + p[len(p)-1].contract)
    plt.show()
    plt.cld()

def plot_oi(p, name = ''):
    if not p or len(p) == 0:
        return
    p.sort(key=lambda x: x.time, reverse=False)
    oi = []
    d = []
    for i in p:
        oi.append(i.oi)
        d.append(i.time.strftime("%m/%y"))
    plt.stacked_bar(d, [oi], color = ["green+"], labels = ["open interest"])
    if name:
        plt.title(name)
    else:
        plt.title(p[len(p)-1].name + ' ' + p[len(p)-1].contract)
    plt.show()
    plt.cld()

def plot_price(p, name = ''):
    return

def print_indexed_values(p, lookback_weeks=26):
    if not p or len(p) == 0:
        return
    last = p[0]
    c = last.com_long - last.com_short
    s = last.noncom_long - last.noncom_short
    ss = last.nonreport_long - last.nonreport_short
    c_min = s_min = ss_min = 0
    c_max = s_max = ss_max = 0
    for i in p:
        if i.time < datetime.fromtimestamp(datetime.now().timestamp() - lookback_weeks * 7 * 24 * 3600):
            continue
        c_min = min(c_min, i.com_long - i.com_short)
        s_min = min(s_min, i.noncom_long - i.noncom_short)
        ss_min = min(ss_min, i.nonreport_long - i.nonreport_short)
        c_max = max(c_max, i.com_long - i.com_short)
        s_max = max(s_max, i.noncom_long - i.noncom_short)
        ss_max = max(ss_max, i.nonreport_long - i.nonreport_short)
    idx_c = int(100 * (c - c_min) / (c_max - c_min + 0.000001))
    idx_s = int(100 * (s - s_min) / (s_max - s_min + 0.000001))
    idx_ss = int(100 * (ss - ss_min) / (ss_max - ss_min + 0.000001))
    print()
    print(f'{last.name}, {last.time.strftime("%Y-%m-%d")}')
    print(f'COMMERCIALS: {idx_c}\nSPECULATORS: {idx_s}\nSMALL SPECS: {idx_ss}')
    return

def need_to_update():
    if not os.path.exists('/dev/shm/cot'):
        os.mkdir('/dev/shm/cot')
        return True
    if len(os.listdir('/dev/shm/cot')) == 0:
        return True
    c = datetime.fromtimestamp(os.path.getmtime('/dev/shm/cot'))
    now = datetime.now()
    # COT gets released by CFTC around 12:35 on Friday
    friday = now.replace(hour=12, minute=35) + timedelta(days=(4 - now.weekday()))
    if now > friday and c < friday:
        for name in os.listdir('/dev/shm/cot'):
            path = os.path.join('/dev/shm/cot', name)
            if os.path.isfile(path):
                os.unlink(path)
        return True
    return False

def fetch_cftc_cot(lookback_years=5):
    if not need_to_update():
        return
    i = datetime.today().year
    j = datetime.today().year - lookback_years
    while i > j:
        try:
            r = requests.get(f'https://www.cftc.gov/files/dea/history/deacot{i}.zip')
            with closing(r), zipfile.ZipFile(io.BytesIO(r.content)) as archive:
                for member in archive.infolist():
                    archive.extract(member, path='/dev/shm/cot')
                    os.rename(f'/dev/shm/cot/{member.filename}', f'/dev/shm/cot/{i}.txt')
        except Exception as e:
            print(f'https://www.cftc.gov/files/dea/history/deacot{i}.zip', e)
        i = i - 1

def verify_consistency(p):
    return

def load_data(contracts, lookback_years=5):
    positions = []
    fetch_cftc_cot(lookback_years)
    i = datetime.today().year
    j = datetime.today().year - lookback_years
    while i > j:
        try:
            load_file(f'/dev/shm/cot/{i}.txt', contracts, positions)
        except Exception as e:
            print(e)
        i = i - 1
    return positions

def main():
    os.system('clear')
    os.chdir('/tmp')
    plt.theme('dark')
    contracts = ['240741', '240743', '13874U', '13874A', '13874+', '209747', '209742', '20974+', '239742', '239744', '239747', '12460+', '124603', '124608', '133741', '133742', '133LM1', '146021', '146022', '146LM1', '1170E1', '098662', '090741', '096742', '099741', '092741', '095741', '097741', '102741', '112741', '232741', '122741', '084691', '088691', '088695', '058644', '085692', '045601','042601', '044601', '043602', '043607', '04360Y', '020601', '020604', '134742', '134741', '067411', '06765A', '067651', '06765T']
    positions = load_data(contracts)
    i = 0
    for contract in contracts:
        c = load_contract(positions, contract)
        print_indexed_values(c, lookback_weeks=26)
        plot(c)
        plot_price(c)
        plot_oi(c)
        if i == 20:
            i = 0
            try:
                input("press Enter to continue...")
                os.system('clear')
            except Exception as e:
                print()
                exit()
        i += 1

if __name__ == '__main__':
    main()
