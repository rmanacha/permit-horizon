# NH GRANIT Parcel Mosaic: may we publish county counts?

Status (2026-11-03): **awaiting an answer; New Hampshire stays on the ACS count until one arrives.**

## Why we ask

The New Hampshire adapter (`src/hre/adapters/nh.py`) would count parcels coded "11 Single Family
Home" in the Parcel Mosaic CAMA table, one total per county, using a grouped count query that
returns ten numbers and no parcel rows. The table carries a `Name` field and street addresses; the
query never requests them and nothing is written to disk but the ten counts.

The service states no licence. Its only terms are a disclaimer: the data "are for
estimation/planning purposes only and are not intended for legal use" (service item description,
`https://nhgeodata.unh.edu/nhgeodata/rest/services/CAD/ParcelMosaic/MapServer`; copyright text
"NHDRA, Axiomatic, Inc."). Publishing derived county counts in a public repository may or may not
be within that. The data belong to the NH Department of Revenue Administration; GRANIT serves them.

## Draft email for Rishabh to send

To: the GRANIT contact on https://granit.unh.edu (Contact page). Cc nobody.
Subject: Parcel Mosaic: publishing county-level counts of single-family parcels

> Hi,
>
> I'm building Permit Horizon, an open-source tool that estimates how state housing reforms
> would change home building (https://github.com/rmanacha/permit-horizon, Apache-2.0). It's our
> team's entry in the Housing Data and Technology Innovation Challenge.
>
> We'd like to use the NH Parcel Mosaic CAMA table for one number per county: the count of
> parcels with state land use code 11 (Single Family Home). We'd get it with a grouped count query
> on the service, so we never download parcel records, owner names or addresses. The ten county
> counts would be published in our repository and on the tool's website, with GRANIT and the
> Department of Revenue Administration credited as the source.
>
> Is that use OK under the Parcel Mosaic's terms? If it needs a different credit line, or the
> Department of Revenue Administration's permission, just let me know who to ask.
>
> Thanks so much,
> Rishabh Manacha
> Community Solutions

## Reply

(none yet; paste the reply here, with its date, and update the status line above)

## What happens next

- **If GRANIT says yes:** set `enabled: true` in `src/hre/adapters/rules/nh.yaml`, run
  `uv run hre build --state NH`, and the tolerance rule decides county by county (decision 39).
- **If no, or no answer by the end of Phase 5:** New Hampshire keeps the ACS detached count in every
  county, and `docs/methods/adapters.md` says why.
