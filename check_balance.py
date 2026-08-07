import sqlite3
import pandas as pd

conn = sqlite3.connect("data/database/nifty100.db")   # Use your actual database path

balance = pd.read_sql("SELECT * FROM balancesheet", conn)
profit = pd.read_sql("SELECT * FROM profitandloss", conn)

print("Balance Columns")
print(balance.columns.tolist())

print("\nProfit Columns")
print(profit.columns.tolist())

conn.close()