"""Write the synthetic two-county state ZZ fixtures under data/sample/ in the real file formats.

Run with ``uv run python scripts/make_sample_zz.py``. Deterministic: the same
bytes every time, so a fixture change shows up as a git diff. The numbers are
invented but internally consistent (units in structure sum to the total, the
address-count files read double from July 2023 on, one block group has no ACS
row, one county has no permit row in 2017), so every pipeline branch runs
offline in ``make demo`` and the tests.

ZZ geography: state FIPS 99. Alder County (99001, metropolitan central, six
block groups) has a light-rail station, a bus stop and a station entrance;
Birch County (99003, outside any CBSA, four block groups) has a ferry stop.
"""

from __future__ import annotations

import csv
import datetime
import json
import zipfile
from pathlib import Path

import openpyxl

ROOT = Path(__file__).resolve().parents[1] / "data" / "sample"
YEARS = range(2016, 2026)

COUNTIES = {
    "99001": {"name": "Alder County", "land": 500.0, "lat": 44.05, "lon": -100.05},
    "99003": {"name": "Birch County", "land": 800.0, "lat": 44.60, "lon": -100.60},
}
BLOCK_GROUPS = [
    # geoid, population, lat, lon
    ("990010001001", 1200, 44.000, -100.000),   # 0.14 mi from the light-rail station
    ("990010001002", 900, 44.002, -99.992),     # 0.40 mi from it
    ("990010001003", 1500, 44.050, -100.050),   # bus stop next door (ignored)
    ("990010002001", 800, 44.100, -100.100),    # station entrance next door (ignored)
    ("990010002002", 700, 44.150, -100.150),
    ("990010002003", 600, 44.200, -100.200),
    ("990030001001", 400, 44.500, -100.500),
    ("990030001002", 350, 44.550, -100.550),
    ("990030002001", 300, 44.600, -100.600),
    ("990030002002", 250, 44.650, -100.650),    # 0.03 mi from the ferry stop; no ACS row
]
PEP = {
    "99001": [20000, 20000, 20200, 20400, 20600, 20800, 21000],   # base, 2020..2025
    "99003": [10000, 10000, 10100, 10200, 10300, 10400, 10500],
}
# Address-count county totals per vintage: 2022-06 near the true stock, later ones doubled.
ACLF = {
    "062022": {"99001": 20350, "99003": 10200},
    "072023": {"99001": 41300, "99003": 20700},
    "122023": {"99001": 41400, "99003": 20700},
    "072024": {"99001": 41700, "99003": 20800},
    "122024": {"99001": 41800, "99003": 20900},
    "072025": {"99001": 42100, "99003": 21000},
    "122025": {"99001": 42200, "99003": 21100},
    "072026": {"99001": 42500, "99003": 21200},
}
ACS_COUNTY = {
    #          total  det   att  2u   3-4  5-9   10-19 20-49 50+  mob  other occ   vac   own   rent  value  rent$
    "99001": [20500, 12000, 800, 500, 400, 2000, 1500, 1000, 1300, 900, 100, 18500, 2000, 12500, 6000, 350000, 1400],
    "99003": [10300, 8000, 200, 300, 200, 300, 200, 100, 100, 850, 50, 8300, 2000, 6500, 1800, 250000, 1100],
}


def w(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="")


