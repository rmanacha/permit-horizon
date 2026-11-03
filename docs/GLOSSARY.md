# Glossary

Plain-language definitions of the terms the Permit Horizon website uses. This file is the
source: `cd web && npm run content` turns it into `web/src/content/glossary.json`, which the
site shows beside each term and on the Methods and limits page, and a test fails when the two
differ. Each line is `- **Term** (`id`): definition`; the id is what the site links to, so keep
ids stable when you edit a definition.

## The three layers and their units

- **Baseline** (`baseline`): The number of building permits a state would issue over 2026-2030 if nothing changes: the average of the last three years (2023-2025) carried forward five years.
- **Range from history** (`band`): The low and high ends around the baseline. In 80% of past five-year periods (every state, 1990-2015) the actual permit total fell inside a range this wide. It describes history, not a probability.
- **Benchmark** (`benchmark`): What the source policy produced where it was measured (a California city's ADUs, Portland's middle housing, Los Angeles near transit), moved to this state's homes and lots, in the source's own unit. It does not subtract what current law already allows.
- **Increment over current law** (`increment`): The part of the benchmark that would be new in this state: the benchmark times the share of homes or lots the reform newly affects, phased in over the years, converted to building permits. This is the number to compare across reforms.
- **Total** (`total`): Baseline plus increment, low with low, middle with middle, high with high.
- **Outcome label** (`outcome-label`): The unit a number is in. Numbers with different labels are never added together or ranked against each other.
- **Permits** (`outcome-permits`): Building permits for new homes, as counted by the Census Building Permits Survey. The headline unit of this tool. A permit is not yet a finished home.
- **Net permits** (`outcome-net-permits`): Permits for new homes minus the homes demolished to make room for them (the unit of the missing-middle evidence).
- **Completed homes** (`outcome-completed-homes`): Homes finished and ready to live in (the unit of the ADU evidence from California).
- **Homes added to the stock** (`outcome-stock-change`): The change in the number of homes in an area, after any losses (the unit of the transit-oriented density studies).
- **Cost-response permits** (`outcome-cost-response-proxy`): Permits estimated from a cost saving and how strongly builders respond to costs, rather than from a place that passed the reform. The parking and fee scenarios use it.
- **Completed-homes equivalent** (`completed-homes-equivalent`): A permit figure multiplied by how many homes get finished per permit. Shown beside ADU permits, because more permits per finished ADU raises permits, not homes.

## Assumptions and cases

- **Assumption set (low, middle, high)** (`assumption-set`): Three named choices for the assumptions that carry a scenario's evidence range. The low-to-high spread is a sensitivity range, not a probability.
- **Register** (`register`): The table of every assumption the model uses, each with its low, middle and high values, its source, the page or table it comes from, and the arithmetic.
- **Register default** (`register-default`): The headline case: the newly affected share comes from the state's current law, with the scenario's phase-in and no delay.
- **User case** (`user-case`): A what-if you choose: 25%, 50% or 100% of homes or lots newly affected, starting after 0, 1 or 2 years.
- **Newly affected share** (`newly-affected-share`): The fraction of the homes or lots in the benchmark whose rules the reform would change, given what the state's law already allows.
- **Current strength** (`current-strength`): How much of the benchmark reform a state's law already provides, from 0 (nothing statewide) to 1 (the same). The newly affected share is 1 minus current strength.
- **Current-law register** (`current-law`): The file for each state and reform that records the statute, a quote, the effective date and a feature-by-feature comparison with the benchmark reform. States without a file are treated as having no statewide law.
- **Human review** (`human-review`): Whether a person has checked a current-law record against the statute. "Pending" means not yet.
- **Delay** (`delay`): Years with no activity before the reform starts producing homes; "starts after the horizon" means nothing within the five years.
- **Phase-in (ramp)** (`ramp`): The share of the full rate reached in each of the five years after a reform takes effect.
- **Tornado** (`tornado`): A chart that moves one assumption at a time from its low to its high value and shows how far the middle result moves. The longest bar is the assumption that matters most.
- **Joint favorable or unfavorable case** (`joint-case`): Every assumption at its most (or least) favorable end at once. An extreme for illustration, not a likely outcome.
- **Exact rescale** (`exact-rescale`): When an assumption multiplies the result, the page recomputes it from the engine's own numbers with the same arithmetic as the engine. A test checks it against the engine to one part in a billion.
- **Interpolated** (`interpolated`): A value between two results the engine computed in advance (at the low, middle and high values), drawn on a straight line between them. Close, not exact; the command line gives the exact value.
- **Combined package** (`combined`): If all five reforms passed together: the five increments added after removing the overlaps (lots near rail count once; parking and fee savings are one cost cut). An illustration; no study has measured the five together.

