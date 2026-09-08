# FCS Lab

전차 사격통제(FCS) 시뮬레이터에서 나온 사격 기록 CSV를 회차별로 저장하고
비교·분석하는 웹 서비스.

## 왜 만들었나

시뮬레이터가 내려주는 파일은 `shots (29).csv`, `shots (33).csv` 처럼
브라우저가 붙인 번호만 다를 뿐이라, 다운로드 폴더에 쌓이고 나면
어느 파일이 어떤 조건에서 나온 것인지 알 수 없다.
실험 조건 중 일부(적 사격 on/off 등)는 CSV 안에 아예 기록되지 않아서,
조건이 다른 회차를 섞어 평균을 내면 분석이 통째로 무의미해진다.

## 기술 스택

- 백엔드: FastAPI, SQLAlchemy
- DB: 개발 SQLite / 배포 PostgreSQL (`DATABASE_URL` 만 교체)
- 프론트엔드: React + Vite (예정)

## 실행

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

http://localhost:8000/docs 에서 API를 직접 호출해 볼 수 있다.

## 테스트

```bash
cd backend
pytest -q
```

## 데이터 모델

`experiment` 1개 = 사격 실험 1회차 = CSV 파일 1개. `shot` 은 그 회차의 개별 탄.

CSV 전 행에 같은 값으로 들어오는 `bias_range` / `bias_n` / `lon_shift` 는
사격 기록이 아니라 실험 설정이므로 `experiment` 쪽으로 올렸다.

## 지표 정의

| 컬럼 | 의미 |
|---|---|
| `miss` | 탄착 오차 [m]. 핵심 성능 지표 |
| `dy` | 표적과의 고저차 [m]. 최소 사거리를 좌우한다 |
| `kind` | tank / terrain. terrain 은 지형 오폭 |
| `zone` | front / rear / side |

`p_hit` 은 기록된 전 회차에서 1.0 으로만 나오므로 성능 지표로 쓰지 않는다.

## 막혔던 문제와 해결

<!-- 여기는 직접 작성한다. 아래는 기록해 둘 만한 항목 목록. -->

- [ ] CSV 첫 컬럼명이 `id` 가 아니라 `\ufeffid` 로 읽히던 문제 (UTF-8 BOM)
- [ ] 한 발도 못 쏜 회차(0행 CSV) 처리
- [ ] 회차 평균 miss 와 중앙값이 반대 방향을 가리키던 문제
- [ ]
