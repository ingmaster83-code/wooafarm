#!/usr/bin/env python3
"""
process_data.py - 원본 데이터를 Jekyll 페이지 생성용 JSON으로 가공

입력: _rawdata/offices_raw.json
출력: _rawdata/offices.json (사업소 목록), search_index.json (검색용, 루트)

사용법:
  python scripts/process_data.py
"""
import json, re, hashlib, sys
from pathlib import Path
from collections import Counter

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).parent.parent
RAW = ROOT / "_rawdata" / "offices_raw.json"
OUT = ROOT / "_rawdata" / "offices.json"
SEARCH_INDEX_OUT = ROOT / "search_index.json"

DO_MAP = {
    "서울특별시": "서울", "부산광역시": "부산", "대구광역시": "대구",
    "인천광역시": "인천", "광주광역시": "광주", "대전광역시": "대전",
    "울산광역시": "울산", "세종특별자치시": "세종", "경기도": "경기",
    "강원특별자치도": "강원", "강원도": "강원",
    "충청북도": "충북", "충청남도": "충남",
    "전북특별자치도": "전북", "전라북도": "전북", "전라남도": "전남",
    "경상북도": "경북", "경상남도": "경남", "제주특별자치도": "제주",
    "전남광주통합특별시": "광주",
}

# 장비 종류 컬럼 -> (표시명, 아이콘)
EQUIP_FIELDS = [
    ("TRCTOR_HOLD_CO", "트랙터", "🚜"),
    ("CULTVT_HOLD_CO", "경운기", "🛞"),
    ("MANAGE_HOLD_CO", "관리기", "⚙️"),
    ("HARVEST_HOLD_CO", "땅속작물수확기", "🥔"),
    ("THRESHER_HOLD_CO", "탈곡기", "🌾"),
    ("PLANTER_HOLD_CO", "파종기", "🌱"),
    ("TRANSPLANT_HOLD_CO", "이앙기", "🌿"),
    ("RCEPNT_HOLD_CO", "벼수확·운반기", "🚛"),
]


def make_slug(name: str, addr: str) -> str:
    slug = re.sub(r"[^\w가-힣\s-]", "", name).strip()
    slug = re.sub(r"\s+", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    h = hashlib.md5(f"{name}|{addr}".encode("utf-8")).hexdigest()[:6]
    return f"{slug}-{h}" if slug else h


def to_int(v):
    try:
        return int(str(v).strip())
    except (ValueError, TypeError):
        return 0


def extract_sigungu(addr: str) -> str:
    if not addr:
        return ""
    for p in addr.split()[1:3]:
        if p.endswith(("시", "군", "구")):
            return p
    return ""


def main():
    raw = json.loads(RAW.read_text(encoding="utf-8"))
    items = []
    seen_slugs = Counter()
    for d in raw:
        # 필드명 주의: Jekyll 내장 Page.name과 충돌하므로 "officeName" 사용
        # (wooaedu/wooaonnuri에서 반복 확인된 버그, jekyll_page_name_collision_bug 참고)
        office_name = (d.get("OFFICE_NM") or "").strip()
        if not office_name:
            continue
        addr = (d.get("RDNMADR") or "").strip() or (d.get("LNMADR") or "").strip()
        do_full = addr.split()[0] if addr else ""
        do_short = DO_MAP.get(do_full, do_full)
        sigungu = extract_sigungu(addr)

        equipment = []
        total_equip = 0
        for field, label, icon in EQUIP_FIELDS:
            cnt = to_int(d.get(field))
            total_equip += cnt
            if cnt > 0:
                equipment.append({"label": label, "icon": icon, "count": cnt})

        lat = (d.get("LATITUDE") or "").strip()
        lng = (d.get("LONGITUDE") or "").strip()

        slug = make_slug(office_name, addr)
        seen_slugs[slug] += 1
        if seen_slugs[slug] > 1:
            slug = f"{slug}-{seen_slugs[slug]}"

        items.append({
            "officeName": office_name,
            "doShort": do_short,
            "doFull": do_full,
            "sigungu": sigungu,
            "addr": addr,
            "tel": (d.get("OFFICE_PHONE_NUMBER") or d.get("PHONE_NUMBER") or "").strip(),
            "lat": lat,
            "lng": lng,
            "equipment": equipment,
            "totalEquip": total_equip,
            "etcEquip": (d.get("ETC_RENT_HOLD_CO") or "").strip(),
            "institution": (d.get("INSTITUTION_NM") or "").strip(),
            "refDate": (d.get("REFERENCE_DATE") or "").strip(),
            "slug": slug,
        })

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"사업소 {len(items)}개 저장 → {OUT}")

    do_counts = Counter(i["doShort"] for i in items)
    print("\n지역별 수:")
    for do, cnt in sorted(do_counts.items(), key=lambda x: -x[1]):
        print(f"  {do}: {cnt}개")

    no_coord = sum(1 for i in items if not i["lat"] or not i["lng"])
    print(f"\n좌표 없음: {no_coord}개")

    index = [
        {
            "n": i["officeName"], "slug": i["slug"], "doShort": i["doShort"],
            "sigungu": i["sigungu"], "addr": i["addr"],
            "equip": [e["label"] for e in i["equipment"]],
        }
        for i in items
    ]
    SEARCH_INDEX_OUT.write_text(json.dumps(index, ensure_ascii=False), encoding="utf-8")
    print(f"검색 인덱스 {len(index)}건 저장 → {SEARCH_INDEX_OUT}")


if __name__ == "__main__":
    main()