## Validation and data

- **Backtest** (`backtest`): Rerunning today's baseline rule on past years and comparing it with what was actually permitted.
- **Coverage by period** (`coverage-by-period`): The share of past five-year periods whose actual total fell inside the range, counted separately for calm years, the 2005-2010 bust and the 2011-2015 recovery.
- **Real-time test** (`real-time-test`): Redrawing the range each past year using only the years already known then, and checking it against what happened next.
- **20-year swing range** (`swing-band`): A second way to draw the baseline range, from a teammate's earlier prototype: the last five years of permits stretched by the state's own slowest and fastest five-year stretches of the past 20 years.
- **Validation ledger** (`validation-ledger`): The list of checks of the model against real reforms whose outcomes were written down before the results were looked at.
- **Census housing-unit estimates** (`pep`): The Census Bureau's yearly count of homes by county. Shown as a consistency check beside the forecast, because the estimates are built partly from the same permits.
- **Builder response** (`builder-response`): How many more homes get built over five years for each 1% fall in the cost of building, relative to the price of a new home. The one parameter behind the parking and fee scenarios.
- **Geography check** (`geography-check`): A per-county version of the builder response built from how easily each metro area's housing supply grows. Shown beside the headline as a check: supply-constrained metros respond less.
- **Market adjustment** (`market-adjustment`): Scales a source city's rate up or down by how this county's home values compare with the source city's, within fixed bounds.
- **Home-value tier** (`home-value-tier`): One of five groups of California cities by median home value; each county elsewhere takes the ADU rate of the tier its own median value falls in.
- **Central metropolitan county** (`central-county`): A county that holds the core of a metropolitan area (the federal government's 2023 definition). The missing-middle estimate counts single-family homes in these counties.
- **Major transit stop** (`major-stop`): A rail, streetcar or ferry stop. Bus and bus rapid transit do not count, because the national stop map cannot tell them apart.
- **Grade and confidence** (`grade`): Grade says what kind of evidence an assumption rests on (A measured, B derived, C judgment, R set by the challenge rules or a design choice); confidence says how far it transfers to another state.
- **Locator** (`locator`): The page, table or paragraph in a source where a number comes from.
- **Vintage** (`vintage`): Which release of a dataset was used (for example the 2020-2024 American Community Survey).
- **Build id** (`build-id`): A code joining the commit of the code with a fingerprint of the inputs and the register, so any number can be traced to exactly what produced it.
- **Fixed templates** (`templates`): Every sentence on this site that describes a result is a fixed sentence with the engine's numbers filled in. No language model writes any text.

## The five reforms

- **ADU (accessory dwelling unit)** (`adu`): A second, smaller home on a lot that already has a house: a backyard cottage, a garage apartment or a basement unit.
- **Missing middle** (`missing-middle`): Buildings between a single house and a large apartment block: duplexes, triplexes, fourplexes and townhouses on lots now zoned for one house.
- **Transit-oriented density (TOD)** (`tod`): Allowing more homes near major transit stops.
- **Parking minimum** (`parking-minimum`): A rule requiring a set number of parking spaces for each new home. Removing it lowers the cost of building where builders would otherwise provide fewer spaces.
- **Development and impact fees** (`fees`): Charges a locality levies on new homes. The challenge assumes $50,000 a home in total, cut in half.
