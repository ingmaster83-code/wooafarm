#!/usr/bin/env python3
"""
fetch_offices.py - 전국농기계임대정보표준데이터 수집 (농림축산식품부/지방자치단체)

사용법:
  python scripts/fetch_offices.py
"""
import sys, json, time
from pathlib import Path
import requests

sys.stdout.reconfigure(encoding="utf-8")

PUBLIC_DATA_PK = "15017325"
SVC_TABLE = "tn_pubr_public_frcn_rent_info_svc"
COLUMNS = [
    "OFFICE_NM", "OFFICE_PHONE_NUMBER", "RDNMADR", "LNMADR", "LATITUDE", "LONGITUDE",
    "TRCTOR_HOLD_CO", "CULTVT_HOLD_CO", "MANAGE_HOLD_CO", "HARVEST_HOLD_CO",
    "THRESHER_HOLD_CO", "PLANTER_HOLD_CO", "TRANSPLANT_HOLD_CO", "RCEPNT_HOLD_CO",
    "ETC_RENT_HOLD_CO", "PHONE_NUMBER", "INSTITUTION_NM", "REFERENCE_DATE",
]
OUT_FILE = Path(__file__).parent.parent / "_rawdata" / "offices_raw.json"
PER_PAGE = 10000


def fetch_page(page: int) -> list:
    params = [("publicDataPk", PUBLIC_DATA_PK)]
    params += [("colNmList", c) for c in COLUMNS]
    params += [
        ("totalCount", "99999"),
        ("svcTableNm", SVC_TABLE),
        ("perPage", str(PER_PAGE)),
        ("page", str(page)),
    ]
    resp = requests.get(
        "https://www.data.go.kr/download/standard.json",
        params=params, timeout=60,
        headers={"User-Agent": "Mozilla/5.0"},
    )
    resp.raise_for_status()
    data = resp.json()
    if isinstance(data, dict):
        return []
    return data


def main():
    print("=== 전국농기계임대정보표준데이터 수집 시작 ===")
    all_items = []
    page = 1
    while True:
        items = fetch_page(page)
        if not items:
            break
        all_items.extend(items)
        print(f"  페이지 {page}: {len(items)}개 (누적 {len(all_items)})")
        if len(items) < PER_PAGE:
            break
        page += 1
        time.sleep(0.3)

    if not all_items:
        raise SystemExit("수집된 데이터가 없습니다.")

    if OUT_FILE.exists():
        existing = json.loads(OUT_FILE.read_text(encoding="utf-8"))
        if len(all_items) < len(existing) * 0.5:
            raise SystemExit(
                f"수집 건수({len(all_items)}건)가 기존 데이터({len(existing)}건)의 절반 미만입니다. "
                "오류로 판단하여 저장을 중단합니다."
            )

    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUT_FILE.write_text(json.dumps(all_items, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n완료: {OUT_FILE}")
    print(f"  총 {len(all_items)}개 사업소 저장")


if __name__ == "__main__":
    main()
