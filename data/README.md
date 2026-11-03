# Data

Nothing large is committed. The repository holds **manifests** (what we
downloaded, from where, with a SHA-256 of every file) and **fixtures** (a
35 KB synthetic state for the offline demo and the tests). Everything else is
fetched by script from keyless public sources.

| Folder | Tracked in git? | What is in it |
|---|---|---|
| `data/manifests/*.json` | yes | one file per source: URL, SHA-256, bytes, fetch time (UTC), licence, vintage, notes, for every downloaded file |
| `data/sample/` | yes | the synthetic state `ZZ` in every real file format (`scripts/make_sample_zz.py` regenerates it) |
| `data/raw/` | no (ignored) | the download cache, about 600 MB per four states, mostly the ACS bulk files |
| `data/processed/` | no (ignored) | `{ST}.json` per built state, the engine's input (`docs/methods/schema.md`) |
| `data/DATA_SOURCES.md` | yes | the organizers' curated provider list |

## How to obtain the data

From the repository root with `uv` and `make` installed:

```
make setup            # once: installs the pinned environment
make data STATE=NH    # downloads every input New Hampshire needs and writes data/processed/NH.json
make data STATE=UT    # any USPS code works; national files are downloaded once and reused
make demo             # no network: builds the fixture state ZZ from data/sample
```

`hre fetch --all` downloads the state-specific files for the 50 states and DC;
`hre build --all` builds them. The California ADU table (HCD Table A2, 295 MB)
is separate: `make hcd`. The address-count doubling check that decided whether
that series is used: `make validate-aclf` (see `docs/DATA_PROVENANCE.md`).

Set `DATA_DIR` in `.env` to put the raw cache elsewhere (an external disk, a
shared folder); manifests always stay under `data/manifests/`. An optional
`HRE_CONTACT_EMAIL` is added to the HTTP User-Agent so a host that limits
scripted downloads can reach a person. No API key is needed anywhere.

## Checking that you have the same bytes we used

Every manifest entry has the file's SHA-256. After `hre fetch`, compare:

```
shasum -a 256 data/raw/bps/co2025a.txt
grep -A4 '"bps/co2025a.txt"' data/manifests/bps.json
```

If a source publishes a revision (BPS revises the latest year; HCD refreshes
Table A2), the digests differ and `hre fetch --force` records the new ones.

## Provenance

Source, vintage, licence, cleaning steps and known limits for every dataset:
[docs/DATA_PROVENANCE.md](../docs/DATA_PROVENANCE.md). Field-by-field meaning
of the processed file: [docs/methods/schema.md](../docs/methods/schema.md).
