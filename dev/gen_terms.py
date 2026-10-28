"""24절기 시각(UTC) 표 만들기: lunar_python(寿星 알고리즘)과 PyEphem(VSOP87)을 서로 비교."""
import ephem, math, json, sys
from datetime import datetime, timedelta
from lunar_python import Solar
NAMES=['小寒','大寒','立春','雨水','惊蛰','春分','清明','谷雨','立夏','小满','芒种','夏至','小暑','大暑','立秋','处暑','白露','秋分','寒露','霜降','立冬','小雪','大雪','冬至']
LON={n:(285+15*i)%360 for i,n in enumerate(NAMES)}
def sunlon(d):
    s=ephem.Sun(); s.compute(d, epoch=d)
    e=ephem.Ecliptic(ephem.Equatorial(s.ra,s.dec,epoch=d), epoch=d)
    return math.degrees(e.lon)
def cross(target, guess):
    lo=ephem.Date(guess-3); hi=ephem.Date(guess+3)
    f=lambda d: ((sunlon(d)-target+180)%360)-180
    for _ in range(60):
        mid=ephem.Date((lo+hi)/2)
        if f(mid)<0: lo=mid
        else: hi=mid
    return ephem.Date((lo+hi)/2)
out={}; worst=0
for y in range(int(sys.argv[1]),int(sys.argv[2])+1):
    tab=Solar.fromYmd(y,6,1).getLunar().getJieQiTable()
    row=[]
    for n in NAMES:
        s=tab[n]
        if n in ('小寒','大寒') and s.getYear()!=y:
            s=Solar.fromYmd(y+1,6,1).getLunar().getJieQiTable()[n] if s.getYear()<y else s
        if s.getYear()!=y:
            s=Solar.fromYmd(y-1 if s.getYear()>y else y+1,6,1).getLunar().getJieQiTable()[n]
        assert s.getYear()==y,(y,n,s.toYmdHms())
        bj=datetime(s.getYear(),s.getMonth(),s.getDay(),s.getHour(),s.getMinute(),s.getSecond())
        utc=bj-timedelta(hours=8)
        e=cross(LON[n], ephem.Date(utc))
        ue=ephem.Date(e).datetime()
        diff=(ue-utc).total_seconds()
        worst=max(worst,abs(diff))
        row.append(round(utc.timestamp()) if False else int((utc-datetime(1970,1,1)).total_seconds()))
        if abs(diff)>120: print('DIFF',y,n,utc,ue,diff)
    out[y]=row
print('worst seconds',worst, file=sys.stderr)
json.dump(out,open(sys.argv[3],'w'))
