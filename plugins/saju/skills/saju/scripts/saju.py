#!/usr/bin/env python3
"""saju.py — 사주팔자(四柱八字) 계산기. 파이썬 표준 라이브러리만 씁니다(설치할 것 없음).

AI가 사주를 '외워서' 뽑으면 기둥(간지)이 자주 틀립니다. 이 도구는 계산으로 뽑습니다.
  - 절기(입춘·경칩…) 시각: 1899~2101년, 두 가지 독립 계산(寿星 알고리즘, VSOP87)이 1분 안으로 일치한 표
  - 한국 표준시 역사(1908~1912 UTC+8:30, 1954~1961 UTC+8:30)와 서머타임(1948~1960, 1987~1988) 자동 반영
  - 한국 음력(한국천문연구원 기준, 1900~2049) 입력, 윤달 지원
  - 시간 기준 선택: 시계 시각 / 경도 보정(지방 평균시) / 진태양시(균시차까지)
  - 자시 처리 선택: 0시에 날 바뀜(기본) / 23시에 날 바뀜
  - 기준에 따라 기둥이 달라지면 경고합니다.

사용 예:
  python3 saju.py chart --date 1990-05-15 --time 14:30 --gender f
  python3 saju.py chart --date 1990-04-21 --lunar --time 14:30 --gender m --place 부산 --basis lmt
  python3 saju.py compat --a "1990-05-15 14:30 f" --b "1988-11-02 09:10 m"
  python3 saju.py today
  python3 saju.py terms --year 2026
"""
import argparse
import json
import re
import math
import os
import sys
from datetime import date, datetime, timedelta, timezone

__version__ = "1.1.0"

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(os.path.dirname(HERE), "data")

# ------------------------------------------------------------------ 기본 표
GAN = "甲乙丙丁戊己庚辛壬癸"
GAN_KO = "갑을병정무기경신임계"
ZHI = "子丑寅卯辰巳午未申酉戌亥"
ZHI_KO = "자축인묘진사오미신유술해"
GAN_EN = ["Jia", "Yi", "Bing", "Ding", "Wu", "Ji", "Geng", "Xin", "Ren", "Gui"]
ZHI_EN = ["Zi", "Chou", "Yin", "Mao", "Chen", "Si", "Wu", "Wei", "Shen", "You", "Xu", "Hai"]
ZHI_ANIMAL_KO = ["쥐", "소", "호랑이", "토끼", "용", "뱀", "말", "양", "원숭이", "닭", "개", "돼지"]
ZHI_ANIMAL_EN = ["Rat", "Ox", "Tiger", "Rabbit", "Dragon", "Snake", "Horse", "Goat", "Monkey", "Rooster", "Dog", "Pig"]

WX = "木火土金水"                      # 오행 순서(상생 순서)
WX_KO = "목화토금수"
WX_EN = ["Wood", "Fire", "Earth", "Metal", "Water"]
GAN_WX = [0, 0, 1, 1, 2, 2, 3, 3, 4, 4]
ZHI_WX = [4, 2, 0, 0, 2, 1, 1, 2, 3, 3, 2, 4]
# 지장간(여기·중기·정기 순, 마지막이 정기)
HIDDEN = {
    0: [8, 9], 1: [9, 7, 5], 2: [4, 2, 0], 3: [0, 1], 4: [1, 9, 4], 5: [4, 6, 2],
    6: [2, 5, 3], 7: [3, 1, 5], 8: [4, 8, 6], 9: [6, 7], 10: [7, 3, 4], 11: [4, 0, 8],
}

TEN_KO = ["비견", "겁재", "식신", "상관", "편재", "정재", "편관", "정관", "편인", "정인"]
TEN_HANJA = ["比肩", "劫財", "食神", "傷官", "偏財", "正財", "偏官", "正官", "偏印", "正印"]
TEN_EN = ["Friend", "Rob Wealth", "Eating God", "Hurting Officer", "Indirect Wealth", "Direct Wealth",
          "Seven Killings", "Direct Officer", "Indirect Resource", "Direct Resource"]

STAGE_KO = ["장생", "목욕", "관대", "건록", "제왕", "쇠", "병", "사", "묘", "절", "태", "양"]
STAGE_EN = ["Birth", "Bath", "Crown", "Office", "Peak", "Decline", "Sickness", "Death", "Tomb", "Extinction", "Conceive", "Nurture"]
STAGE_START = {0: 11, 1: 6, 2: 2, 3: 9, 4: 2, 5: 9, 6: 5, 7: 0, 8: 8, 9: 3}  # 12운성 장생 자리

# 12절(달이 바뀌는 절기): 절기표 안에서의 번호 → 달의 지지
TERM_NAMES_KO = ["소한", "대한", "입춘", "우수", "경칩", "춘분", "청명", "곡우", "입하", "소만", "망종", "하지",
                 "소서", "대서", "입추", "처서", "백로", "추분", "한로", "상강", "입동", "소설", "대설", "동지"]
TERM_NAMES_HANJA = ["小寒", "大寒", "立春", "雨水", "驚蟄", "春分", "淸明", "穀雨", "立夏", "小滿", "芒種", "夏至",
                    "小暑", "大暑", "立秋", "處暑", "白露", "秋分", "寒露", "霜降", "立冬", "小雪", "大雪", "冬至"]
TERM_NAMES_EN = ["Minor Cold", "Major Cold", "Start of Spring", "Rain Water", "Awakening of Insects", "Spring Equinox",
                 "Clear and Bright", "Grain Rain", "Start of Summer", "Grain Buds", "Grain in Ear", "Summer Solstice",
                 "Minor Heat", "Major Heat", "Start of Autumn", "End of Heat", "White Dew", "Autumn Equinox",
                 "Cold Dew", "Frost's Descent", "Start of Winter", "Minor Snow", "Major Snow", "Winter Solstice"]
JIE_INDEX = [0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22]   # 소한, 입춘, 경칩 … 대설
JIE_MONTH_ZHI = {0: 1, 2: 2, 4: 3, 6: 4, 8: 5, 10: 6, 12: 7, 14: 8, 16: 9, 18: 10, 20: 11, 22: 0}

PLACES = {  # 이름: 경도(동경 +)
    "서울": 126.98, "seoul": 126.98, "인천": 126.71, "incheon": 126.71, "수원": 127.03, "suwon": 127.03,
    "성남": 127.13, "용인": 127.18, "고양": 126.83, "안산": 126.83, "안양": 126.93, "평택": 127.11, "안성": 127.28,
    "의정부": 127.04, "파주": 126.78, "김포": 126.72, "화성": 126.83, "부천": 126.78,
    "춘천": 127.73, "chuncheon": 127.73, "원주": 127.95, "강릉": 128.90, "gangneung": 128.90, "속초": 128.59,
    "대전": 127.38, "daejeon": 127.38, "세종": 127.29, "sejong": 127.29, "청주": 127.49, "cheongju": 127.49,
    "천안": 127.15, "cheonan": 127.15, "충주": 127.93,
    "전주": 127.15, "jeonju": 127.15, "광주": 126.85, "gwangju": 126.85, "목포": 126.39, "여수": 127.66, "순천": 127.49,
    "대구": 128.60, "daegu": 128.60, "포항": 129.37, "pohang": 129.37, "경주": 129.22, "안동": 128.73, "구미": 128.34,
    "부산": 129.08, "busan": 129.08, "울산": 129.31, "ulsan": 129.31, "창원": 128.68, "changwon": 128.68,
    "진주": 128.11, "김해": 128.88, "제주": 126.53, "jeju": 126.53, "서귀포": 126.56,
    "평양": 125.75, "pyongyang": 125.75,
    "도쿄": 139.69, "tokyo": 139.69, "오사카": 135.50, "osaka": 135.50, "베이징": 116.40, "beijing": 116.40,
    "상하이": 121.47, "shanghai": 121.47, "타이베이": 121.56, "taipei": 121.56, "홍콩": 114.17, "hong kong": 114.17,
    "싱가포르": 103.82, "singapore": 103.82, "뉴욕": -74.01, "new york": -74.01, "la": -118.24,
    "로스앤젤레스": -118.24, "los angeles": -118.24, "시카고": -87.63, "chicago": -87.63, "토론토": -79.38,
    "toronto": -79.38, "밴쿠버": -123.12, "vancouver": -123.12, "런던": -0.13, "london": -0.13, "파리": 2.35,
    "paris": 2.35, "베를린": 13.40, "berlin": 13.40, "시드니": 151.21, "sydney": 151.21, "멜버른": 144.96,
    "melbourne": 144.96, "오클랜드": 174.76, "auckland": 174.76, "호치민": 106.70, "ho chi minh": 106.70,
    "방콕": 100.50, "bangkok": 100.50, "마닐라": 120.98, "manila": 120.98,
}

# 한국 표준시·서머타임 바뀐 때(UTC 시각, 그때부터의 UTC 차이(시간), 서머타임 여부). tz 데이터베이스 Asia/Seoul과 같음.
KOREA_TZ = [
    (datetime(1800, 1, 1), 8 + 27 / 60 + 52 / 3600, False),
    (datetime(1908, 3, 31, 15, 32, 8), 8.5, False),
    (datetime(1911, 12, 31, 15, 30), 9.0, False),
    (datetime(1948, 5, 31, 15, 0), 10.0, True), (datetime(1948, 9, 12, 14, 0), 9.0, False),
    (datetime(1949, 4, 2, 15, 0), 10.0, True), (datetime(1949, 9, 10, 14, 0), 9.0, False),
    (datetime(1950, 3, 31, 15, 0), 10.0, True), (datetime(1950, 9, 9, 14, 0), 9.0, False),
    (datetime(1951, 5, 5, 15, 0), 10.0, True), (datetime(1951, 9, 8, 14, 0), 9.0, False),
    (datetime(1954, 3, 20, 15, 0), 8.5, False),
    (datetime(1955, 5, 4, 15, 30), 9.5, True), (datetime(1955, 9, 8, 14, 30), 8.5, False),
    (datetime(1956, 5, 19, 15, 30), 9.5, True), (datetime(1956, 9, 29, 14, 30), 8.5, False),
    (datetime(1957, 5, 4, 15, 30), 9.5, True), (datetime(1957, 9, 21, 14, 30), 8.5, False),
    (datetime(1958, 5, 3, 15, 30), 9.5, True), (datetime(1958, 9, 20, 14, 30), 8.5, False),
    (datetime(1959, 5, 2, 15, 30), 9.5, True), (datetime(1959, 9, 19, 14, 30), 8.5, False),
    (datetime(1960, 4, 30, 15, 30), 9.5, True), (datetime(1960, 9, 17, 14, 30), 8.5, False),
    (datetime(1961, 8, 9, 15, 30), 9.0, False),
    (datetime(1987, 5, 9, 17, 0), 10.0, True), (datetime(1987, 10, 10, 17, 0), 9.0, False),
    (datetime(1988, 5, 7, 17, 0), 10.0, True), (datetime(1988, 10, 8, 17, 0), 9.0, False),
]

