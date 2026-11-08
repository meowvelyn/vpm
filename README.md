# Evelyn's VPM Packages

VPM package listing for [Avatar Toolbox](https://github.com/meowvelyn/toolbox).

[Add to VRChat Creator Companion](https://meowvelyn.github.io/vpm/)

Repository URL: `https://meowvelyn.github.io/vpm/index.json`

## Hosting

Use a public repository and enable GitHub Pages with **GitHub Actions** as the
build source in Settings → Pages. The workflow publishes `index.json` and an
installation page whenever `main` changes, on manual dispatch, and hourly.
The hourly run picks up new Toolbox releases without a cross-repository token.
GitHub may delay scheduled runs and disables schedules after 60 days without
repository activity in public repositories; a manual run re-enables the schedule.

The listing identity and package repository are configured in `source.json`.
This repository was created from VRChat's package listing template. Its original
`Website/` assets remain available for future customization. The deployment uses
the Python generator's installation page and listing, rebuilding all versions
on each run so previously published versions remain available.

The listing includes stable `vX.Y.Z` releases with a matching
`net.lynuwu.toolbox-X.Y.Z.zip` asset. It checks each package name, version and
download URL and computes its SHA-256 hash. A malformed stable release fails
the build, preserving the previously deployed listing.

## Local build

Requires Python 3.12 or newer and access to GitHub:

```powershell
python scripts/build_listing.py
```

The result is written to `_site/`. An optional `GITHUB_TOKEN` environment
variable authenticates GitHub API reads; public release ZIPs are downloaded
without forwarding that token.
