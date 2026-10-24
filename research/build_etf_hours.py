#!/usr/bin/env python3
"""Rebuild BTC as it would trade on a spot-BTC ETF (IBIT hours) from 24/7 hourly data, so the rules can be tested on weekday session bars with a longer history than IBIT has.
    python3 research/build_etf_hours.py Bitstamp_BTCUSD_1h.csv [ibit.csv]
Input: CryptoDataDownload hourly CSV (unix,date,symbol,open,high,low,close,...; UTC). Optional real IBIT daily CSV (Date,Open,High,Low,Close) for validation.
Open = price at 9:30 ET (log-interpolated between hourly opens), close = price at 16:00 ET (13:00 on early-close days), high/low from hourly bars from the session's first hour on (includes the opening partial hour).
Writes btc_etfhours.csv and btc_utcday_bitstamp.csv (24/7 daily baseline).  Needs pandas_market_calendars.
Validated 2024-01..2026-10 against real IBIT: close-to-close corr 0.9989 (8 bps typical error), overnight/weekend gaps match (mean abs 167 vs 168 bps), range 98% of real; the open is the loosest (47 bps)."""
import sys
A=sys.argv[1]; IB=sys.argv[2] if len(sys.argv)>2 else None
import pandas as pd, numpy as np, pandas_market_calendars as mcal
d=pd.read_csv(A,skiprows=1,parse_dates=['date']).sort_values('date').reset_index(drop=True)
d['t']=d['date'].astype('datetime64[s]').astype('int64')//10**9 if False else (d['date']-pd.Timestamp('1970-01-01')).dt.total_seconds().astype('int64')
T=d['t'].values; O=d['open'].values; H=d['high'].values; L=d['low'].values; C=d['close'].values
lo=np.log(O)
def px(ts): return np.exp(np.interp(ts, T, lo))
# daily UTC bars (the 24/7 baseline)
d['day']=d['date'].dt.floor('D')
g=d.groupby('day'); day=pd.DataFrame({'Open':g['open'].first(),'High':g['high'].max(),'Low':g['low'].min(),'Close':g['close'].last()})
day=day.iloc[1:-1]; day.index.name='Date'; day.to_csv('btc_utcday_bitstamp.csv')
# ETF-hours bars
cal=mcal.get_calendar('NYSE'); sch=cal.schedule('2018-05-16','2026-10-23')
rows=[]
for dt,r in sch.iterrows():
    o=int(r.market_open.timestamp()); c=int(r.market_close.timestamp())
    if o<T[0]+3600 or c>T[-1]: continue
    m=(T>=(o//3600)*3600)&(T<c)       # hourly bars starting inside the session (first full hour on)
    hh=[px(o),px(c)]; ll=[px(o),px(c)]
    if m.any(): hh.append(H[m].max()); ll.append(L[m].min())
    rows.append((dt.date(),px(o),max(hh),min(ll),px(c)))
e=pd.DataFrame(rows,columns=['Date','Open','High','Low','Close']); e.to_csv('btc_etfhours.csv',index=False)
print(len(day),'utc-day bars;',len(e),'etf-hour bars', e.Date.iloc[0], e.Date.iloc[-1])
# validation vs real IBIT
if not IB: sys.exit()
ib=pd.read_csv(IB,parse_dates=['Date']); e['Date']=pd.to_datetime(e['Date'])
m=ib.merge(e,on='Date',suffixes=('_i','_c')).iloc[1:].reset_index(drop=True)
print('matched days',len(m),'of IBIT',len(ib),'| missing in construction:',sorted(set(ib.Date)-set(e.Date))[:5],'| extra in construction:',len(set(e.Date)-set(ib.Date)&set(e.Date[e.Date>=ib.Date.min()])))
def lr(x): return np.diff(np.log(x))
for nm,a,b in (('close-close',m.Close_i.values,m.Close_c.values),('open-open',m.Open_i.values,m.Open_c.values)):
    ra,rb=lr(a),lr(b); print(f'{nm}: corr {np.corrcoef(ra,rb)[0,1]:.4f}  mean abs diff {np.mean(abs(ra-rb))*1e4:.0f} bps  median abs diff {np.median(abs(ra-rb))*1e4:.0f} bps')
gi=np.log(m.Open_i.values[1:]/m.Close_i.values[:-1]); gc=np.log(m.Open_c.values[1:]/m.Close_c.values[:-1])
print(f'overnight/weekend gap (open vs prev close): corr {np.corrcoef(gi,gc)[0,1]:.4f}  mean abs diff {np.mean(abs(gi-gc))*1e4:.0f} bps | mean abs gap IBIT {np.mean(abs(gi))*1e4:.0f} vs built {np.mean(abs(gc))*1e4:.0f} bps | 5th pct IBIT {np.percentile(gi,5)*100:.1f}% built {np.percentile(gc,5)*100:.1f}%')
ri=(m.High_i-m.Low_i)/m.Close_i; rc=(m.High_c-m.Low_c)/m.Close_c
print(f'mean intraday range/close: IBIT {ri.mean()*100:.2f}% vs built {rc.mean()*100:.2f}%  (ratio {rc.mean()/ri.mean():.3f})')
# scale: IBIT price per BTC
print('IBIT/BTC ratio first/last:', (m.Close_i/m.Close_c).iloc[[0,-1]].round(6).tolist())