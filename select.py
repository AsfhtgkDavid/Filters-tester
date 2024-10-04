from random import uniform, getrandbits

import tester
import json

from utils import TimeFrame


def load_filters() -> dict[str, list[int]]:
    with open('filters.json') as f:
        res = json.load(f)
    return res

def main():
    Symbol = 'ETHUSDT'

    trades = tester.read_trades_from_csv('TradesList-ETH11-min.csv')
    start_date, end_date = tester.get_date_range(trades)
    dataset = tester.fetch_market_data(Symbol, TimeFrame(1, 'm'), start_date, end_date)

    filters = load_filters()
    params: list[dict[str, list[list[str | float]] | float]] = []

    for _ in range(10):
        temp = {'long': [], 'short': []}
        used_filters = set()

        for filt, rng in filters.items():
            base_filt = filt.split('_')[0]
            if base_filt in used_filters:
                continue

            rand_val = uniform(0, 100)
            sign = '<' if getrandbits(1) else '>'
            value = uniform(rng[0], rng[1])

            if rand_val > 5:
                temp['long'].append([filt, sign, value])
            elif rand_val < 5:
                temp['short'].append([filt, sign, value])
            elif 47 < rand_val < 53:
                opposite_sign = '>' if sign == '<' else '<'
                temp['long'].append([filt, sign, value])
                temp['short'].append([filt, opposite_sign, value])
            else:
                continue

            used_filters.add(base_filt)

        filtered_trades = tester.apply_filters(trades, dataset, temp['long'], temp['short'])
        if not filtered_trades:
            continue

        temp['res'] = sum(float(trade['profit_or_loss']) for trade in filtered_trades)
        params.append(temp)
    print(params)



if __name__ == '__main__':
    main()