def save_xlsx(wb: openpyxl.Workbook, path: Path) -> None:
    """Save with fixed document timestamps so the bytes are reproducible."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fixed = datetime.datetime(2026, 1, 1, 0, 0, 0)
    wb.properties.created = fixed
    wb.properties.modified = fixed
    wb.properties.lastModifiedBy = "make_sample_zz"
    wb.properties.creator = "make_sample_zz"
    wb.save(path)


def gazetteer() -> None:
    header = "USPS|GEOID|GEOIDFQ|ANSICODE|NAME|ALAND|AWATER|ALAND_SQMI|AWATER_SQMI|INTPTLAT|INTPTLONG"
    rows = [header, "NH|33001|0500000US33001|00873174|Belknap County|1040947197|176373665|401.912|68.098|43.519109|-71.425366"]
    for fips, c in COUNTIES.items():
        aland = int(c["land"] * 2_589_988)
        rows.append(f"ZZ|{fips}|0500000US{fips}|0000{fips}|{c['name']}|{aland}|1000000|{c['land']:.3f}|0.386|{c['lat']:.6f}|{c['lon']:.6f}")
    out = ROOT / "gazetteer" / "2025_Gaz_counties_national.zip"
    out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        info = zipfile.ZipInfo("2025_Gaz_counties_national.txt", date_time=(2025, 1, 1, 0, 0, 0))
        z.writestr(info, "\n".join(rows) + "\n")


def cbsa() -> None:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "List 1"
    ws.append(["Table with row headers in column A and column headers in row 3"])
    ws.append(["List 1. CORE BASED STATISTICAL AREAS (CBSAs), METROPOLITAN DIVISIONS, AND COMBINED STATISTICAL AREAS (CSAs), JULY 2023"])
    ws.append(["CBSA Code", "Metropolitan Division Code", "CSA Code", "CBSA Title",
               "Metropolitan/Micropolitan Statistical Area", "Metropolitan Division Title", "CSA Title",
               "County/County Equivalent", "State Name", "FIPS State Code", "FIPS County Code",
               "Central/Outlying County"])
    ws.append(["29060", None, "148", "Laconia, NH", "Micropolitan Statistical Area", None,
               "Boston-Worcester-Providence, MA-RI-NH", "Belknap County", "New Hampshire", "33", "001", "Central"])
    ws.append(["99900", None, None, "Alderton, ZZ", "Metropolitan Statistical Area", None, None,
               "Alder County", "Zetaland", "99", "001", "Central"])
    save_xlsx(wb, ROOT / "cbsa" / "list1_2023.xlsx")


def bps() -> None:
    h1 = ("Survey,FIPS,FIPS,Region,Division,County,,1-unit,,,2-units,,,3-4 units,,,5+ units,,,"
          "1-unit rep,,,2-units rep,,,3-4 units rep,,, 5+units rep")
    h2 = ("Date,State,County,Code,Code,Name,Bldgs,Units,Value,Bldgs,Units,Value,Bldgs,Units,Value,"
          "Bldgs,Units,Value,Bldgs,Units,Value,Bldgs,Units,Value,Bldgs,Units,Value,Bldgs,Units,Value")
    totals = {}
    for y in YEARS:
        lines = [h1, h2, " "]
        lines.append(f"{y},33,001,1,1,{'Belknap County':<30},300,300,100000000,10,20,4000000,2,8,2000000,3,30,5000000,"
                     "290,290,97000000,10,20,4000000,2,8,2000000,3,30,5000000")
        cells = {}
        for fips, c in COUNTIES.items():
            if fips == "99003" and y == 2017:
                continue  # no permit-issuing place reported that year
            base = 100 + (y - 2016) * 10 if fips == "99001" else 40 + (y - 2016) * 2
            u5 = (80 if y >= 2021 else 50) if fips == "99001" else 0
            u1, u2, u34 = base, 10 if fips == "99001" else 2, 6 if fips == "99001" else 0
            cells[fips] = (u1, u2, u34, u5)
            lines.append(f"{y},{fips[:2]},{fips[2:]},4,8,{c['name']:<30},{u1},{u1},{u1 * 300000},"
                         f"{u2 // 2},{u2},{u2 * 200000},{u34 // 3 if u34 else 0},{u34},{u34 * 150000},"
                         f"{u5 // 40 if u5 else 0},{u5},{u5 * 120000},"
                         f"{u1},{u1},{u1 * 300000},{u2 // 2},{u2},{u2 * 200000},{u34 // 3 if u34 else 0},{u34},"
                         f"{u34 * 150000},{u5 // 40 if u5 else 0},{u5},{u5 * 120000}")
        w(ROOT / "bps" / f"co{y}a.txt", "\n".join(lines) + "\n")
        totals[y] = tuple(sum(v[i] for v in cells.values()) for i in range(4))
    s1 = ("Survey,FIPS,Region,Division,State,,1-unit,,,2-units,,,3-4 units,,,5+ units,,,1-unit rep,,,"
          "2-units rep,,,3-4 units rep       ,,,5+ units rep")
    s2 = ("Date,State,Code,Code,Name,Bldgs,Units,Value,Bldgs,Units,Value,Bldgs,Units,Value,      Bldgs,Units,Value,"
          "Bldgs,Units,Value,Bldgs,Units,Value,      Bldgs,Units,Value,Bldgs,Units,Value")
    for y in (2024, 2025):
        u1, u2, u34, u5 = totals[y]
        lines = [s1, s2, " ",
                 (f"{y}99,33,1,1,New Hampshire,3279,3279,1296819,83,166,34508,46,157,29731,87,1428,291671,"
                 "2784,2784,1123431,72,144,29173,31,112,21638,50,1045,213804"),
                 (f"{y}99,99,4,8,Zetaland,{u1},{u1},{u1 * 300},{u2 // 2},{u2},{u2 * 200},{u34 // 3 if u34 else 0},{u34},"
                 f"{u34 * 150},{u5 // 40 if u5 else 0},{u5},{u5 * 120},{u1},{u1},{u1 * 300},{u2 // 2},{u2},{u2 * 200},"
                 f"{u34 // 3 if u34 else 0},{u34},{u34 * 150},{u5 // 40 if u5 else 0},{u5},{u5 * 120}")]
        w(ROOT / "bps" / f"st{y}a.txt", "\n".join(lines) + "\n")


def pep() -> None:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "CO-EST2025-HU"
    ws.append(["table with row headers in column A and column headers in rows 3 through 4 (leading dots indicate sub-parts)"])
    ws.append(["Annual Estimates of Housing Units for Counties in the United States: April 1, 2020 to July 1, 2025"])
    ws.append(["Geographic Area", "April 1, 2020\nEstimates Base", "Housing Unit Estimate (as of July 1)"])
    ws.append([None, None, 2020, 2021, 2022, 2023, 2024, 2025])
    ws.append(["United States", 140498736, 140817690, 142193055, 143831409, 145398445, 146829273, 148260882])
    ws.append([".Belknap County, New Hampshire", 38251, 38302, 38629, 39041, 39394, 39731, 39998])
    for fips, c in COUNTIES.items():
        ws.append([f".{c['name']}, Zetaland", *PEP[fips]])
    save_xlsx(wb, ROOT / "pep" / "CO-EST2025-HU.xlsx")


def acs() -> None:
    bg_rows = {}
    for geoid, pop, _, _ in BLOCK_GROUPS:
        if geoid == "990030002002":
            continue  # no ACS row: exercises the null path
        total = pop // 2
        det = int(total * 0.6)
        bg_rows[geoid] = [total, det, total // 20, total // 20, total // 20, total // 10, total // 10, 0, 0,
                          total - det - 3 * (total // 20) - 2 * (total // 10), 0]

    def line(geo: str, est: list[int]) -> str:
        cells = []
        for v in est:
            cells.append(str(v))
            cells.append(str(max(1, v // 10)))
        return geo + "|" + "|".join(cells)

    def table(name: str, n: int, county_vals, bg_vals=None) -> None:
        header = "GEO_ID|" + "|".join(f"{name.upper()}_{k}{i:03d}" for i in range(1, n + 1) for k in ("E", "M"))
        lines = [header, line("0100000US", [sum(county_vals(f)[i] for f in COUNTIES) for i in range(n)]),
                 line("0500000US33001", [1] * n)]
        for fips in COUNTIES:
            lines.append(line(f"0500000US{fips}", county_vals(fips)))
        if bg_vals is not None:
            for geoid, est in bg_rows.items():
                lines.append(line(f"1500000US{geoid}", bg_vals(est)))
        lines.append(line("1600000US9900100", [v // 2 for v in county_vals("99001")]))
        w(ROOT / "acs" / f"acsdt5y2024-{name}.dat", "\n".join(lines) + "\n")

    c = ACS_COUNTY
    table("b25001", 1, lambda f: [c[f][0]], lambda e: [e[0]])
    table("b25024", 11, lambda f: c[f][:11], lambda e: e)
    table("b25002", 3, lambda f: [c[f][0], c[f][11], c[f][12]])
    table("b25003", 3, lambda f: [c[f][11], c[f][13], c[f][14]])
    table("b25077", 1, lambda f: [c[f][15]])
    table("b25064", 1, lambda f: [c[f][16]])
    geos = ["FILEID|STUSAB|SUMLEVEL|COMPONENT|US|REGION|DIVISION|STATE|COUNTY|COUSUB|PLACE|TRACT|BLKGRP|GEO_ID|NAME",
            "ACSSF|ZZ|050|00||||99|001|||||0500000US99001|Alder County, Zetaland",
            "ACSSF|ZZ|160|00||||99||00100||||1600000US9900100|Alderton city, Zetaland"]
    w(ROOT / "acs" / "Geos20245YR.txt", "\n".join(geos) + "\n")


def fhfa() -> None:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "county"
    ws.append(["HPI for Counties (All-Transactions Index)\nExperimental Indexes Showing Cumulative (Nominal) Annual Appreciation"])
    ws.append([None])
    ws.append(["* These annual county indexes should be considered developmental."])
    ws.append(["Last updated: March 31, 2026."])
    ws.append(["Not Seasonally Adjusted (NSA) "])
    ws.append(["State", "County", "FIPS code", "Year", "Annual Change (%)", "HPI", "HPI with 1990 base", "HPI with 2000 base"])
    ws.append(["NH", "Belknap", "33001", 2025, 5.0, 420.0, 400.0, 300.0])
    for fips, c in COUNTIES.items():
        hpi = 100.0
        for y in range(2014, 2026):
            hpi = round(hpi * (1.05 if fips == "99001" else 1.03), 2)
            cell = "." if (fips == "99003" and y == 2016) else hpi
            ws.append(["ZZ", c["name"].replace(" County", ""), fips if fips == "99001" else int(fips), y, 3.0, cell, None, None])
    save_xlsx(wb, ROOT / "fhfa" / "hpi_at_county.xlsx")


def cenpop() -> None:
    lines = ["﻿STATEFP,COUNTYFP,TRACTCE,BLKGRPCE,POPULATION,LATITUDE,LONGITUDE"]
    for geoid, pop, lat, lon in BLOCK_GROUPS:
        lines.append(f"{geoid[:2]},{geoid[2:5]},{geoid[5:11]},{geoid[11]},{pop},{lat:.6f},{lon:.6f}")
    w(ROOT / "cenpop" / "CenPop2020_Mean_BG99.txt", "\n".join(lines) + "\n")


def aclf() -> None:
    for mm, totals in ACLF.items():
        if mm == "062022":
            header = ("STATE|COUNTY|TRACT|BLOCK|BLOCK_GEOID|TOTAL HOUSING UNITS|TOTAL GROUP QUARTERS|"
                      "TOTAL COLLEGE/UNIVERSITY STUDENT HOUSING")
        elif mm == "072026":
            header = "STATE|COUNTY|TRACT|BLOCK|BLOCK_GEOID|TOTAL_HOUSING_UNITS|TOTAL_GROUP_QUARTERS"
        else:
            header = "STATE|COUNTY|TRACT|BLOCK|BLOCK_GEOID|TOTAL HOUSING UNITS|TOTAL GROUP QUARTERS"
        lines = [header]
        for fips, total in totals.items():
            per_block = [total // 4] * 4
            per_block[0] += total - sum(per_block)
            for i, units in enumerate(per_block):
                tract = f"{(i // 2) + 1:04d}.00"
                block = f"{1000 + i}"
                extra = "|0" if mm == "062022" else ""
                lines.append(f"{fips[:2]}|{fips[2:]}|{tract}|{block}|{fips}{tract.replace('.', '')}{block}|{units}|0{extra}")
        w(ROOT / "aclf" / f"99_Zetaland_AddressBlockCountList_{mm}.txt", "\n".join(lines) + "\n")


def transit() -> None:
    stops = [
        {"stop_id": "LR1", "stop_name": "Alder Center Station", "lat": 44.002, "lon": -100.000,
         "stop_type": "0;3", "location_type": "1", "parent_station": "", "ntd_id": "99001", "download_date": "2026-09-23"},
        {"stop_id": "LR1-P", "stop_name": "Alder Center Platform", "lat": 44.002, "lon": -100.0001,
         "stop_type": "0", "location_type": "0", "parent_station": "LR1", "ntd_id": "99001", "download_date": "2026-09-23"},
        {"stop_id": "B7", "stop_name": "Elm St and 3rd", "lat": 44.0501, "lon": -100.050,
         "stop_type": "3", "location_type": "", "parent_station": "", "ntd_id": "99001", "download_date": "2026-09-23"},
        {"stop_id": "LR1-E", "stop_name": "Oak Station Entrance", "lat": 44.1001, "lon": -100.100,
         "stop_type": "0", "location_type": "2", "parent_station": "LR1", "ntd_id": "99001", "download_date": "2026-09-23"},
        {"stop_id": "F1", "stop_name": "Birch Landing", "lat": 44.6505, "lon": -100.650,
         "stop_type": "4", "location_type": "0", "parent_station": "", "ntd_id": "99002", "download_date": "2026-09-23"},
        {"stop_id": "X", "stop_name": "No coordinates", "lat": None, "lon": None,
         "stop_type": "2", "location_type": "0", "parent_station": "", "ntd_id": "99001", "download_date": "2026-09-23"},
    ]
    payload = {"bbox": [-102.1, 42.55, -98.55, 46.1], "pages": 1, "count": len(stops), "stops": stops}
    w(ROOT / "transit" / "ntm_stops_99.json", json.dumps(payload, separators=(",", ":"), sort_keys=True) + "\n")
    ntd = [{"agency": "Alder Transit", "ntd_id": "99001", "modes": ["LR", "MB"]},
           {"agency": "Birch Ferries", "ntd_id": "99002", "modes": ["FB"]}]
    w(ROOT / "transit" / "ntd_modes_99.json", json.dumps(ntd, indent=1, sort_keys=True) + "\n")


def nzlud() -> None:
    msa_header = ["cbsa10", "cbsaname10", "responses", "min_lot_size", "adu", "parking_median", "parking_mode", "zri_median"]
    rows = [msa_header,
            ["10180", "Abilene, TX Metropolitan Statistical Area", "1", "1", "1", "2", "1", "2.09"],
            ["99900", "Alderton, ZZ Metropolitan Statistical Area", "3", "1", "0.666666667", "1.5", "2", "NA"]]
    out = ROOT / "nzlud" / "nzlud_msa.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8", newline="") as f:
        csv.writer(f, lineterminator="\n").writerows(rows)
    muni = [["GEOID", "statename", "place", "type", "mf_per", "parking_median", "adu", "min_lot_size"],
            ["102956", "AL", "Athens", "City", "0.285714286", "2", "1", "1"],
            ["9900100", "ZZ", "Alderton", "City", "0.5", "1.5", "1", "1"]]
    with open(ROOT / "nzlud" / "nzlud_muni.csv", "w", encoding="utf-8", newline="") as f:
        csv.writer(f, lineterminator="\n").writerows(muni)


def hcd() -> None:
    cols = ["JURIS_NAME", "CNTY_NAME", "YEAR", "PRIOR_APN", "APN", "STREET_ADDRESS", "PROJECT_NAME",
            "JURS_TRACKING_ID", "UNIT_CAT", "TENURE", "NO_ENTITLEMENTS", "BP_ISSUE_DT1", "NO_BUILDING_PERMITS",
            "CO_ISSUE_DT1", "NO_OTHER_FORMS_OF_READINESS", "NOTES"]
    r = [
        # 1. one ADU reported three years running: entitled+permitted 2021, permitted again + completed 2022, completed again 2023
        ["ZETA CITY", "Alder", 2021, "", "001-001-001", "1 Main St", "", "B21-1", "ADU", "Renter", 1, "2021-03-01", 1, "", 0, ""],
        ["ZETA CITY", "Alder", 2022, "", "001-001-001", "1 Main St", "", "B21-1", "ADU", "Renter", 0, "2021-03-01", 1, "2022-06-01", 1, ""],
        ["ZETA CITY", "Alder", 2023, "", "001-001-001", "1 Main St", "", "B21-1", "ADU", "Renter", 0, "", 0, "2022-06-01", 1, ""],
        # 2. no APN, tracked by local id; permit repeated
        ["ZETA CITY", "Alder", 2022, "", "", "2 Side St", "", "T-9", "ADU", "Owner", 0, "2022-04-01", 1, "", 0, ""],
        ["ZETA CITY", "Alder", 2023, "", "", "2 Side St", "", "T-9", "ADU", "Owner", 0, "2022-04-01", 1, "", 0, ""],
        # 3. two ADUs on one lot in the same year: both count
        ["ZETA CITY", "Alder", 2023, "", "002-002-002", "3 Twin Ct", "", "", "ADU", "Renter", 0, "2023-02-01", 1, "", 0, ""],
        ["ZETA CITY", "Alder", 2023, "", "002-002-002", "3 Twin Ct", "", "", "ADU", "Renter", 0, "2023-02-02", 1, "", 0, ""],
        # 4. nothing to key on: kept as unique
        ["ZETA CITY", "Alder", 2024, "", "", "", "", "", "ADU", "Renter", 0, "2024-01-01", 1, "", 0, ""],
        # 5. not an ADU
        ["ZETA CITY", "Alder", 2024, "", "004-004-004", "5 Big Rd", "", "", "SFD", "Owner", 1, "2024-01-01", 1, "", 0, ""],
        # 6. county jurisdiction, permitted then completed
        ["ALDER COUNTY", "Alder", 2024, "", "003-003-003", "6 Farm Ln", "", "", "ADU", "Owner", 0, "2024-05-01", 1, "", 0, ""],
        ["ALDER COUNTY", "Alder", 2025, "", "003-003-003", "6 Farm Ln", "", "", "ADU", "Owner", 0, "", 0, "2025-07-01", 1, ""],
    ]
    out = ROOT / "hcd" / "tablea2.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8", newline="") as f:
        wr = csv.writer(f, lineterminator="\n")
        wr.writerow(cols)
        wr.writerows(r)


def main() -> None:
    for fn in (gazetteer, cbsa, bps, pep, acs, fhfa, cenpop, aclf, transit, nzlud, hcd):
        fn()
    total = sum(p.stat().st_size for p in ROOT.rglob("*") if p.is_file())
    print(f"wrote fixtures under {ROOT} ({total:,} bytes)")


if __name__ == "__main__":
    main()
