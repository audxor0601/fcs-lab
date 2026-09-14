덮어쓰기 안내
=============

폴더를 fcs-lab 위에 그대로 덮어씁니다.

  backend/   →  fcs-lab/backend/
  frontend/  →  fcs-lab/frontend/
  data/      →  fcs-lab/data/   (새 CSV 9개 + notes.json)

덮어쓴 뒤:

1. backend/fcs_lab.db 파일을 삭제한다
   (테이블 구조가 바뀌었으므로 반드시 지워야 한다)

2. 백엔드
      cd backend
      source .venv/bin/activate        (윈도우: .venv\Scripts\Activate.ps1)
      python seed.py
      uvicorn app.main:app --reload

3. 프론트엔드 (다른 터미널)
      cd frontend
      npm run dev

4. http://localhost:5173/


이번에 바뀐 것
--------------
- 명중률이 주 지표가 됐다. kind=tank 가 명중, terrain 이 빗나감이다.
  (p_hit 은 발사 전 예측값이라 쓰지 않는다)
- 정지/기동 사격을 자동으로 구분하고, 섞여 있으면 경고한다.
- bias_range 를 회차 설정이 아니라 사격별 값으로 옮겼다.
  BiasEstimator 가 사격 중에 학습하는 값이기 때문이다.
- 회차 29~46 (18개) 전부 들어간다.
