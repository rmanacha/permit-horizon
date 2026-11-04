# The site tour

Five stops on New Hampshire, about three minutes. This file is the source: `cd web && npm run content`
turns it into `web/src/content/tour.json`, which the site reads, and a test fails when the two differ.
Each stop is a heading in the form `## Title (`target`, page)`, where the target names an element on
that page (`data-tour="..."` in `web/src/`), followed by two or three sentences. A Markdown link in the
text opens another page and closes the tour. The tour explains how to read the tool; it never argues
for a reform, and the result sentences on the cards stay the engine's.

## The baseline (`baseline`, explore)

If nothing changes, New Hampshire issues about 24,250 building permits over 2026-2030: the last three years,
averaged and carried forward. The range beside it, 12,991 to 38,616, is as wide as history says it should be.
In 80% of past five-year periods the actual total landed inside a range this wide; it's a reading of history,
with no probability attached.

## One reform, three layers (`layers`, explore)

The benchmark is what the reform produced where it was measured, moved to New Hampshire, in the source's own
unit. The increment in the blue band is the part that would be new here, in building permits, and the total
adds it to the baseline. Every number carries its unit and its own low and high, so finished homes and
permits never get added together.

## Current law is a dimmer switch (`law-note`, explore)

This note says how much of the reform New Hampshire already has. Its ADU law carries three of the four
benchmark features, so three quarters of the switch is already on and a quarter of the reform would be new.
"Human review pending" means nobody on the team has signed off on this reading of the statute yet; the
Scenario detail page quotes and links it.

## Compare the reforms (`compare`, explore)

This table ranks the five increments, all in permits, so they can be compared. The warning row says where the
order changes between the low, middle and high assumption sets: a ranking that flips isn't one to repeat on
its own. Benchmarks sit in their own units and aren't ranked.

## Every check, including the misses (`ledger`, validation)

This ledger lists every check we ran against real places, misses included. The Austin check was written down
and fingerprinted before the count was fetched: the model said 139 to 1,217 ADU permits a year, Austin issued
117, and the miss stays on the page. The [Methods and limits](#/methods?st=NH) page lists what the tool can't
tell you: which towns will build, prices or rents, or how likely any number is.
