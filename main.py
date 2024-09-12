import csv
from datetime import datetime, timedelta

from dataset import Dataset
from utils import TimeFrame

Symbol = 'BTCUSDT'
INITIAL_AMOUNT = 20000


def read_trades_from_csv(csv_file):
    trades = []
    with open(csv_file, 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            trades.append(row)
    return trades


def get_date_range(trades):
    opened_at_times = [datetime.strptime(trade['opened_at'], '%Y-%m-%d %H:%M:%S').date() for trade in trades]
    closed_at_times = [datetime.strptime(trade['closed_at'], '%Y-%m-%d %H:%M:%S').date() for trade in trades]

    min_date = min(opened_at_times)
    max_date = max(closed_at_times)

    return datetime.combine(min_date, datetime.min.time()), datetime.combine(max_date, datetime.min.time()) + timedelta(days=1)


def fetch_market_data(symbol, timeframe, start, end):
    return Dataset.make(symbol=symbol, timeframe=timeframe, start=start, end=end)


def apply_filters(trades, dataset):
    filtered_trades = []

    for trade in trades:
        opened_at = datetime.strptime(trade['opened_at'], '%Y-%m-%d %H:%M:%S') - timedelta(minutes=1)

        matching_row = dataset.content.loc[dataset.content['time'] == opened_at]

        if matching_row.empty:
            continue

        rsi = matching_row['RSI_14'].values[0]
        cci = matching_row['CCI_14_0.015'].values[0]
        side = trade['side'].upper()
        if ((rsi < 30 and side == "LONG") or (rsi > 70 and side == "SHORT")) and ((cci < -100 and side == "LONG") or (cci > 100 and side == "SHORT")):
            filtered_trades.append(trade)

    return filtered_trades


def calculate_statistics(filtered_trades):
    long_trades = [trade for trade in filtered_trades if trade['side'].upper() == 'LONG']
    short_trades = [trade for trade in filtered_trades if trade['side'].upper() == 'SHORT']

    def print_trade_stats(trades, label):
        if not trades:
            print(f"{label} - No trades to calculate statistics.")
            return

        total_trades = len(trades)
        wins = sum(float(trade['profit_or_loss']) > 0 for trade in trades)
        winrate = (wins / total_trades) * 100

        pnl = sum(float(trade['profit_or_loss']) for trade in trades)

        max_up = max(float(trade['profit_or_loss']) for trade in trades) if trades else 0
        max_drawdown = min(float(trade['profit_or_loss']) for trade in trades) if trades else 0

        print(f"{label}:")
        print(f"  Total Trades: {total_trades}")
        print(f"  Winrate: {winrate:.2f}%")
        print(f"  Total PnL: {pnl:.2f}")
        print(f"  Max Up: {max_up:.2f}")
        print(f"  Max Drawdown: {max_drawdown:.2f}\n")

    print_trade_stats(filtered_trades, "Total Trades")
    print_trade_stats(long_trades, "Long Trades")
    print_trade_stats(short_trades, "Short Trades")


trades = read_trades_from_csv('TradesListBy_Klines-BTCUSDT-1m.csv')
start_date, end_date = get_date_range(trades)
dataset = fetch_market_data(Symbol, TimeFrame(1, 'm'), start_date, end_date)

filtered_trades = apply_filters(trades, dataset)
calculate_statistics(filtered_trades)
