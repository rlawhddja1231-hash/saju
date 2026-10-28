#!/usr/bin/env python3
"""설치 확인용 자체 시험. 설치할 것 없이 돌아갑니다: python3 tests/selftest.py

기대값은 한국천문연구원(KASI) 절기 시각과, 독립 구현(lunar_python, 6tail)으로 맞춰 본 값입니다.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
import saju  # noqa: E402

CASES = [
    # (날짜, 시각, 옵션, 기대 [년, 월, 일, 시], 설명)
    ("2000-02-04", "21:39", {}, ["己卯", "丁丑", "壬辰", "辛亥"], "입춘(21:40) 1분 전 → 아직 기묘년"),
    ("2000-02-04", "21:41", {}, ["庚辰", "戊寅", "壬辰", "辛亥"], "입춘 1분 뒤 → 경진년"),
    ("2024-02-04", "17:27", {}, ["癸卯", "乙丑", "戊戌", "辛酉"], "입춘 17:27:07 직전"),
    ("2024-02-04", "17:28", {}, ["甲辰", "丙寅", "戊戌", "辛酉"], "입춘 직후 → 갑진년"),
    ("1990-05-15", "14:30", {}, ["庚午", "辛巳", "庚辰", "癸未"], "평범한 날"),
    ("1988-07-01", "23:20", {}, ["戊辰", "戊午", "丁巳", "辛亥"], "서머타임: 시계 23:20 → 표준시 22:20(亥시)"),
    ("1958-08-15", "06:00", {}, ["戊戌", "庚申", "甲子", "丁卯"], "UTC+8:30 시절의 서머타임"),
    ("2010-10-10", "23:30", {}, ["庚寅", "丙戌", "癸巳", "甲子"], "자시: 0시에 날 바뀜(기본)"),
    ("2010-10-10", "23:30", {"zi": "23"}, ["庚寅", "丙戌", "甲午", "甲子"], "자시: 23시에 날 바뀜"),
    ("1999-12-31", "00:10", {}, ["己卯", "丙子", "丁巳", "庚子"], "새벽 자시"),
]


def main():
    bad = 0
    for d, t, opt, want, why in CASES:
        info = saju.resolve_input(d, t, **opt)
        got = [p["ganzhi"] for p in saju.build_chart(info)["pillars"]]
        ok = got == want
        bad += not ok
        print(("통과" if ok else "실패"), d, t, opt or "", got, "" if ok else f"(기대 {want})", "—", why)
    # 음력
    for (y, m, dd, leap), want in [((2023, 2, 1, True), "2023-03-22"), ((2000, 8, 4, False), "2000-09-01"),
                                    ((2020, 4, 1, True), "2020-05-23")]:
        got = saju.lunar_to_solar(y, m, dd, leap).isoformat()
        ok = got == want
        bad += not ok
        print(("통과" if ok else "실패"), f"음력 {y}-{'윤' if leap else ''}{m}-{dd} → {got}")
    # 대운
    info = saju.resolve_input("1990-05-15", "14:30")
    dw = saju.build_chart(info, "f")["daewoon"]
    ok = (not dw["forward"]) and dw["start_age"] == 3 and dw["pillars"][0]["ganzhi"] == "庚辰"
    bad += not ok
    print(("통과" if ok else "실패"), "대운: 庚년생 여자 역행, 대운수 3, 첫 대운 庚辰")
    # 절기 시각(KASI 발표값)
    for y, i, want in [(2000, 2, "2000-02-04 21:40"), (1984, 2, "1984-02-05 00:19"), (2026, 2, "2026-02-04 05:02")]:
        got = saju.kst_str(saju.term_time(y, i))
        ok = got == want
        bad += not ok
        print(("통과" if ok else "실패"), f"{y} 입춘 {got}")
    print("\n모두 통과" if bad == 0 else f"\n실패 {bad}개")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
