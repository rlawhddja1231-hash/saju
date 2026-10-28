"""saju.py 와 lunar_python(6tail, 독립 구현)을 많은 순간에 대해 비교."""
import sys, random
sys.path.insert(0, sys.argv[1])
import saju
from datetime import datetime, timedelta
from lunar_python import Solar
random.seed(int(sys.argv[3]) if len(sys.argv)>3 else 1)
N=int(sys.argv[2]); bad=[]
def lp(bj):
    l=Solar.fromYmdHms(bj.year,bj.month,bj.day,bj.hour,bj.minute,bj.second).getLunar()
    e=l.getEightChar(); e.setSect(2)
    return [e.getYear(),e.getMonth(),e.getDay(),e.getTime()]
samples=[]
for _ in range(N):
    u=datetime(1900,3,1)+timedelta(seconds=random.randint(0,int((datetime(2100,11,1)-datetime(1900,3,1)).total_seconds())))
    samples.append(u)
# 절기 바로 앞뒤(±90초)도 많이 넣기
T=saju._load_terms()
for _ in range(N//2):
    y=random.randint(1901,2099); i=random.choice(saju.JIE_INDEX)
    t=T[y][i]; samples.append(t+timedelta(seconds=random.choice([-90,-75,75,90])))
for u in samples:
    bj=u+timedelta(hours=8)
    mine=saju.pillars_for(bj,u,"midnight",True)
    m=[saju.gz(mine[0]),saju.gz(mine[1]),saju.gz(mine[2]),saju.gz(mine[3])]
    ref=[x.replace('凶','') for x in lp(bj)]
    # 한자 간체 차이 없음(간지 글자는 같음)
    if m!=ref: bad.append((u,m,ref))
print('samples',len(samples),'mismatch',len(bad))
for b in bad[:15]: print(b)
