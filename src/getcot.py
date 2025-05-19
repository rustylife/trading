#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only

import os, requests
from datetime import datetime

def get_cot(url):
    r = requests.get(url)
    r.raise_for_status()
    r = r.content.decode('ascii').replace('\r\n', '\n')
    start = r.find('\n', r.find('includeHTML'))
    end = r.rfind('\n', start, r.rfind('includeHTML'))
    r = r[start:end]
    return r

def main():
    if not os.path.exists('../db/cot'):
        print('cannot find ../db/cot folder, cd to src directory and run it again')
        return
    os.chdir('../db/cot')
    url = f'https://www.cftc.gov/dea/futures/financial_lf.htm'
    r = get_cot(url)
    start = r.find('Futures Only Positions as of ') + len('Futures Only Positions as of ')
    end = r.find('\n', start)
    d = r[start:end].strip()
    d = datetime.strptime(d, '%B %d, %Y').strftime("%Y-%m-%d")
    print(d)
    data = ''
    for i in r.splitlines():
        data = data + i.rstrip() + '\n'
    with open(d + '.txt', 'w') as f:
        f.write(data)

if __name__ == '__main__':
    main()
