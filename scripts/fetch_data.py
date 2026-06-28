#!/usr/bin/env python3
"""
장 시작 전 매크로 대시보드 - 일일 데이터 수집 스크립트 (Twelve Data API 버전)
2026년 3월부터 Stooq가 API 키를 요구하기 시작해 더 이상 무료로 못 쓰게 되어,
Twelve Data(무료 가입, 분당 8회 호출 제한)로 전환했다.

필요 환경변수: TWELVEDATA_API_KEY (GitHub Secrets에 등록)
"""
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

API_KEY = os.environ.get("TWELVEDATA_API_KEY", "").strip()

# (표시이름, 그룹, twelve data 심볼)
ITEMS = [
    # 환율·통화
    ("USD/KRW", "fx", "USD/KRW"),
    ("USD/JPY", "fx", "USD/JPY"),
    ("EUR/USD", "fx", "EUR/USD"),
    ("달러지수 (DXY)", "fx", "DXY"),
    # 금리·채권 (단위: %)
    ("미국 10년물", "rates", "US10Y"),
    ("미국 30년물", "rates", "US30Y"),
    ("일본 10년물", "rates", "JP10Y"),
    ("한국 10년물", "rates", "KR10Y"),
    ("독일 10년물", "rates", "DE10Y"),
    # 원자재·에너지
    ("금 (Gold)", "commodity", "XAU/USD"),
    ("WTI 유가", "commodity", "WTI/USD"),
    ("브렌트유", "commodity", "BRENT/USD"),
    ("천연가스", "commodity", "NATGAS/USD"),
    # 농산물
    ("미국 소맥(밀)", "agri", "WHEAT/USD"),
    ("미국 옥수수", "agri", "CORN/USD"),
    ("미국 대두", "agri", "SOYBEAN/USD"),
    # 암호화폐
    ("비트코인", "crypto", "BTC/USD"),
    # 변동성
    ("VIX 지수", "vol", "VIX"),
    # 미국 증시
    ("다우존스", "us_eq", "DJI"),
    ("S&P500", "us_eq", "SPX"),
    ("나스닥100", "us_eq", "NDX"),
    ("러셀2000", "us_eq", "RUT"),
    # 글로벌 증시
    ("니케이225", "global_eq", "NI225"),
    ("Euro Stoxx 50", "global_eq", "STOXX50E"),
    ("항셍지수", "global_eq", "HSI"),
    ("대만 가권지수", "global_eq", "TWII"),
]

QUOTE_URL = "https://api.twelvedata.com/quote?symbol={symbol}&apikey={key}"


def fetch_one(symbol: str):
    """Twelve Data /quote 엔드포인트에서 현재가(close)를 가져온다. 실패 시 None."""
    url = QUOTE_URL.format(symbol=urllib.parse.quote(symbol), key=API_KEY)
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"  [실패] {symbol}: HTTP {e.code} - {body[:200]}", file=sys.stderr)
        return None
    except (urllib.error.URLError, TimeoutError) as e:
        print(f"  [실패] {symbol}: {e}", file=sys.stderr)
        return None

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        print(f"  [실패] {symbol}: JSON 파싱 실패 - {raw[:150]}", file=sys.stderr)
        return None

    if "code" in data and data.get("status") == "error":
        print(f"  [실패] {symbol}: {data.get('message')}", file=sys.stderr)
        return None

    close = data.get("close")
    date = data.get("datetime")
    if close is None:
        print(f"  [실패] {symbol}: close 값 없음 - {raw[:150]}", file=sys.stderr)
        return None
    try:
        value = float(close)
    except (ValueError, TypeError):
        return None
    return {"value": value, "date": date}


def main():
    if not API_KEY:
        print("오류: TWELVEDATA_API_KEY 환경변수가 설정되지 않았습니다.", file=sys.stderr)
        print("GitHub 저장소 Settings > Secrets and variables > Actions 에서 등록해주세요.", file=sys.stderr)
        sys.exit(1)

    results = []
    print(f"총 {len(ITEMS)}개 항목 수집 시작...")
    for i, (name, group, symbol) in enumerate(ITEMS):
        data = fetch_one(symbol)
        if data:
            print(f"  [OK] {name} ({symbol}): {data['value']}")
            results.append({
                "name": name, "group": group, "ticker": symbol,
                "value": data["value"], "date": data["date"], "ok": True,
            })
        else:
            print(f"  [N/A] {name} ({symbol}): 데이터 없음")
            results.append({
                "name": name, "group": group, "ticker": symbol,
                "value": None, "date": None, "ok": False,
            })
        # 무료 플랜은 분당 8회 제한 -> 매 호출 사이 8초 대기 (26개 * 8초 = 약 3.5분)
        if i < len(ITEMS) - 1:
            time.sleep(8)

    output = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "items": results,
    }

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
