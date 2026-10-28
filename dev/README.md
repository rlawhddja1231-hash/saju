# dev — 자료 다시 만들기·맞춰 보기 (일반 사용자는 필요 없음)

```
pip install lunar-python ephem korean-lunar-calendar
python3 dev/gen_terms.py 1899 2101 raw.json      # 절기 표 + PyEphem(VSOP87)과 비교(가장 큰 차이 출력)
python3 dev/gen_lunar.py lunar_ko.json           # 한국 음력 표
python3 dev/cross_check.py plugins/saju/skills/saju/scripts 20000   # lunar-python과 네 기둥 비교
```
gen_terms.py의 결과는 data/terms.json 형식(해마다 첫 값 + 차이)으로 바꿔 넣습니다.