_TERMS = None
_LUNAR = None


def _load_terms():
    global _TERMS
    if _TERMS is None:
        raw = json.load(open(os.path.join(DATA, "terms.json"), encoding="utf-8"))
        _TERMS = {}
        for y, v in raw.items():
            acc, row = 0, []
            for i, x in enumerate(v):
                acc = x if i == 0 else acc + x
                row.append(datetime(1970, 1, 1) + timedelta(seconds=acc))
            _TERMS[int(y)] = row
    return _TERMS


def kst_str(utc):
    """UTC → 그때 한국 벽시계 시각 글자(분 단위 반올림). 1954~1961 UTC+8:30, 서머타임도 그대로."""
    off, _ = korea_offset_at_utc(utc)
    return (utc + timedelta(hours=off, seconds=30)).strftime("%Y-%m-%d %H:%M")


def term_time(year, idx):
    """year년의 idx번째 절기(0=소한 … 23=동지) 시각, UTC(naive)."""
    t = _load_terms()
    if year not in t:
        raise SajuError(f"절기 표는 1899~2101년만 있어요 ({year}년)")
    return t[year][idx]


class SajuError(Exception):
    pass


# ------------------------------------------------------------------ 시간대
def korea_offset_at_utc(utc):
    off, dst = KOREA_TZ[0][1], False
    for t, o, d in KOREA_TZ:
        if utc >= t:
            off, dst = o, d
        else:
            break
    return off, dst


def korea_local_to_utc(local):
    """한국 벽시계 시각 → (UTC, 그때 UTC 차이, 서머타임 여부, 메모). 모호하거나 없는 시각도 처리."""
    cands = []
    for _, o, d in KOREA_TZ:
        u = local - timedelta(hours=o)
        o2, d2 = korea_offset_at_utc(u)
        if abs(o2 - o) < 1e-9 and (u, o2, d2) not in cands:
            cands.append((u, o2, d2))
    note = None
    if not cands:  # 시계가 앞으로 당겨지며 건너뛴 시각: 바뀌기 전 기준으로 본다(zoneinfo fold=0과 같음)
        for i in range(1, len(KOREA_TZ)):
            t, o_new, d_new = KOREA_TZ[i]
            o_old, d_old = KOREA_TZ[i - 1][1], KOREA_TZ[i - 1][2]
            lo, hi = t + timedelta(hours=o_old), t + timedelta(hours=o_new)
            if lo <= local < hi:
                return local - timedelta(hours=o_old), o_old, d_old, ("gap", d_new, o_new - o_old)
        raise SajuError("시각을 시간대에 맞추지 못했어요")
    if len(cands) > 1:
        cands.sort(key=lambda c: (c[2], c[0]))  # 서머타임 아닌 쪽, 같으면 먼저 지나간 쪽
        note = ("ambiguous", any(c[2] for c in cands), abs(cands[0][1] - cands[1][1]))
    u, o, d = cands[0]
    return u, o, d, note


def parse_tz(s):
    """'+09:00', '-5', '5.5', 'UTC+8' 또는 IANA 이름(가능할 때)."""
    if s is None:
        return None
    s0 = s.strip()
    t = s0.upper().replace("UTC", "").replace("GMT", "").strip()
    try:
        if ":" in t:
            sign = -1 if t.startswith("-") else 1
            h, m = t.lstrip("+-").split(":")
            v = sign * (int(h) + int(m) / 60)
        else:
            v = float(t)
        if not -14 <= v <= 14:
            raise SajuError(f"시간대가 범위(-14~+14)를 벗어났어요: {s0}")
        return ("fixed", v)
    except ValueError:
        pass
    try:
        from zoneinfo import ZoneInfo
        return ("iana", ZoneInfo(s0))
    except Exception:
        raise SajuError(f"시간대를 모르겠어요: {s0} (예: +09:00, -5, America/New_York)")


# ------------------------------------------------------------------ 균시차(진태양시)
def equation_of_time_minutes(utc):
    """균시차(분). NOAA 근사식(오차 약 30초)."""
    doy = utc.timetuple().tm_yday
    g = 2 * math.pi / 365 * (doy - 1 + (utc.hour - 12) / 24)
    return 229.18 * (0.000075 + 0.001868 * math.cos(g) - 0.032077 * math.sin(g)
                     - 0.014615 * math.cos(2 * g) - 0.040849 * math.sin(2 * g))


# ------------------------------------------------------------------ 음력
def _load_lunar():
    global _LUNAR
    if _LUNAR is None:
        _LUNAR = {int(k): v for k, v in json.load(open(os.path.join(DATA, "lunar_ko.json"), encoding="utf-8")).items()}
    return _LUNAR


def lunar_to_solar(y, m, d, leap=False):
    tab = _load_lunar()
    if y not in tab:
        raise SajuError(f"음력 표는 1900~2049년만 있어요 ({y}년)")
    start, leapm, bits = tab[y]
    if leap and leapm != m:
        raise SajuError(f"음력 {y}년에는 윤{m}월이 없어요" + (f" (그해 윤달은 윤{leapm}월)" if leapm else " (그해는 윤달 없음)"))
    order = []
    for mm in range(1, 13):
        order.append((mm, False))
        if mm == leapm:
            order.append((mm, True))
    off = 0
    for i, (mm, lp) in enumerate(order):
        length = 30 if bits[i] == "1" else 29
        if mm == m and lp == bool(leap):
            if not 1 <= d <= length:
                raise SajuError(f"음력 {y}년 {'윤' if leap else ''}{m}월은 {length}일까지예요")
            return date.fromordinal(start + off + d - 1)
        off += length
    raise SajuError("음력 날짜를 찾지 못했어요")


def solar_to_lunar(dt):
    tab = _load_lunar()
    o = dt.toordinal()
    for y in sorted(tab):
        start, leapm, bits = tab[y]
        total = sum(30 if b == "1" else 29 for b in bits)
        if start <= o < start + total:
            off = o - start
            order = []
            for mm in range(1, 13):
                order.append((mm, False))
                if mm == leapm:
                    order.append((mm, True))
            for i, (mm, lp) in enumerate(order):
                length = 30 if bits[i] == "1" else 29
                if off < length:
                    return y, mm, off + 1, lp
                off -= length
    return None


# ------------------------------------------------------------------ 기둥 계산
def gz(i):
    return GAN[i % 10] + ZHI[i % 12]


def gz_ko(i):
    return GAN_KO[i % 10] + ZHI_KO[i % 12]


def gz_index(g, z):
    for i in range(60):
        if i % 10 == g and i % 12 == z:
            return i
    raise ValueError


def day_index(d):
    return (d.toordinal() + 14) % 60


def year_month_index(utc):
    """UTC 순간 → (해 간지 번호, 달 간지 번호, 직전 절(년,번호), 다음 절(년,번호))."""
    y = utc.year
    jies = []
    tt = _load_terms()
    if y not in tt or (y - 1 not in tt and y + 1 not in tt):
        raise SajuError(f"사주 계산은 1900~2100년만 돼요 ({y}년)")
    for yy in (y - 1, y, y + 1):
        if yy not in tt:
            continue
        for j in JIE_INDEX:
            jies.append((term_time(yy, j), yy, j))
    jies.sort()
    prev = nxt = None
    for t, yy, j in jies:
        if t <= utc:
            prev = (t, yy, j)
        elif nxt is None:
            nxt = (t, yy, j)
    if prev is None or nxt is None:
        raise SajuError("사주 계산은 1900~2100년만 돼요")
    _, py, pj = prev
    # 해: 입춘 기준
    sy = utc.year if utc >= term_time(utc.year, 2) else utc.year - 1
    yidx = (sy - 4) % 60
    mz = JIE_MONTH_ZHI[pj]
    # 달 천간: 오호둔(년간 → 인월 천간)
    yin_gan = {0: 2, 5: 2, 1: 4, 6: 4, 2: 6, 7: 6, 3: 8, 8: 8, 4: 0, 9: 0}[yidx % 10]
    mg = (yin_gan + (mz - 2) % 12) % 10
    midx = gz_index(mg, mz)
    return yidx, midx, prev, nxt


