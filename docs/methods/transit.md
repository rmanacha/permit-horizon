# Transit proximity: how "near a major transit stop" is measured

The transit-oriented density scenario applies to homes near rail. This page
says exactly which stops count, where distance is measured from, and what the
method cannot see.

## What counts as a major stop

Source: the Bureau of Transportation Statistics **National Transit Map** stops
layer (keyless ArcGIS FeatureServer, compiled from the GTFS feeds that transit
agencies file with the National Transit Database). Each stop carries the GTFS
route types that serve it, as a semicolon-separated list.

| GTFS route type | Meaning | Counted? |
|---|---|---|
| 0 | tram, streetcar, light rail | yes |
| 1 | subway, metro | yes |
| 2 | rail (commuter, regional, intercity) | yes |
| 4 | ferry | yes |
| 3 | bus | no |
| 11 | trolleybus | no |
| 5, 6, 7, 12 | cable tram, aerial lift, funicular, monorail | no |

A stop is kept only when it is a stop, platform or station (`location_type`
blank, 0 or 1). Station entrances (2), generic nodes (3) and boarding areas (4)
are dropped so a large station is not counted several times at its doors.
Several platforms of one station may remain; this does not change any
distance, because the nearest one is what matters.

Fetch: `hre fetch --state NH` pages the layer 2,000 stops at a time inside a
bounding box drawn 1.5 degrees (about 100 miles) around the state's county
internal points, so stops just across the state line are included: a New
Hampshire block group near the Massachusetts commuter rail is measured to that
station, not to the nearest station inside New Hampshire. The saved file lists
every stop in the box (bus included) with the query URL and SHA-256 in
`data/manifests/transit.json`; the rail/streetcar/ferry filter runs at build time.

Cross-check: the National Transit Database annual service file (Socrata,
keyless) lists which agencies in the state report rail or ferry modes. For
Utah it names the Utah Transit Authority's light rail (LR) and commuter rail
(CR); the build then finds its TRAX and FrontRunner stations. For New
Hampshire no agency reports a rail mode; the three rail stops inside the state
(Dover, Durham, Exeter) belong to Amtrak's Downeaster, which appears in the
National Transit Map through the Northern New England Passenger Rail Authority feed.

## Where distance is measured from

From each block group's **2020 center of population** (the mean location of its
residents, published by the Census Bureau as a plain CSV) to the nearest major
stop, as a great-circle distance in statute miles (haversine formula, earth
radius 3,958.76 miles, computed in numpy). The result is stored per block
group as `dist_major_stop_miles`, with `near_transit_half_mile` (0.5 miles or
less) and `near_transit_quarter_mile` (0.25 or less).

Why the center of population and not the block-group boundary or centroid: a
rural block group can be twenty square miles with everyone living in one
corner; the center of population is where the people are, and the half-mile
test in the source studies (Kestelman 2025 for Los Angeles; Stacy et al. 2023)
is about people's homes, not land. Using a point rather than a polygon also
removes any shapefile dependency (decision 36).

The exposure for the scenario is the sum of `housing_units` (ACS 2020-2024)
over block groups within half a mile. For New Hampshire the build finds eight
such block groups holding 6,371 homes, the same figure Adam Ruege's
independent build reached, which is a useful check that two implementations
of the same definition agree.

## Limitations

- **Bus rapid transit is invisible.** GTFS gives BRT the bus route type (3), so
  a frequent BRT line with stations does not count. States whose transit
  investment is BRT (several Arizona and Utah corridors) are under-measured.
  No open national source distinguishes BRT; if a state supplies a list of BRT
  stations, it can be appended to the stops file before the build.
- **Frequency is unknown.** The National Transit Map holds stops and routes,
  not schedules, so "major" cannot mean "frequent"; a once-a-day commuter
  stop counts the same as a subway station. Rail is used as the proxy for
  frequent, permanent service.
- **Planned lines are not included.** Only stops in agencies' current GTFS
  feeds appear; a line under construction counts only after it opens.
- **A whole block group is in or out.** Homes are assigned by the center of
  population; a block group whose center sits 0.6 miles from a station has no
  homes "near transit" even if a third of its houses are closer. Over a state
  the errors in both directions roughly offset; for one neighbourhood they do not.
- **Vintage.** Stops are as compiled by BTS on the date in the manifest
  (feeds downloaded September 2026); block groups and centers of population
  are 2020 Census geography; housing counts are 2020-2024 ACS.
