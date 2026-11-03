# Usability check: four questions, answered cold

Purpose: the challenge scores Usability on interface clarity, ease of comparing scenarios, clear
labels and plain-language terms. The test is whether someone who has never seen the site can
answer four questions from it alone. Status: **form ready; not yet run** (an open item for
Phase 6 if it is not done before then).

## How to run it (about 15 minutes)

1. Pick a tester who has not seen Permit Horizon: a teammate, a policy colleague or a friend
   who reads the news. No housing expertise needed. Do not explain the tool first.
2. Open https://rmanacha.github.io/permit-horizon/ (or `make run` and http://localhost:8080) and
   choose the tester's own state, or New Hampshire.
3. Read each question aloud, one at a time. Let them click anywhere. Do not answer for them; if
   they ask a question, write it down and say "what would you look for?".
4. Write their answer as close to their words as you can, the time it took, and where they got
   stuck (the friction column). Stop a question at 4 minutes.
5. Afterwards, list the three biggest friction points; those are the fixes.

## The four questions

1. **What does this tool estimate?** (Looking for: building permits over 2026-2030 for one state,
   under five reforms, compared with no change.)
2. **What does it assume?** (Looking for: any of the named assumptions, the low / middle / high
   sets, where they come from, or that current law decides how much is new.)
3. **For one reform you pick: how many more permits than current law, and why that number?**
   (Looking for: the increment over current law in permits, with its range, and one reason, such
   as the assumption that moves it most or the share newly affected.)
4. **What can't it tell you?** (Looking for: which places will build, prices or rents, how likely
   a number is, or another limit the site states.)

## One-page form

Tester (first name or initials only, no other details): ______ Date: ______ State used: ______
Device: laptop / phone. Has the tester seen the site before? no / yes (then pick someone else).

| # | Question | Answer, in their words | Right? (yes / partly / no) | Time | Where they got stuck |
|---|---|---|---|---|---|
| 1 | What does this tool estimate? | | | | |
| 2 | What does it assume? | | | | |
| 3 | One reform: how many more permits than current law, and why? | | | | |
| 4 | What can't it tell you? | | | | |

Questions the tester asked out loud: ____________________________________________

Words or labels they did not understand: _________________________________________

The three fixes, most important first:
1. ______________________________________________
2. ______________________________________________
3. ______________________________________________

## Results

Not yet run. Record each tester's form here (initials, date, state, the four answers and the
friction), then the three fixes and the commits that made them.
