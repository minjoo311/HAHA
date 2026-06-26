#!/usr/bin/env python3
"""
장 시작 전 매크로 대시보드 - 일일 데이터 수집 스크립트
Stooq(무료, 키 불필요)에서 환율/금리/원자재/지수 데이터를 가져와 docs/data.json에 저장한다.
GitHub Actions가 매일 1회 이 스크립트를 실행한다.
"""
import csv
import io
import json
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone

# (표시이름, 그룹, stooq 티커)
# 티커가 잘못되었거나 데이터가 없으면 해당 항목은 "N/A"로 표시되고 나머지는 정상 진행된다.
ITEMS = [
    # 환율·통화
    ("USD/KRW", "fx", "usdkrw"),
    ("USD/JPY", "fx", "usdjpy"),
    ("EUR/USD", "fx", "eurusd"),
    ("달러지수 (DXY)", "fx", "dx.f"),
    # 금리·채권 (단위: %)
    ("미국 10년물", "rates", "10yusy.b"),
    ("미국 30년물", "rates", "30yusy.b"),
    ("일본 10년물", "rates", "10yjpy.b"),
    ("한국 10년물", "rates", "10ykry.b"),
    ("독일 10년물", "rates", "10ydey.b"),
    # 원자재·에너지
    ("금 (Gold)", "commodity", "xauusd"),
    ("WTI 유가", "commodity", "cl.f"),
    ("브렌트유", "commodity", "lco.f"),
    ("천연가스", "commodity", "ng.f"),
    # 농산물
    ("미국 소맥(밀)", "agri", "zw.f"),
    ("미국 옥수수", "agri", "zc.f"),
    ("미국 대두", "agri", "zs.f"),
    # 암호화폐
    ("비트코인", "crypto", "btcusd"),
    # 변동성
    ("VIX 지수", "vol", "^vix"),
    # 미국 증시
    ("다우존스", "us_eq", "^dji"),
    ("S&P500", "us_eq", "^spx"),
    ("나스닥100", "us_eq", "^ndq"),
    ("러셀2000", "us_eq", "^rut"),
    # 글로벌 증시
    ("니케이225", "global_eq", "^nkx"),
    ("Euro Stoxx 50", "global_eq", "^estx50"),
    ("항셍지수", "global_eq", "^hsi"),
    ("대만 가권지수", "global_eq", "^twii"),
]

STOOQ_URL = "https://stooq.com/q/l/?s={ticker}&f=sd2t2ohlcv&h&e=csv"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; personal-dashboard-script/1.0)"}


def fetch_one(ticker: str):
    """Stooq CSV에서 마지막 종가(Close)와 날짜를 가져온다. 실패 시 None."""
    url = STOOQ_URL.format(ticker=ticker)
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
    except (urllib.error.URLError, TimeoutError) as e:
        print(f"  [실패] {ticker}: {e}", file=sys.stderr)
        return None

    reader = csv.DictReader(io.StringIO(raw))
    row = next(reader, None)
    if not row:
        return None

    # Stooq는 데이터 없을 때 Close 값이 'N/D'
    close = row.get("Close") or row.get("Close ")
    date = row.get("Date")
    if not close or close in ("N/D", ""):
        return None
    try:
        value = float(close)
    except ValueError:
        return None
    return {"value": value, "date": date}


def main():
    results = []
    print(f"총 {len(ITEMS)}개 항목 수집 시작...")
    for name, group, ticker in ITEMS:
        data = fetch_one(ticker)
        if data:
            print(f"  [OK] {name} ({ticker}): {data['value']}")
            results.append({
                "name": name,
                "group": group,
                "ticker": ticker,
                "value": data["value"],
                "date": data["date"],
                "ok": True,
            })
        else:
            print(f"  [N/A] {name} ({ticker}): 데이터 없음")
            results.append({
                "name": name,
                "group": group,
                "ticker": ticker,
                "value": None,
                "date": None,
                "ok": False,
            })
        time.sleep(0.5)  # 과도한 요청 방지

    output = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "items": results,
    }

    # 이전 데이터 불러와서 전일 대비 변화율 계산용으로 history에 누적
    import os
    docs_dir = os.path.join(os.path.dirname(__file__), "..", "docs")
    os.makedirs(docs_dir, exist_ok=True)
    data_path = os.path.join(docs_dir, "data.json")
    prev_path = os.path.join(docs_dir, "data_prev.json")

    if os.path.exists(data_path):
        with open(data_path, "r", encoding="utf-8") as f:
            prev = json.load(f)
        with open(prev_path, "w", encoding="utf-8") as f:
            json.dump(prev, f, ensure_ascii=False, indent=2)

    with open(data_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n완료: {data_path} 에 저장됨")
    ok_count = sum(1 for r in results if r["ok"])
    print(f"성공 {ok_count}/{len(results)}건")


if __name__ == "__main__":
    main()
