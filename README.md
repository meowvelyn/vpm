# Evelyn's VPM Packages

VPM package listing for [Avatar Toolbox](https://github.com/meowvelyn/toolbox),
hosted on **Cloudflare Workers Static Assets** with a custom domain.

## Deployment setup

In this repository's **Settings → Secrets and variables → Actions**, configure:

| Type | Name | Value |
| --- | --- | --- |
| Variable | `VPM_PUBLIC_URL` | `https://YOUR-HOSTNAME/index.json` |
| Secret | `CLOUDFLARE_ACCOUNT_ID` | Your Cloudflare account ID |
| Secret | `CLOUDFLARE_API_TOKEN` | A scoped Cloudflare deployment token |

Use Cloudflare's **Edit Cloudflare Workers** API token template, scoped to the
target account and domain's zone. Custom domain deployment also requires zone
read access. Keep the token in GitHub Secrets; do not commit it.

Run **Build and deploy VPM listing to Cloudflare Workers** from the Actions tab.
The workflow also runs when `main` changes and hourly to pick up Toolbox releases.
Until `VPM_PUBLIC_URL` is set, deployment jobs are skipped.
GitHub may delay scheduled runs and disables them after 60 days without activity
in public repositories. Re-enable the schedule if needed.

The build uses the same public URL for `index.json`, the VCC installation link,
and the generated Worker custom domain route. Use a hostname in an active
Cloudflare zone in the deployment account. Deployment creates the domain route,
DNS record, and certificate. If that hostname already serves another application,
resolve that conflict before deploying.

Worker name: `meowvelyn-vpm`. Its static asset directory is `_site/`.
No runtime Worker code, database, or GitHub Pages configuration is required.
The `workers.dev` address remains enabled; to use it as the canonical URL,
set `VPM_PUBLIC_URL` to its full `/index.json` URL instead.

## Package listing

The listing identity and package repository are configured in `source.json`.
Its `url` can hold a default; the `VPM_PUBLIC_URL` environment variable overrides
it. No domain is assumed until one is configured.

The generator includes stable `vX.Y.Z` releases with a matching
`net.lynuwu.toolbox-X.Y.Z.zip` asset. It checks each package name, version and
download URL and computes SHA-256. All versions are rebuilt on every run.
A malformed stable release stops deployment and leaves the existing site intact.
Package ZIPs continue to be hosted on GitHub Releases.

The original VRChat template's `Website/` assets remain available for future
customization; deployment uses the generator's installation page.

## Local build and deployment

Requires Python 3.12 or newer, Node.js, and access to GitHub and Cloudflare:

```powershell
$env:VPM_PUBLIC_URL = 'https://YOUR-HOSTNAME/index.json'
python scripts/build_listing.py
npx wrangler@4 login
npx wrangler@4 deploy --config wrangler.generated.json
```

Generated `_site/` and `wrangler.generated.json` files are ignored by Git.
Optional `GITHUB_TOKEN` authenticates API reads; it is not forwarded to ZIP downloads.
