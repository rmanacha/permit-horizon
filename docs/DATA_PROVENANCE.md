# Data Provenance

Document every dataset your tool uses. The code license does **not** relicense data—each dataset carries its own terms, and you are responsible for them. Do not commit raw or large data to the repository; describe how to obtain it here and keep only small samples in `data/sample/`.

# Dataset Inventory

Complete one row per dataset.

| Dataset | Source | Version / vintage | Access date | License / terms | Category |
| ------- | ------ | ----------------- | ----------- | --------------- | -------- |
| [name]  | [org + URL] | [year/release] | [YYYY-MM-DD] | [e.g., public domain, CC BY 4.0] | [public / state-provided / third-party / team-created] |

Categories:

- **Public** — nationally available public datasets (e.g., Census/ACS, BLS).
- **State-provided** — datasets supplied by participating states for the challenge.
- **Third-party** — commercial, nonprofit, academic, or online sources.
- **Team-created** — datasets you built or materially modified.

# Cleaning and Preparation

[For each dataset, describe the cleaning, joining, filtering, or transformation steps you applied, and any assumptions those steps embed.]

# Known Limitations

[Coverage gaps, staleness, geographic mismatches, or quality issues a user should know about.]

# Restricted, Sensitive, or Personal Data

[State whether any dataset involves individuals, households, addresses, facilities, or restricted records. If you used de-identified or aggregated data, describe the method and any re-identification or small-cell risk. Do not use sensitive, confidential, or restricted-use data unless the [Challenge Handbook](https://housingchallenge.turnout.rocks/handbook.html) and the [Official Rules](https://housingchallenge.turnout.rocks/rules.html) expressly permit it and you can document that permission.]
