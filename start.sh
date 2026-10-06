#!/bin/bash
# 맥/리눅스용 실행 스크립트. 윈도우는 START.bat 을 쓴다.
set -e
cd "$(dirname "$0")/backend"

if [ ! -d ".venv" ]; then
  echo "[1/3] 처음 실행입니다. 준비 중..."
  python3 -m venv .venv
  source .venv/bin/activate
  pip install -q --upgrade pip
  pip install -r requirements.txt
else
  echo "[1/3] 준비 완료"
  source .venv/bin/activate
fi

echo
echo "[2/3] data 폴더의 CSV 를 불러옵니다..."
python seed.py

echo
echo "[3/3] 서버를 시작합니다. 끄려면 Ctrl+C."
echo
( sleep 2 && open http://127.0.0.1:8000/ ) &
python -m uvicorn app.main:app --reload
