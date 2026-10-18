#!/usr/bin/env python3
"""Pull daily OHLC from Yahoo into data/*.csv (Date,Open,High,Low,Close).   pip install yfinance pandas   then: python3 data/download.py"""
import os, yfinance as yf
here = os.path.dirname(os.path.abspath(__file__))
for name, sym, start in (("iau", "IAU", "2005-01-28"), ("pplt", "PPLT", "2010-01-08"), ("btc", "BTC-USD", "2014-09-17")):
    d = yf.Ticker(sym).history(start=start, interval="1d", auto_adjust=False)[["Open", "High", "Low", "Close"]].dropna()
    d.index = d.index.tz_localize(None).normalize(); d.index.name = "Date"
    d.to_csv(os.path.join(here, f"{name}.csv")); print(name, len(d), d.index[0].date(), d.index[-1].date())
