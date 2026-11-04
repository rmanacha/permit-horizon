# Current-law review: Utah, New Hampshire, Arizona (for the policy teammate)

Status (2026-11-03): **all 15 records await review**; every card on the website says "Human review
pending" until a person signs. About 45 minutes. You need a browser and the three files:
`src/hre/current_law/UT.yaml`, `NH.yaml`, `AZ.yaml`. The rules are in
`docs/methods/current_law.md` ("Review checklist"); the machine checks have already run (every
quote appears on its page: `docs/evidence/current_law_quotes.md`; coverage reproduces:
`docs/evidence/current_law_coverage.md`).

For each reform below, open the link, then tick the four boxes or write what is wrong.

1. The citation and dates are right (bill, chapter, effective date).
2. Each feature's status is fair: "supported with limits" means the statute requires towns to allow
   it; "differs" means it does not; the limits name what the text leaves out.
3. Who is bound is right (population line, counties, exclusions), and so is the coverage share.
4. The rationale is a sentence you would read to a legislator without wincing.

## Arizona

| Reform | Strength | Link | The one thing to look at hardest |
|---|---|---|---|
| ADU | 0.80 | https://www.azleg.gov/ars/9/00461-18.htm and https://www.azleg.gov/ars/11/00810-01.htm | Size is "supported with limits" (75% of the house or 1,000 sq ft reaches 600 sq ft for houses of 800+); Adam's record said "differs". Coverage 79.9%: 15 cities over 75,000 by the 2020 Census plus unincorporated land, less tribal land. |
| Missing middle | 0.04 | https://www.azleg.gov/ars/9/00462-13.htm | Coverage is an upper bound (single-family lots within a mile of downtown in the 15 largest cities, at most 5.2% of homes). Is two floors (not three) fairly "differs"? |
| Transit density | 0 | https://www.azleg.gov/ars/9/00462-10.htm | No transit-area statute; the commercial-conversion law is not counted. Any 2025-2026 law we missed? |
| Parking | 0 | https://www.azleg.gov/ars/9/00462-13.htm | Only ADU and middle-housing caps; nothing for apartment buildings. |
| Fees | 0 | https://www.azleg.gov/ars/9/00463-05.htm | Regulates development fees; cuts none. |

## Utah

| Reform | Strength | Link | The one thing to look at hardest |
|---|---|---|---|
| ADU | 0.50 | https://le.utah.gov/xcode/Title10/Chapter21/10-21-S303.html, https://le.utah.gov/xcode/Title17/Chapter80/17-80-S303.html, https://le.utah.gov/xcode/Title10/Chapter21/10-21-S304.html | Forms stays "differs" although detached ADUs are required on lots of 11,000 sq ft or more in cities of 10,000+ since October 1, 2026. Size is "supported" because towns may not limit an internal ADU's size relative to the house. |
| Missing middle | 0 | https://le.utah.gov/xcode/Title10/Chapter21/10-21-S201.html | A menu of housing-plan strategies, no mandate. |
| Transit density | 0 | https://le.utah.gov/xcode/Title63N/Chapter23/63N-23-S104.html | Station area plans are required but density is only "may consider"; the gate rule scores it 0 though the geography row is supported. Agree? |
| Parking | 0 | https://le.utah.gov/xcode/Title10/Chapter20/10-20-S618.html | S.B. 181 (2025) limits space size and garage rules, not the number of spaces. |
| Fees | 0 | https://le.utah.gov/xcode/Title11/Chapter36a/11-36a-S202.html | Impact Fees Act regulates; internal ADUs are exempt; no general cut. |

## New Hampshire

| Reform | Strength | Link | The one thing to look at hardest |
|---|---|---|---|
| ADU | 0.75 | https://gc.nh.gov/rsa/html/LXIV/674/674-72.htm and https://gc.nh.gov/rsa/html/LXIV/674/674-73.htm | Unchanged from Phase 2 (decision 62): parking "differs" because towns may require one space. Owner occupancy may still be required. |
| Missing middle | 0 | https://gc.nh.gov/rsa/html/LXIV/674/674-59.htm | Workforce housing "opportunities" are not a right to two to six homes on single-family lots. |
| Transit density | 0 | https://gc.nh.gov/rsa/html/LXIV/674/674-80.htm | Apartments on commercial land (from July 1, 2026) are not tied to transit. |
| Parking | 0.43 (quantified) | https://gc.nh.gov/rsa/html/LXIV/674/674-16.htm | The cap at one space per home already removes the spaces above one that local codes required; check the arithmetic in `strength_arithmetic` (decision 93). |
| Fees | 0 | https://gc.nh.gov/rsa/html/LXIV/674/674-21.htm | Impact fees limited to a proportional share; none cut. |

## Signing

When a reform's four boxes are ticked, edit its block in the state file:

```yaml
    human_review: {status: reviewed, by: "Full Name", date: "2026-11-xx"}
```

Commit with a message such as "Current law review: AZ ADU and missing middle (Full Name)", then
regenerate the bundle (`make results-all export` from the clean checkout) and commit it on its
own. The card then reads "reviewed by Full Name on 2026-11-xx". If you change a status, the tests
will tell you the new strength the rule gives; update `current_strength` and the rationale to match.
