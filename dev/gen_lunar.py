"""한국 음력(한국천문연구원 기준, korean_lunar_calendar 자료) → 압축 표.
각 음력 해: [설날 양력 서수(ordinal), 윤달 번호(0=없음), 달 길이 비트(1=30일, 순서대로, 윤달 포함)]"""
import json, sys
from datetime import date, timedelta
from korean_lunar_calendar import KoreanLunarCalendar as K
c=K(); years={}
d=date(1900,1,31); end=date(2050,12,31)
cur=None
while d<=end:
    c.setSolarDate(d.year,d.month,d.day)
    ly,lm,ld,leap=c.lunarYear,c.lunarMonth,c.lunarDay,c.isIntercalation
    if ld==1:
        y=years.setdefault(ly,{'start':None,'leap':0,'months':[]})
        if lm==1 and not leap: y['start']=d.toordinal()
        if leap: y['leap']=lm
        y['months'].append([lm,leap,0])
    if ly in years and years[ly]['months']:
        years[ly]['months'][-1][2]=ld
    d+=timedelta(1)
out={}
for ly,y in years.items():
    if y['start'] is None: continue
    ms=y['months']
    if ms[-1][2] not in (29,30): continue  # 마지막 해가 잘린 경우
    bits=''.join('1' if m[2]==30 else '0' for m in ms)
    out[ly]=[y['start'],y['leap'],bits]
print(min(out),max(out),len(out),file=sys.stderr)
json.dump(out,open(sys.argv[1],'w'),separators=(',',':'))