def hour_branch(h, m):
    t = h * 60 + m
    return ((t + 60) // 120) % 12


def ten_god(dm, other_gan):
    a, b = GAN_WX[dm], GAN_WX[other_gan]
    same = (dm % 2) == (other_gan % 2)
    rel = (b - a) % 5  # 0 같음, 1 내가 생함, 2 내가 극함, 3 나를 극함, 4 나를 생함
    base = {0: 0, 1: 2, 2: 4, 3: 6, 4: 8}[rel]
    return base + (0 if same else 1)


def stage(gan, zhi):
    s = STAGE_START[gan]
    if gan % 2 == 0:
        return (zhi - s) % 12
    return (s - zhi) % 12


# ------------------------------------------------------------------ 관계(합·충·형·해·파·원진)
GAN_HE = {frozenset((0, 5)): "土", frozenset((1, 6)): "金", frozenset((2, 7)): "水", frozenset((3, 8)): "木", frozenset((4, 9)): "火"}
GAN_CHONG = [frozenset(p) for p in ((0, 6), (1, 7), (2, 8), (3, 9))]
ZHI_LIUHE = {frozenset((0, 1)): "土", frozenset((2, 11)): "木", frozenset((3, 10)): "火", frozenset((4, 9)): "金",
             frozenset((5, 8)): "水", frozenset((6, 7)): "火"}
SANHE = [((8, 0, 4), "水"), ((11, 3, 7), "木"), ((2, 6, 10), "火"), ((5, 9, 1), "金")]
FANGHE = [((2, 3, 4), "木"), ((5, 6, 7), "火"), ((8, 9, 10), "金"), ((11, 0, 1), "水")]
ZHI_CHONG = [frozenset((i, (i + 6) % 12)) for i in range(6)]
ZHI_HAI = [frozenset(p) for p in ((0, 7), (1, 6), (2, 5), (3, 4), (8, 11), (9, 10))]
ZHI_PO = [frozenset(p) for p in ((0, 9), (1, 4), (2, 11), (3, 6), (5, 8), (7, 10))]
YUANJIN = [frozenset(p) for p in ((0, 7), (1, 6), (2, 9), (3, 8), (4, 11), (5, 10))]
XING3 = [((2, 5, 8), "무은지형(寅巳申)"), ((1, 10, 7), "지세지형(丑戌未)")]
XING_ZIMAO = frozenset((0, 3))
SELF_XING = {4, 6, 9, 11}

REL_EN = {"천간합": "stem combination", "천간충": "stem clash", "육합": "six harmony", "삼합": "three harmony",
          "반합": "half harmony", "방합": "directional harmony", "충": "clash", "형": "punishment",
          "해": "harm", "파": "break", "원진": "resentment", "자형": "self punishment"}


SHINSAL_EN = {"천을귀인": "Nobleman", "도화": "Peach Blossom", "역마": "Travelling Horse", "화개": "Canopy",
              "양인": "Yang Blade", "괴강": "Kui Gang", "공망": "Void"}

EN_TOKENS = [("년주", "Year"), ("월주", "Month"), ("일주", "Day"), ("시주", "Hour"), ("년", "y"),
             ("무은지형", "ungrateful punishment"), ("지세지형", "bullying punishment"), ("무례지형", "rude punishment"),
             ("방합", "directional harmony"), ("삼합", "three harmony"), ("반합", "half harmony"), ("자형", "self punishment"),
             ("원진", "resentment"), ("합", "combine"), ("충", "clash"), ("해", "harm"), ("파", "break")]


def en_text(t):
    for a, b in EN_TOKENS:
        t = t.replace(a, b)
    return re.sub(r"(?<![A-Za-z])([AB])(Year|Month|Day|Hour)", r"\1 \2", t)


def relations(pillars, labels):
    """pillars: [(gan, zhi)...], labels: 이름들 → 관계 목록."""
    out = []
    n = len(pillars)
    for i in range(n):
        for j in range(i + 1, n):
            gi, zi = pillars[i]
            gj, zj = pillars[j]
            pair = f"{labels[i]}–{labels[j]}"
            if gi is not None and gj is not None:
                k = frozenset((gi, gj))
                if k in GAN_HE:
                    out.append(("천간합", pair, f"{GAN[gi]}{GAN[gj]} 합 → {GAN_HE[k]}"))
                if k in GAN_CHONG:
                    out.append(("천간충", pair, f"{GAN[gi]}{GAN[gj]} 충"))
            if zi is None or zj is None:
                continue
            k = frozenset((zi, zj))
            if k in ZHI_LIUHE:
                out.append(("육합", pair, f"{ZHI[zi]}{ZHI[zj]} 합 → {ZHI_LIUHE[k]}"))
            if k in ZHI_CHONG:
                out.append(("충", pair, f"{ZHI[zi]}{ZHI[zj]} 충"))
            if k in ZHI_HAI:
                out.append(("해", pair, f"{ZHI[zi]}{ZHI[zj]} 해"))
            if k in ZHI_PO:
                out.append(("파", pair, f"{ZHI[zi]}{ZHI[zj]} 파"))
            if k in YUANJIN:
                out.append(("원진", pair, f"{ZHI[zi]}{ZHI[zj]} 원진"))
            if k == XING_ZIMAO:
                out.append(("형", pair, f"{ZHI[zi]}{ZHI[zj]} 무례지형(子卯)"))
            for grp, name in XING3:
                if zi in grp and zj in grp and zi != zj:
                    out.append(("형", pair, f"{ZHI[zi]}{ZHI[zj]} {name}"))
            if zi == zj and zi in SELF_XING:
                out.append(("자형", pair, f"{ZHI[zi]}{ZHI[zj]} 자형"))
            for grp, el in SANHE:
                if zi in grp and zj in grp and zi != zj and grp[1] in (zi, zj):
                    out.append(("반합", pair, f"{ZHI[zi]}{ZHI[zj]} 반합(→{el})"))
    zs = [p[1] for p in pillars if p[1] is not None]
    for grp, el in SANHE:
        if all(z in zs for z in grp):
            out.append(("삼합", "·".join(labels[k] for k, p in enumerate(pillars) if p[1] in grp), f"{''.join(ZHI[z] for z in grp)} 삼합 → {el}"))
    for grp, el in FANGHE:
        if all(z in zs for z in grp):
            out.append(("방합", "·".join(labels[k] for k, p in enumerate(pillars) if p[1] in grp), f"{''.join(ZHI[z] for z in grp)} 방합 → {el}"))
    return out


# ------------------------------------------------------------------ 신살
def shinsal(pillars, day_idx, year_idx):
    dg = pillars[2][0]
    yz, dz = pillars[0][1], pillars[2][1]
    names = ["년", "월", "일", "시"]
    found = []
    gui = {0: (1, 7), 4: (1, 7), 6: (1, 7), 1: (0, 8), 5: (0, 8), 2: (11, 9), 3: (11, 9), 7: (2, 6), 8: (5, 3), 9: (5, 3)}[dg]
    for k, (g, z) in enumerate(pillars):
        if z is not None and z in gui:
            found.append(("천을귀인", names[k], ZHI[z]))

    def grp(z):
        for g3, _ in SANHE:
            if z in g3:
                return g3
    tables = {"도화": {8: 9, 2: 3, 5: 6, 11: 0}, "역마": {8: 2, 2: 8, 5: 11, 11: 5}, "화개": {8: 4, 2: 10, 5: 1, 11: 7}}
    for base_name, bz in (("년지", yz), ("일지", dz)):
        g3 = grp(bz)
        for nm, tb in tables.items():
            target = tb[g3[0]]
            for k, (g, z) in enumerate(pillars):
                if z == target and not (base_name == "년지" and k == 0) and not (base_name == "일지" and k == 2):
                    found.append((nm, names[k], f"{ZHI[z]} ({base_name} 기준)"))
    yangren = {0: 3, 2: 6, 4: 6, 6: 9, 8: 0}
    if dg in yangren:
        for k, (g, z) in enumerate(pillars):
            if z == yangren[dg]:
                found.append(("양인", names[k], ZHI[z]))
    if day_idx in (gz_index(6, 4), gz_index(6, 10), gz_index(8, 4), gz_index(8, 10), gz_index(4, 10)):
        found.append(("괴강", "일", gz(day_idx)))
    b = (day_idx - day_idx % 10) % 12
    kong = ((b + 10) % 12, (b + 11) % 12)
    for k, (g, z) in enumerate(pillars):
        if k != 2 and z in kong:
            found.append(("공망", names[k], ZHI[z]))
    seen, uniq = set(), []
    for f in found:
        if f not in seen:
            seen.add(f)
            uniq.append(f)
    return uniq, kong


# ------------------------------------------------------------------ 입력 → 순간·현지 시각
def resolve_input(date_str, time_str=None, lunar=False, leap=False, tz=None, place=None, lon=None,
                  basis="clock", zi="midnight"):
    try:
        y, m, d = [int(x) for x in date_str.replace("/", "-").replace(".", "-").split("-")]
    except Exception:
        raise SajuError(f"날짜 모양이 이상해요: {date_str} (예: 1990-05-15)")
    notes = []
    if leap and not lunar:
        raise SajuError("윤달(--leap)은 음력(--lunar)과 같이 써야 해요")
    if lunar:
        sd = lunar_to_solar(y, m, d, leap)
        notes.append(("lunar", f"음력 {y}년 {'윤' if leap else ''}{m}월 {d}일 = 양력 {sd.isoformat()}",
                      f"Lunar {y}-{'leap ' if leap else ''}{m}-{d} = solar {sd.isoformat()}"))
    else:
        try:
            sd = date(y, m, d)
        except ValueError:
            raise SajuError(f"없는 날짜예요: {date_str}")
    time_known = time_str not in (None, "", "unknown", "모름", "?")
    if time_known:
        try:
            ts = time_str.strip().replace("시", ":").replace("분", "")
            if ts.endswith(":"):
                ts += "0"
            hh, mm = [int(x) for x in ts.split(":")[:2]]
        except Exception:
            raise SajuError(f"시각 모양이 이상해요: {time_str} (예: 14:30)")
        if not (0 <= hh <= 23 and 0 <= mm <= 59):
            raise SajuError(f"시각이 범위를 벗어났어요: {time_str}")
    else:
        hh, mm = 12, 0
    wall = datetime(sd.year, sd.month, sd.day, hh, mm)

    tzinfo = parse_tz(tz) if tz else None
    if tzinfo is None:
        utc, off, dst, note = korea_local_to_utc(wall)
        tzname = "Asia/Seoul"
        if note and note[0] == "gap":
            what = "서머타임이 시작되며" if note[1] else "표준시가 바뀌며"
            mins = round(note[2] * 60)
            notes.append(("gap", f"{what} 시계가 {mins}분 앞으로 당겨져서 실제로는 없던 시각이에요. 바뀌기 전 시계로 봤어요. 바뀐 뒤 시계였다면 실제로는 {mins}분 이른 시각이에요",
                          f"This clock time did not exist (clocks jumped {mins} min forward). Read with the earlier offset; otherwise the real time is {mins} min earlier"))
        if note and note[0] == "ambiguous":
            what = "서머타임이 끝나며" if note[1] else "표준시가 바뀌며"
            mins = round(note[2] * 60)
            notes.append(("ambiguous", f"{what} 같은 시각이 두 번 지나갔어요. {'표준시' if note[1] else '먼저 지나간'} 쪽으로 봤어요. 다른 쪽이면 실제 시각이 {mins}분 달라요",
                          f"This clock time occurred twice; read as {'standard time' if note[1] else 'the first occurrence'}. The other reading differs by {mins} min"))
        std_off = off - (1 if dst else 0)
    elif tzinfo[0] == "fixed":
        off = tzinfo[1]
        dst = False
        utc = wall - timedelta(hours=off)
        tzname = f"UTC{off:+g}"
        std_off = off
    else:
        z = tzinfo[1]
        a0, a1 = wall.replace(tzinfo=z, fold=0), wall.replace(tzinfo=z, fold=1)
        aware = a0
        if a0.utcoffset() != a1.utcoffset():
            back = a0.astimezone(timezone.utc).astimezone(z).replace(tzinfo=None)
            mins = round(abs((a0.utcoffset() - a1.utcoffset()).total_seconds()) / 60)
            if back != wall:  # 건너뛴 시각
                notes.append(("gap", f"서머타임이 시작되며 시계가 {mins}분 앞으로 당겨져서 실제로는 없던 시각이에요. 바뀌기 전 시계로 봤어요",
                              f"This clock time did not exist (clocks jumped {mins} min forward); read with the earlier offset"))
            else:  # 두 번 지나간 시각: 서머타임 아닌 쪽
                if a0.dst() and a0.dst().total_seconds() and not (a1.dst() and a1.dst().total_seconds()):
                    aware = a1
                notes.append(("ambiguous", f"서머타임이 끝나며 같은 시각이 두 번 지나갔어요. 표준시 쪽으로 봤어요. 다른 쪽이면 실제 시각이 {mins}분 달라요",
                              f"This clock time occurred twice; read as standard time. The other reading differs by {mins} min"))
        utc = aware.astimezone(timezone.utc).replace(tzinfo=None)
        off = aware.utcoffset().total_seconds() / 3600
        dstd = aware.dst()
        dst = bool(dstd and dstd.total_seconds())
        std_off = off - (dstd.total_seconds() / 3600 if dst else 0)
        tzname = str(z)
    if dst:
        dsth = off - std_off
        notes.append(("dst", f"서머타임 기간이라 {round(dsth * 60)}분을 빼서 계산했어요 (시계 {wall:%H:%M} → 표준시 {(wall - timedelta(hours=dsth)):%H:%M})",
                      f"Daylight saving time: subtracted {round(dsth * 60)} min (clock {wall:%H:%M} → standard {(wall - timedelta(hours=dsth)):%H:%M})"))

    if lon is None and place:
        key = place.strip().lower().replace("_", " ")
        if key not in PLACES:
            key = " ".join(key.split())
        if key not in PLACES and key.replace(" ", "") in {k.replace(" ", ""): k for k in PLACES}:
            key = {k.replace(" ", ""): k for k in PLACES}[key.replace(" ", "")]
        if key not in PLACES:
            raise SajuError(f"모르는 곳이에요: {place}. --lon 으로 경도를 직접 넣어 주세요 (예: --lon 127.0)")
        lon = PLACES[key]
    if lon is None:
        lon = 126.98 if tzinfo is None else std_off * 15
        lon_src = "기본값(서울)" if tzinfo is None else "시간대 중앙 경도"
    else:
        lon_src = place or "입력"

    # 사주용 현지 시각(기준별)
    std_local = utc + timedelta(hours=std_off)          # 서머타임 뺀 표준시
    lmt = utc + timedelta(hours=lon / 15)               # 지방 평균시(경도 보정)
    tst = lmt + timedelta(minutes=equation_of_time_minutes(utc))  # 진태양시
    bases = {"clock": std_local, "lmt": lmt, "true": tst}
    if basis not in bases:
        raise SajuError("basis는 clock / lmt / true 중 하나예요")
    return dict(utc=utc, wall=wall, solar_date=sd, time_known=time_known, tzname=tzname, utc_offset=off,
                std_offset=std_off, dst=dst, lon=lon, lon_src=lon_src, bases=bases, basis=basis, zi=zi, notes=notes)


def pillars_for(local, utc, zi="midnight", time_known=True):
    yidx, midx, prev, nxt = year_month_index(utc)
    dd = local.date()
    if zi == "23" and local.hour == 23:
        dd = dd + timedelta(days=1)
    didx = day_index(dd)
    hidx = None
    if time_known:
        hz = hour_branch(local.hour, local.minute)
        # 시 천간: 오서둔. 23시대 자시는 다음날 일간으로 잇는다(연속된 60갑자).
        base_day = didx
        if local.hour == 23 and zi == "midnight":
            base_day = (didx + 1) % 60
        zi_gan = {0: 0, 5: 0, 1: 2, 6: 2, 2: 4, 7: 4, 3: 6, 8: 6, 4: 8, 9: 8}[base_day % 10]
        hidx = gz_index((zi_gan + hz) % 10, hz)
    return yidx, midx, didx, hidx, prev, nxt


# ------------------------------------------------------------------ 대운·세운
def daewoon(info, yidx, midx, gender, count=10):
    if gender not in ("m", "f"):
        return None
    yang_year = (yidx % 10) % 2 == 0
    forward = (yang_year and gender == "m") or ((not yang_year) and gender == "f")
    utc = info["utc"]
    _, _, prev, nxt = year_month_index(utc)
    target = nxt[0] if forward else prev[0]
    days = abs((target - utc).total_seconds()) / 86400
    years_exact = days / 3
    num = max(1, int(years_exact + 0.5))
    start_date = utc + timedelta(days=years_exact * 365.2422)
    birth_year = info["solar_date"].year
    rows = []
    for k in range(1, count + 1):
        idx = (midx + (k if forward else -k)) % 60
        age = num + (k - 1) * 10
        rows.append(dict(index=idx, ganzhi=gz(idx), ko=gz_ko(idx), age=age, year=birth_year + age))
    return dict(forward=forward, days_to_term=round(days, 3), start_exact_years=round(years_exact, 2),
                start_age=num, start_date=start_date.date().isoformat(), pillars=rows)


def year_pillar_of(year):
    return (year - 4) % 60


# ------------------------------------------------------------------ 차트 만들기
def build_chart(info, gender=None, years=None):
    local = info["bases"][info["basis"]]
    yidx, midx, didx, hidx, prev, nxt = pillars_for(local, info["utc"], info["zi"], info["time_known"])
    P = [(yidx % 10, yidx % 12), (midx % 10, midx % 12), (didx % 10, didx % 12),
         (hidx % 10, hidx % 12) if hidx is not None else (None, None)]
    dm = didx % 10
    labels = ["년주", "월주", "일주", "시주"]
    pillars = []
    for k, (g, z) in enumerate(P):
        if g is None:
            pillars.append(None)
            continue
        idx = [yidx, midx, didx, hidx][k]
        hid = HIDDEN[z]
        pillars.append(dict(
            label=labels[k], ganzhi=gz(idx), ko=gz_ko(idx), index=idx,
            gan=dict(hanja=GAN[g], ko=GAN_KO[g], en=GAN_EN[g], element=WX[GAN_WX[g]], yinyang="양" if g % 2 == 0 else "음",
                     ten_god=None if k == 2 else TEN_KO[ten_god(dm, g)]),
            zhi=dict(hanja=ZHI[z], ko=ZHI_KO[z], en=ZHI_EN[z], animal=ZHI_ANIMAL_KO[z], element=WX[ZHI_WX[z]],
                     ten_god=TEN_KO[ten_god(dm, hid[-1])], hidden=[dict(hanja=GAN[h], ko=GAN_KO[h], ten_god=TEN_KO[ten_god(dm, h)]) for h in hid],
                     stage=STAGE_KO[stage(dm, z)])))
    # 오행 세기(여덟 글자)
    cnt = [0] * 5
    for g, z in P:
        if g is not None:
            cnt[GAN_WX[g]] += 1
            cnt[ZHI_WX[z]] += 1
    # 지장간까지 넣은 세기(정기 1, 중기 0.5, 여기 0.3 — 참고용)
    w = [0.0] * 5
    for g, z in P:
        if g is None:
            continue
        w[GAN_WX[g]] += 1
        hid = HIDDEN[z]
        ws = [0.3, 0.5, 1.0][-len(hid):] if len(hid) == 3 else [0.3, 1.0]
        for h, ww in zip(hid, ws):
            w[GAN_WX[h]] += ww
    rel = relations([p for p in P if p[0] is not None], [labels[k] for k, p in enumerate(P) if p[0] is not None])
    ss, kong = shinsal([p if p[0] is not None else (None, None) for p in P], didx, yidx)
    ten_count = {}
    for k, (g, z) in enumerate(P):
        if g is None:
            continue
        if k != 2:
            t = TEN_KO[ten_god(dm, g)]
            ten_count[t] = ten_count.get(t, 0) + 1
        t = TEN_KO[ten_god(dm, HIDDEN[z][-1])]
        ten_count[t] = ten_count.get(t, 0) + 1

    # 기준에 따라 달라지는지
    variants = []
    if info["time_known"]:
        for b in ("clock", "lmt", "true"):
            for z_ in ("midnight", "23"):
                loc = info["bases"][b]
                v = pillars_for(loc, info["utc"], z_, True)
                variants.append(dict(basis=b, zi=z_, local=loc.strftime("%Y-%m-%d %H:%M"), day=gz(v[2]), hour=gz(v[3])))
    me = (gz(didx), gz(hidx) if hidx is not None else None)
    differs = sorted({(v["day"], v["hour"]) for v in variants} - {me}) if variants else []
    warnings = []
    term_margin_min = min(abs((info["utc"] - prev[0]).total_seconds()), abs((nxt[0] - info["utc"]).total_seconds())) / 60
    if term_margin_min < 120:
        near = prev if abs((info["utc"] - prev[0]).total_seconds()) < abs((nxt[0] - info["utc"]).total_seconds()) else nxt
        warnings.append(dict(kind="term_boundary", minutes=round(term_margin_min, 1), term=TERM_NAMES_KO[near[2]],
                             term_time_kst=kst_str(near[0])))
    if not info["time_known"]:
        warnings.append(dict(kind="time_unknown"))
        if term_margin_min < 12 * 60:
            near = prev if abs((info["utc"] - prev[0]).total_seconds()) < abs((nxt[0] - info["utc"]).total_seconds()) else nxt
            warnings.append(dict(kind="term_same_day", term=TERM_NAMES_KO[near[2]],
                                 term_time_kst=kst_str(near[0])))
    if differs:
        warnings.append(dict(kind="basis_dependent", alternatives=[dict(day=a, hour=b) for a, b in differs]))
    if info["time_known"]:
        hm = local.hour * 60 + local.minute
        edge = min(abs(((hm - 60) % 120)), 120 - ((hm - 60) % 120))
        if edge <= 10:
            warnings.append(dict(kind="hour_boundary", minutes=edge))

    natal_groups = {r[2] for r in rel if r[0] in ("삼합", "방합")}
    year_now = years[0] if years else datetime.now().year
    seun = []
    for yy in (years or range(year_now, year_now + 10)):
        i = year_pillar_of(yy)
        seun.append(dict(year=yy, ganzhi=gz(i), ko=gz_ko(i), gan_ten=TEN_KO[ten_god(dm, i % 10)],
                         zhi_ten=TEN_KO[ten_god(dm, HIDDEN[i % 12][-1])], animal=ZHI_ANIMAL_KO[i % 12],
                         relations=[r for r in relations(
                             [p for p in P if p[0] is not None] + [(i % 10, i % 12)],
                             [labels[k] for k, p in enumerate(P) if p[0] is not None] + [f"{yy}년"])
                             if f"{yy}년" in r[1] and not (r[0] in ("삼합", "방합") and r[2] in natal_groups)]))
    lun = solar_to_lunar(info["solar_date"])
    dw = daewoon(info, yidx, midx, gender) if gender else None
    return dict(
        version=__version__,
        input=dict(solar_date=info["solar_date"].isoformat(), wall_time=info["wall"].strftime("%H:%M") if info["time_known"] else None,
                   lunar=dict(year=lun[0], month=lun[1], day=lun[2], leap=lun[3]) if lun else None,
                   timezone=info["tzname"], utc=info["utc"].strftime("%Y-%m-%d %H:%M"), dst=info["dst"],
                   longitude=round(info["lon"], 2), longitude_source=info["lon_src"], basis=info["basis"], zi=info["zi"],
                   local_used=local.strftime("%Y-%m-%d %H:%M") if info["time_known"] else None, gender=gender),
        pillars=pillars,
        day_master=dict(hanja=GAN[dm], ko=GAN_KO[dm], element=WX[GAN_WX[dm]], element_ko=WX_KO[GAN_WX[dm]],
                        yinyang="양" if dm % 2 == 0 else "음"),
        elements={WX[i]: cnt[i] for i in range(5)},
        elements_weighted={WX[i]: round(w[i], 1) for i in range(5)},
        ten_gods_count=ten_count,
        relations=[dict(type=t, where=wh, what=wt) for t, wh, wt in rel],
        shinsal=[dict(name=n, where=wh, what=wt) for n, wh, wt in ss],
        kongmang=[ZHI[k] for k in kong],
        terms=dict(prev=dict(name=TERM_NAMES_KO[prev[2]], kst=kst_str(prev[0])),
                   next=dict(name=TERM_NAMES_KO[nxt[2]], kst=kst_str(nxt[0]))),
        daewoon=dw, seun=seun, variants=variants, warnings=warnings,
        notes=[n[1] for n in info["notes"]],
        notes_en=[n[2] for n in info["notes"]],
    )


# ------------------------------------------------------------------ 글로 보여 주기
def md_chart(c, lang="ko"):
    ko = lang == "ko"
    L = []
    inp = c["input"]
    if ko:
        L.append("## 사주팔자 (만세력 계산)")
        lun = inp["lunar"]
        ls = f" (음력 {lun['year']}년 {'윤' if lun['leap'] else ''}{lun['month']}월 {lun['day']}일)" if lun else ""
        L.append(f"- 양력 {inp['solar_date']}{ls}, " + (f"{inp['wall_time']} 출생" if inp["wall_time"] else "태어난 시각 모름"))
        basis_ko = {"clock": "시계 시각(표준시)", "lmt": "경도 보정(지방 평균시)", "true": "진태양시(경도+균시차)"}[inp["basis"]]
        zi_ko = {"midnight": "0시에 날 바뀜", "23": "23시에 날 바뀜(조자시 통일)"}[inp["zi"]]
        if inp["wall_time"]:
            L.append(f"- 시간 기준: {basis_ko} → 사주에 쓴 시각 {inp['local_used']} · 자시: {zi_ko} · 경도 {inp['longitude']}° ({inp['longitude_source']})")
        L.append(f"- 직전 절기 {c['terms']['prev']['name']} {c['terms']['prev']['kst']} / 다음 절기 {c['terms']['next']['name']} {c['terms']['next']['kst']} (그때 한국 시계 시각)")
    else:
        L.append("## Four Pillars (BaZi) chart")
        L.append(f"- Solar date {inp['solar_date']}, " + (f"born {inp['wall_time']}" if inp["wall_time"] else "birth time unknown"))
        if inp["wall_time"]:
            L.append(f"- Time basis: {inp['basis']} → time used {inp['local_used']} · day boundary: {inp['zi']} · longitude {inp['longitude']}°")
        L.append(f"- Previous solar term {c['terms']['prev']['kst']} / next {c['terms']['next']['kst']} (KST)")
    for n in (c["notes"] if ko else c.get("notes_en", c["notes"])):
        L.append(f"- ※ {n}")
    L.append("")
    cols = [p for p in reversed(c["pillars"])]
    head = ["시주", "일주", "월주", "년주"] if ko else ["Hour", "Day", "Month", "Year"]
    L.append("| | " + " | ".join(head) + " |")
    L.append("|---|" + "---|" * 4)

    def cell(p, f):
        return "—" if p is None else f(p)
    def tg(t):
        return t if ko else TEN_EN[TEN_KO.index(t)]

    def stg(t):
        return t if ko else STAGE_EN[STAGE_KO.index(t)]
    if ko:
        rows = [
            ("천간 십신", lambda p: "일간(나)" if p["label"] == "일주" else p["gan"]["ten_god"]),
            ("천간", lambda p: f"**{p['gan']['hanja']}** {p['gan']['ko']} ({p['gan']['element']}{WX_KO[WX.index(p['gan']['element'])]}·{p['gan']['yinyang']})"),
            ("지지", lambda p: f"**{p['zhi']['hanja']}** {p['zhi']['ko']} ({p['zhi']['element']}{WX_KO[WX.index(p['zhi']['element'])]})"),
            ("지지 십신", lambda p: p["zhi"]["ten_god"]),
            ("지장간", lambda p: " ".join(h["hanja"] + h["ko"] for h in p["zhi"]["hidden"])),
            ("12운성", lambda p: p["zhi"]["stage"]),
        ]
    else:
        rows = [
            ("Stem god", lambda p: "Day Master (you)" if p["label"] == "일주" else tg(p["gan"]["ten_god"])),
            ("Stem", lambda p: f"**{p['gan']['hanja']}** {p['gan']['en']} ({WX_EN[WX.index(p['gan']['element'])]}, {'Yang' if p['gan']['yinyang'] == '양' else 'Yin'})"),
            ("Branch", lambda p: f"**{p['zhi']['hanja']}** {p['zhi']['en']} ({WX_EN[WX.index(p['zhi']['element'])]}, {ZHI_ANIMAL_EN[ZHI.index(p['zhi']['hanja'])]})"),
            ("Branch god", lambda p: tg(p["zhi"]["ten_god"])),
            ("Hidden stems", lambda p: " ".join(h["hanja"] for h in p["zhi"]["hidden"])),
            ("12 stages", lambda p: stg(p["zhi"]["stage"])),
        ]
    for name, f in rows:
        L.append(f"| {name} | " + " | ".join(cell(p, f) for p in cols) + " |")
    L.append("")
    dm = c["day_master"]
    e = c["elements"]
    if ko:
        L.append(f"- 일간(나): **{dm['hanja']} {dm['ko']}** — {dm['element_ko']}({dm['element']}), {dm['yinyang']}")
        yz = c["pillars"][0]["zhi"]
        L.append(f"- 띠: {yz['animal']}띠 (년지 {yz['hanja']}, 입춘 기준)")
        L.append("- 오행 개수(여덟 글자): " + " · ".join(f"{WX_KO[i]}({WX[i]}) {e[WX[i]]}" for i in range(5)))
        L.append("- 지장간까지 넣은 세기(참고): " + " · ".join(f"{WX_KO[i]} {c['elements_weighted'][WX[i]]}" for i in range(5)))
        L.append("- 십신 개수: " + ", ".join(f"{k} {v}" for k, v in sorted(c["ten_gods_count"].items(), key=lambda x: -x[1])))
        if c["relations"]:
            L.append("- 원국 안의 합·충·형: " + "; ".join(f"{r['where']} {r['what']}" for r in c["relations"]))
        if c["shinsal"]:
            L.append("- 신살: " + ", ".join(f"{s['name']}({s['where']} {s['what']})" for s in c["shinsal"]))
        L.append(f"- 공망(일주 기준): {''.join(c['kongmang'])}")
    else:
        L.append(f"- Day Master: **{dm['hanja']}** {GAN_EN[GAN.index(dm['hanja'])]} — {WX_EN[WX.index(dm['element'])]}, {'Yang' if dm['yinyang'] == '양' else 'Yin'}")
        L.append(f"- Zodiac animal: {ZHI_ANIMAL_EN[ZHI.index(c['pillars'][0]['zhi']['hanja'])]} (year changes at Start of Spring, not Jan 1 or Lunar New Year)")
        L.append("- Element count: " + " · ".join(f"{WX_EN[i]} {e[WX[i]]}" for i in range(5)))
        L.append("- Ten gods: " + ", ".join(f"{tg(k)} {v}" for k, v in sorted(c["ten_gods_count"].items(), key=lambda x: -x[1])))
        if c["relations"]:
            L.append("- Relations in chart: " + "; ".join(en_text(f"{r['where']} {r['what']}") for r in c["relations"]))
        if c["shinsal"]:
            L.append("- Symbolic stars: " + ", ".join(f"{SHINSAL_EN.get(x['name'], x['name'])} ({en_text(x['where'] + '주')} {x['what'].split(' ')[0]})" for x in c["shinsal"]))
        L.append(f"- Void (空亡, from day pillar): {''.join(c['kongmang'])}")
    dw = c["daewoon"]
    if dw:
        L.append("")
        if ko:
            L.append(f"### 대운 ({'순행' if dw['forward'] else '역행'}, 대운수 {dw['start_age']} — 정확히는 만 {dw['start_exact_years']}세, {dw['start_date']} 무렵 시작)")
            L.append("| 시작 나이(만) | " + " | ".join(str(r["age"]) for r in dw["pillars"]) + " |")
        else:
            L.append(f"### Luck pillars ({'forward' if dw['forward'] else 'backward'}, start age {dw['start_age']}, exact {dw['start_exact_years']} y)")
            L.append("| Start age | " + " | ".join(str(r["age"]) for r in dw["pillars"]) + " |")
        L.append("|---|" + "---|" * len(dw["pillars"]))
        L.append("| " + ("대운" if ko else "Pillar") + " | " + " | ".join(f"{r['ganzhi']} {r['ko']}" if ko else r['ganzhi'] for r in dw["pillars"]) + " |")
        L.append("| " + ("해" if ko else "Year") + " | " + " | ".join(str(r["year"]) for r in dw["pillars"]) + " |")
    elif ko:
        L.append("")
        L.append("- 대운은 성별을 넣어야 계산돼요 (--gender m 또는 f)")
    L.append("")
    L.append("### " + ("세운(해마다)" if ko else "Annual pillars"))
    L.append("| " + ("해" if ko else "Year") + " | " + ("간지" if ko else "Pillar") + " | " + ("십신(천간/지지)" if ko else "Gods") + " | " + ("원국과의 관계" if ko else "Relations") + " |")
    L.append("|---|---|---|---|")
    for s in c["seun"]:
        rel = "; ".join(f"{r[1].split('–')[0]} {r[2]}" for r in s["relations"]) or "—"
        if not ko:
            rel = en_text(rel)
        if ko:
            L.append(f"| {s['year']} | {s['ganzhi']} {s['ko']}({s['animal']}) | {s['gan_ten']} / {s['zhi_ten']} | {rel} |")
        else:
            L.append(f"| {s['year']} | {s['ganzhi']} | {tg(s['gan_ten'])} / {tg(s['zhi_ten'])} | {rel} |")
    if c["warnings"]:
        L.append("")
        L.append("### " + ("확인할 점" if ko else "Warnings"))
        for w in c["warnings"]:
            L.append("- " + warn_text(w, ko))
    return "\n".join(L)


def warn_text(w, ko=True):
    k = w["kind"]
    if k == "term_boundary":
        return (f"⚠️ 절기가 바뀌는 때({w['term']}, {w['term_time_kst']})와 {w['minutes']}분 차이예요. 태어난 시각이 조금만 달라도 월주{'와 년주(띠)' if w['term'] == '입춘' else ''}가 바뀌어요. 출생 시각을 정확히 확인하세요"
                if ko else f"⚠️ Within {w['minutes']} min of a solar term ({w['term_time_kst']} KST); month (and maybe year) pillar depends on the exact birth time")
    if k == "time_unknown":
        return "태어난 시각을 몰라서 시주는 비웠어요. 대운 시작 나이는 정오 기준이라 조금 다를 수 있어요" if ko else "Birth time unknown: hour pillar omitted"
    if k == "term_same_day":
        yr = w.get("term") == "입춘"
        return (f"⚠️ 절기가 바뀌는 때({w.get('term')}, {w.get('term_time_kst')})와 태어난 날이 가까워서, 시각을 모르면 월주{'와 년주(띠)' if yr else ''}가 확실하지 않아요"
                if ko else f"⚠️ Solar term at {w.get('term_time_kst')} KST is close; month{' and year' if yr else ''} pillar uncertain without birth time")
    if k == "basis_dependent":
        alts = ", ".join(f"일주 {a['day']}·시주 {a['hour']}" if ko else f"day {a['day']} / hour {a['hour']}" for a in w["alternatives"])
        return (f"⚠️ 시간 기준(시계 시각/경도 보정/진태양시)이나 자시 처리를 다르게 하면 기둥이 달라져요 → {alts}. 만세력 앱마다 결과가 다를 수 있는 사주예요"
                if ko else f"⚠️ Other time-basis / day-boundary conventions give different pillars: {alts}")
    if k == "hour_boundary":
        return (f"시(時)가 바뀌는 경계와 {w['minutes']}분 차이예요. 출생 시각이 몇 분만 달라도 시주가 바뀔 수 있어요"
                if ko else f"Within {w['minutes']} min of an hour-branch boundary")
    return str(w)


# ------------------------------------------------------------------ 궁합
def parse_spec(s):
    """'1990-05-15 14:30 f', '1990-04-21 lunar leap m', '1990-05-15 unknown'"""
    parts = s.replace(",", " ").split()
    if not parts:
        raise SajuError("궁합 입력이 비었어요")
    spec = dict(date=parts[0], time=None, lunar=False, leap=False, gender=None, place=None)
    for p in parts[1:]:
        pl = p.lower()
        if ":" in p or re.fullmatch(r"\d{1,2}시(\d{1,2}분)?", p):
            spec["time"] = p
        elif pl in ("lunar", "음력"):
            spec["lunar"] = True
        elif pl in ("leap", "윤달", "윤"):
            spec["leap"] = True
        elif pl in ("m", "male", "남", "남자"):
            spec["gender"] = "m"
        elif pl in ("f", "female", "여", "여자"):
            spec["gender"] = "f"
        elif pl in ("unknown", "모름"):
            spec["time"] = None
        elif pl in PLACES:
            spec["place"] = p
        else:
            raise SajuError(f"궁합 입력에서 모르는 말: {p}")
    return spec


def compat(a, b, basis="clock", zi="midnight"):
    ca = build_chart(resolve_input(a["date"], a["time"], a["lunar"], a["leap"], place=a["place"], basis=basis, zi=zi), a["gender"])
    cb = build_chart(resolve_input(b["date"], b["time"], b["lunar"], b["leap"], place=b["place"], basis=basis, zi=zi), b["gender"])
    pa = [(p["index"] % 10, p["index"] % 12) for p in ca["pillars"] if p]
    pb = [(p["index"] % 10, p["index"] % 12) for p in cb["pillars"] if p]
    la = ["A" + p["label"] for p in ca["pillars"] if p]
    lb = ["B" + p["label"] for p in cb["pillars"] if p]
    own = {x["what"] for x in ca["relations"] + cb["relations"] if x["type"] in ("삼합", "방합")}
    rel = [r for r in relations(pa + pb, la + lb) if ("A" in r[1] and "B" in r[1]) and not (r[0] in ("삼합", "방합") and r[2] in own)]
    da, db = ca["pillars"][2]["index"] % 10, cb["pillars"][2]["index"] % 10
    ea, eb = ca["elements"], cb["elements"]
    lack_a = [k for k, v in ea.items() if v == 0]
    lack_b = [k for k, v in eb.items() if v == 0]
    fill = dict(a_fills_b=[k for k in lack_b if ea[k] >= 2], b_fills_a=[k for k in lack_a if eb[k] >= 2])
    good = sum(1 for r in rel if r[0] in ("천간합", "육합", "삼합", "반합", "방합"))
    bad = sum(1 for r in rel if r[0] in ("천간충", "충", "형", "해", "파", "원진", "자형"))
    day_rel = [r for r in rel if "–" in r[1] and r[1].split("–")[0] == "A일주" and r[1].split("–")[1] == "B일주"]
    return dict(a=ca, b=cb, relations=[dict(type=t, where=w, what=x) for t, w, x in rel],
                day_master=dict(a_to_b=TEN_KO[ten_god(da, db)], b_to_a=TEN_KO[ten_god(db, da)]),
                day_pillar_relations=[dict(type=t, where=w, what=x) for t, w, x in day_rel],
                element_fill=fill, harmony_count=good, conflict_count=bad)


def md_compat(r, lang="ko"):
    ko = lang == "ko"
    L = ["## 궁합 (두 사람 사주 비교)" if ko else "## Compatibility"]
    for tag, c in (("A", r["a"]), ("B", r["b"])):
        ps = " ".join(p["ganzhi"] if p else "□□" for p in c["pillars"])
        dm = c["day_master"]
        if ko:
            L.append(f"- {tag}: {c['input']['solar_date']} {c['input']['wall_time'] or '(시각 모름)'} → 년월일시 {ps}, 일간 {dm['hanja']}{dm['ko']}({dm['element_ko']}), "
                     + "오행 " + " ".join(f"{WX_KO[i]}{c['elements'][WX[i]]}" for i in range(5)))
        else:
            L.append(f"- {tag}: {c['input']['solar_date']} {c['input']['wall_time'] or '(time unknown)'} → Y/M/D/H {ps}, Day Master {dm['hanja']} ({WX_EN[WX.index(dm['element'])]}), "
                     + "elements " + " ".join(f"{WX_EN[i]} {c['elements'][WX[i]]}" for i in range(5)))
    dmr = r["day_master"]
    if ko:
        L.append(f"- 일간끼리: A가 보기에 B는 **{dmr['a_to_b']}**, B가 보기에 A는 **{dmr['b_to_a']}**")
        L.append("- 일주끼리(배우자 자리): " + ("; ".join(x["what"] for x in r["day_pillar_relations"]) or "특별한 합·충 없음"))
        L.append(f"- 서로 맺는 합 {r['harmony_count']}개, 부딪힘(충·형·해·파·원진) {r['conflict_count']}개")
    else:
        L.append(f"- Day Masters: to A, B is **{TEN_EN[TEN_KO.index(dmr['a_to_b'])]}**; to B, A is **{TEN_EN[TEN_KO.index(dmr['b_to_a'])]}**")
        L.append("- Day pillars (spouse palace): " + ("; ".join(en_text(x["what"]) for x in r["day_pillar_relations"]) or "no special combination or clash"))
        L.append(f"- Combinations between charts: {r['harmony_count']}, conflicts (clash/punishment/harm/break/resentment): {r['conflict_count']}")
    for x in r["relations"]:
        L.append(f"  - {x['where'] if ko else en_text(x['where'])}: {x['what'] if ko else en_text(x['what'])}")
    f = r["element_fill"]
    if f["a_fills_b"] or f["b_fills_a"]:
        if ko:
            L.append("- 오행 채워 주기: " + ", ".join([f"A가 B에게 없는 {WX_KO[WX.index(k)]}" for k in f["a_fills_b"]] + [f"B가 A에게 없는 {WX_KO[WX.index(k)]}" for k in f["b_fills_a"]]))
        else:
            L.append("- Filling missing elements: " + ", ".join([f"A gives B {WX_EN[WX.index(k)]}" for k in f["a_fills_b"]] + [f"B gives A {WX_EN[WX.index(k)]}" for k in f["b_fills_a"]]))
    for tag, c in (("A", r["a"]), ("B", r["b"])):
        for n in (c["notes"] if ko else c["notes_en"]):
            L.append(f"- {tag}: ※ {n}")
        for w in c["warnings"]:
            if w["kind"] in ("term_boundary", "basis_dependent", "term_same_day"):
                L.append(f"- {tag}: " + warn_text(w, ko))
    return "\n".join(L)


# ------------------------------------------------------------------ 띠별 운세
SAMJAE = {8: (2, 3, 4), 0: (2, 3, 4), 4: (2, 3, 4), 2: (8, 9, 10), 6: (8, 9, 10), 10: (8, 9, 10),
          5: (11, 0, 1), 9: (11, 0, 1), 1: (11, 0, 1), 11: (5, 6, 7), 3: (5, 6, 7), 7: (5, 6, 7)}
SAMJAE_KO = ["들삼재", "눌삼재", "날삼재"]
SAMJAE_EN = ["entering", "staying", "leaving"]


def ddi_year(target_year, lang="ko"):
    """target_year 해의 간지와 12띠 각각의 관계(충·합·형·해·파·원진·삼재·본명년)."""
    ti = year_pillar_of(target_year)
    tz = ti % 12
    rows = []
    for z in range(12):
        rel = []
        k = frozenset((z, tz))
        if z == tz:
            rel.append(("본명년", "내 띠의 해"))
        if k in ZHI_CHONG:
            rel.append(("충", "부딪힘·변화·이동"))
        if k in ZHI_LIUHE:
            rel.append(("육합", "도움·인연"))
        for grp, el in SANHE:
            if z in grp and tz in grp and z != tz:
                rel.append(("삼합", "같은 편·협력"))
        for grp, el in FANGHE:
            if z in grp and tz in grp and z != tz:
                rel.append(("방합", "같은 계절·뭉침"))
        if k == XING_ZIMAO:
            rel.append(("형", "긴장·조정"))
        for grp, name in XING3:
            if z in grp and tz in grp and z != tz:
                rel.append(("형", "긴장·조정"))
        if z == tz and z in SELF_XING:
            rel.append(("자형", "스스로 다그침"))
        if k in ZHI_HAI:
            rel.append(("해", "작은 어긋남"))
        if k in ZHI_PO:
            rel.append(("파", "계획 틀어짐"))
        if k in YUANJIN:
            rel.append(("원진", "미묘한 서운함"))
        sj = None
        if tz in SAMJAE[z]:
            sj = SAMJAE[z].index(tz)
        rows.append(dict(zhi=ZHI[z], ko=ZHI_KO[z], animal=ZHI_ANIMAL_KO[z], animal_en=ZHI_ANIMAL_EN[z],
                         relations=[dict(type=t, meaning=m) for t, m in rel],
                         samjae=SAMJAE_KO[sj] if sj is not None else None,
                         samjae_en=SAMJAE_EN[sj] if sj is not None else None))
    lichun = kst_str(term_time(target_year, 2)) if target_year in _load_terms() else None
    return dict(year=target_year, ganzhi=gz(ti), ko=gz_ko(ti), animal=ZHI_ANIMAL_KO[tz], animal_en=ZHI_ANIMAL_EN[tz],
                lichun_kst=lichun, rows=rows)


def ddi_of_birth(date_str, time_str=None, lunar=False, leap=False):
    """생일 → 띠(입춘 기준)와, 1월 1일·설날 기준이면 달라지는지."""
    info = resolve_input(date_str, time_str, lunar, leap)
    yidx, _, _, _ = year_month_index(info["utc"])
    z = yidx % 12
    sd = info["solar_date"]
    by_jan1 = (sd.year - 4) % 12
    lun = solar_to_lunar(sd)
    by_seollal = (lun[0] - 4) % 12 if lun else None
    return dict(zhi=ZHI[z], animal=ZHI_ANIMAL_KO[z], animal_en=ZHI_ANIMAL_EN[z], year_pillar=gz(yidx),
                by_jan1=ZHI_ANIMAL_KO[by_jan1], by_seollal=ZHI_ANIMAL_KO[by_seollal] if by_seollal is not None else None,
                time_known=info["time_known"], z=z,
                lichun_day=(not info["time_known"]) and kst_str(term_time(sd.year, 2))[:10] == sd.isoformat(),
                lichun_kst=kst_str(term_time(sd.year, 2)))


def md_ddi(r, mine=None, lang="ko"):
    ko = lang == "ko"
    L = []
    if mine:
        if ko:
            L.append(f"## 내 띠: {mine['animal']}띠 ({mine['zhi']}, 년주 {mine['year_pillar']}, 입춘 기준)")
            diff = []
            if mine["by_jan1"] != mine["animal"]:
                diff.append(f"1월 1일 기준이면 {mine['by_jan1']}띠")
            if mine["by_seollal"] and mine["by_seollal"] != mine["animal"]:
                diff.append(f"설날(음력 1월 1일) 기준이면 {mine['by_seollal']}띠")
            if diff:
                L.append(f"- ※ {', '.join(diff)}로 볼 수도 있어요. 사주와 운세에서는 **입춘 기준**이 맞아요.")
            if mine.get("lichun_day"):
                L.append(f"- ⚠️ 입춘 날({mine['lichun_kst']})에 태어나서, 태어난 시각에 따라 띠가 바뀌어요. 시각을 넣어 주세요(--time).")
        else:
            L.append(f"## Your zodiac animal: {mine['animal_en']} ({mine['zhi']}, year pillar {mine['year_pillar']}, from Start of Spring)")
        L.append("")
    if ko:
        L.append(f"## {r['year']}년 {r['ganzhi']}({r['ko']})년 — {r['animal']}의 해 띠별 운세")
        if r["lichun_kst"]:
            L.append(f"- 이 해는 입춘 {r['lichun_kst']}부터예요(1월 1일이나 설날이 아니에요).")
        L.append("")
        L.append("| 띠 | 올해와의 관계 | 삼재 |")
        L.append("|---|---|---|")
    else:
        L.append(f"## {r['year']} {r['ganzhi']} — year of the {r['animal_en']}: by zodiac animal")
        L.append("")
        L.append("| Animal | Relation to the year | Sam-jae (3 hard years) |")
        L.append("|---|---|---|")
    for row in r["rows"]:
        if mine and row["zhi"] != mine["zhi"]:
            continue
        rel = ", ".join(f"{x['type']}({x['meaning']})" for x in row["relations"]) if ko else \
            ", ".join(en_text(x['type']).replace("본명년", "own-sign year").replace("방합", "directional harmony") for x in row["relations"])
        if ko:
            L.append(f"| {row['animal']}띠 {row['zhi']} | {rel or '특별한 충·합 없음(무난)'} | {row['samjae'] or '—'} |")
        else:
            L.append(f"| {row['animal_en']} {row['zhi']} | {rel or 'neutral'} | {row['samjae_en'] or '—'} |")
    if ko:
        L.append("")
        L.append("- 띠별 운세는 년지(태어난 해의 지지) 하나만 보는 아주 큰 그림이에요. 같은 띠라도 사주 전체에 따라 많이 달라요.")
        L.append("- 삼재는 민간에서 조심하라는 3년이에요. 나쁜 일이 생긴다는 뜻이 아니라 무리하지 말라는 신호로 보면 돼요.")
    return "\n".join(L)


# ------------------------------------------------------------------ 명령
def main(argv=None):
    for st in (sys.stdout, sys.stderr):  # 윈도우 콘솔(cp949)에서 ⚠️ 같은 글자가 깨지지 않게
        try:
            st.reconfigure(encoding="utf-8")
        except Exception:
            pass
    ap = argparse.ArgumentParser(description="사주팔자 계산기 (만세력)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    def common(p):
        p.add_argument("--basis", default="clock", choices=["clock", "lmt", "true"],
                       help="시간 기준: clock=시계 시각(기본), lmt=경도 보정, true=진태양시")
        p.add_argument("--zi", default="midnight", choices=["midnight", "23"], help="자시: midnight=0시에 날 바뀜(기본), 23=23시에 날 바뀜")
        p.add_argument("--json", action="store_true", help="JSON으로 출력")
        p.add_argument("--lang", default="ko", choices=["ko", "en"])

    c = sub.add_parser("chart", help="사주 한 사람")
    c.add_argument("--date", required=True, help="생년월일 YYYY-MM-DD")
    c.add_argument("--time", help="태어난 시각 HH:MM (모르면 생략)")
    c.add_argument("--lunar", action="store_true", help="음력 날짜로 입력")
    c.add_argument("--leap", action="store_true", help="윤달")
    c.add_argument("--gender", choices=["m", "f"], help="성별(대운 방향에 필요)")
    c.add_argument("--place", help="태어난 곳(경도 보정용, 예: 서울, 부산, tokyo)")
    c.add_argument("--lon", type=float, help="태어난 곳 경도(동경 +, 서경 -)")
    c.add_argument("--tz", help="한국 밖에서 태어났으면 시간대 (예: -05:00, America/New_York)")
    c.add_argument("--years", help="세운 볼 해, 예: 2026 또는 2026-2030")
    common(c)

    p = sub.add_parser("compat", help="궁합 두 사람")
    p.add_argument("--a", required=True, help='예: "1990-05-15 14:30 f"')
    p.add_argument("--b", required=True, help='예: "1988-11-02 09:10 m" (음력이면 lunar, 윤달이면 leap)')
    common(p)

    def simple(p):
        p.add_argument("--json", action="store_true", help="JSON으로 출력")
        p.add_argument("--lang", default="ko", choices=["ko", "en"])

    t = sub.add_parser("today", help="오늘(또는 --date) 일진")
    t.add_argument("--date")
    simple(t)

    dd = sub.add_parser("ddi", help="띠별 운세(삼재, 올해 띠와의 충·합)")
    dd.add_argument("--year", type=int, help="볼 해(기본: 올해)")
    dd.add_argument("--date", help="생년월일을 넣으면 내 띠만 (입춘 기준으로 띠를 정함)")
    dd.add_argument("--time", help="태어난 시각(입춘 날 태어났을 때 필요)")
    dd.add_argument("--lunar", action="store_true")
    dd.add_argument("--leap", action="store_true")
    simple(dd)

    s = sub.add_parser("terms", help="한 해의 24절기 시각(그때 한국 시계 시각)")
    s.add_argument("--year", type=int, required=True)
    simple(s)

    v = sub.add_parser("convert", help="양력↔음력 바꾸기")
    v.add_argument("--date", required=True)
    v.add_argument("--lunar", action="store_true", help="입력이 음력")
    v.add_argument("--leap", action="store_true")
    simple(v)

    # '--tz -05:00'처럼 '-'로 시작하는 값을 argparse가 옵션으로 오해하지 않게
    argv = list(sys.argv[1:] if argv is None else argv)
    fixed = []
    i = 0
    while i < len(argv):
        if argv[i] in ("--tz", "--lon") and i + 1 < len(argv) and argv[i + 1].startswith("-"):
            fixed.append(f"{argv[i]}={argv[i + 1]}")
            i += 2
            continue
        fixed.append(argv[i])
        i += 1
    a = ap.parse_args(fixed)

    def ymd(txt):
        try:
            y, m, d = [int(x) for x in txt.replace("/", "-").replace(".", "-").split("-")]
            return y, m, d
        except Exception:
            raise SajuError(f"날짜 모양이 이상해요: {txt} (예: 1990-05-15)")

    def real_date(txt):
        y, m, d = ymd(txt)
        try:
            return date(y, m, d)
        except ValueError:
            raise SajuError(f"없는 날짜예요: {txt}")

    try:
        if a.cmd == "chart":
            years = None
            if a.years:
                try:
                    if "-" in a.years:
                        y0, y1 = [int(x) for x in a.years.split("-")]
                    else:
                        y0 = y1 = int(a.years)
                except ValueError:
                    raise SajuError(f"--years 모양이 이상해요: {a.years} (예: 2026 또는 2026-2030)")
                if y1 < y0 or y1 - y0 > 100 or not (1900 <= y0 and y1 <= 2100):
                    raise SajuError(f"--years는 1900~2100 사이, 앞이 작은 숫자로 넣어 주세요: {a.years}")
                years = list(range(y0, y1 + 1))
            info = resolve_input(a.date, a.time, a.lunar, a.leap, a.tz, a.place, a.lon, a.basis, a.zi)
            ch = build_chart(info, a.gender, years)
            print(json.dumps(ch, ensure_ascii=False, indent=1) if a.json else md_chart(ch, a.lang))
        elif a.cmd == "compat":
            r = compat(parse_spec(a.a), parse_spec(a.b), a.basis, a.zi)
            print(json.dumps(r, ensure_ascii=False, indent=1) if a.json else md_compat(r, a.lang))
        elif a.cmd == "today":
            d = real_date(a.date) if a.date else (datetime.now(timezone.utc) + timedelta(hours=9)).date()
            i = day_index(d)
            noon = datetime(d.year, d.month, d.day, 3)
            yidx, midx, prev, nxt = year_month_index(noon)
            out = dict(date=d.isoformat(), day=gz(i), day_ko=gz_ko(i), month=gz(midx), month_ko=gz_ko(midx),
                       year=gz(yidx), year_ko=gz_ko(yidx), animal=ZHI_ANIMAL_KO[i % 12], animal_en=ZHI_ANIMAL_EN[i % 12])
            day0 = datetime(d.year, d.month, d.day) - timedelta(hours=9)
            for t_, _, j in (prev, nxt):
                if day0 <= t_ < day0 + timedelta(days=1):
                    out["term_today"] = dict(name=TERM_NAMES_KO[j], en=TERM_NAMES_EN[j], kst=kst_str(t_))
            lun = solar_to_lunar(d)
            if lun:
                out["lunar"] = f"{lun[0]}-{'윤' if lun[3] else ''}{lun[1]:02d}-{lun[2]:02d}"
            if a.json:
                print(json.dumps(out, ensure_ascii=False, indent=1))
            elif a.lang == "en":
                print(f"{d} day pillar: {out['day']} ({out['animal_en']} day) · month {out['month']} · year {out['year']}"
                      + (f" · lunar {out['lunar'].replace('윤', 'leap ')}" if lun else "")
                      + (f" · solar term {out['term_today']['en']} at {out['term_today']['kst']} KST (month pillar changes then)" if "term_today" in out else ""))
            else:
                print(f"{d} 일진: {out['day']}({out['day_ko']})일 · {out['month']}({out['month_ko']})월 · {out['year']}({out['year_ko']})년"
                      + (f" · 음력 {out['lunar']}" if lun else "")
                      + (f" · 오늘 {out['term_today']['kst'][11:]}에 절기 {out['term_today']['name']} — 그때부터 월주{'와 해(띠)' if out['term_today']['name'] == '입춘' else ''}가 바뀌어요" if "term_today" in out else ""))
        elif a.cmd == "ddi":
            y = a.year or (datetime.now(timezone.utc) + timedelta(hours=9)).year
            if not 1900 <= y <= 2100:
                raise SajuError("띠별 운세는 1900~2100년만 돼요")
            r = ddi_year(y, a.lang)
            mine = ddi_of_birth(a.date, a.time, a.lunar, a.leap) if a.date else None
            if mine:
                r["mine"] = {k: v for k, v in mine.items() if k != "z"}
            print(json.dumps(r, ensure_ascii=False, indent=1) if a.json else md_ddi(r, mine, a.lang))
        elif a.cmd == "terms":
            if a.year not in _load_terms():
                raise SajuError("절기 표는 1899~2101년만 있어요")
            rows = [dict(name=TERM_NAMES_KO[i], hanja=TERM_NAMES_HANJA[i], en=TERM_NAMES_EN[i],
                         kst=kst_str(term_time(a.year, i)),
                         starts_month=ZHI[JIE_MONTH_ZHI[i]] if i in JIE_MONTH_ZHI else "") for i in range(24)]
            if a.json:
                print(json.dumps(rows, ensure_ascii=False, indent=1))
            elif a.lang == "en":
                print(f"## Solar terms {a.year} (Korean clock time of that era)\n\n| Term | Time | Starts month |\n|---|---|---|")
                for r in rows:
                    print(f"| {r['en']} {r['hanja']} | {r['kst']} | {r['starts_month']} |")
            else:
                print(f"## {a.year}년 24절기 (그때 한국 시계 시각)\n\n| 절기 | 시각 | 달 시작 |\n|---|---|---|")
                for r in rows:
                    print(f"| {r['name']} {r['hanja']} | {r['kst']} | {r['starts_month'] + '월' if r['starts_month'] else ''} |")
        elif a.cmd == "convert":
            y, m, d = ymd(a.date)
            if a.leap and not a.lunar:
                raise SajuError("윤달(--leap)은 음력(--lunar)과 같이 써야 해요")
            if a.lunar:
                sd = lunar_to_solar(y, m, d, a.leap)
                out = dict(lunar=f"{y}-{'윤' if a.leap else ''}{m:02d}-{d:02d}", solar=sd.isoformat())
            else:
                r = solar_to_lunar(real_date(a.date))
                if not r:
                    raise SajuError("음력 표 범위(1900~2049) 밖이에요")
                out = dict(solar=real_date(a.date).isoformat(), lunar=f"{r[0]}-{'윤' if r[3] else ''}{r[1]:02d}-{r[2]:02d}", leap=r[3])
            if a.json:
                print(json.dumps(out, ensure_ascii=False))
            elif a.lang == "en":
                print(f"solar {out['solar']} = lunar {out['lunar'].replace('윤', 'leap ')}")
            else:
                print(f"양력 {out['solar']} = 음력 {out['lunar']}")
    except SajuError as e:
        print(f"오류: {e}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
