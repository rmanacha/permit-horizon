# What this tool cannot tell you

The plain-language limits shown on the website's Methods and limits page. This file is the
source: `cd web && npm run content` turns it into `web/src/content/limits.json`. Each scenario
also carries its own limits in the results file (`limits[]`), shown on its Scenario detail page.
Each line is `- **Short title**: sentence`.

- **Which places will build**: Results are statewide totals built from county figures; the tool does not say which towns, neighborhoods or lots will see new homes.
- **How likely each number is**: Low, middle and high are named assumption sets, not probabilities. Nobody can say that the middle is twice as likely as the low.
- **A turn in the market**: The baseline range is fitted on history. It held in most past periods, but for forecasts made in 2005-2010, the bust, the actual total fell inside only 56% of the time, and a range drawn at the time would have missed almost every state in 2005-2008.
- **Local rules**: The tool reads state law only, and only where a current-law file exists; local zoning, permitting practice and fee schedules are not modeled. Where no file exists the whole benchmark counts as new, so estimates read high in states whose law already gives part of a reform.
- **Prices, rents and who can afford the homes**: The tool estimates building permits. It does not estimate prices, rents, affordability or who moves in.
- **Permits are not homes**: A permit is not a finished home; about 79 of every 100 apartment permits and nearly all house permits lead to a finished home. Where the page shows homes, it says how the conversion was made.
- **Homes built without a permit count**: The Census permit survey misses homes built where no permit is required and many ADU conversions, so the baseline and the ADU increment are not measured the same way.
- **Reforms together**: The combined package is an illustration. No study has measured the five reforms passed together, so the overlaps are removed by stated rules, not by evidence.
- **Bus rapid transit**: Only rail, streetcar and ferry stops count for transit-oriented density, because the national stop map cannot identify bus rapid transit.
- **Small numbers**: Increments of a few dozen permits are within the uncertainty of the inputs; read them as "about zero", not as a precise count.
- **The data's date**: Every figure reflects the data releases listed on the Assumptions and data page (for example, permits through 2025 and the 2020-2024 American Community Survey).
