# Evelyn's VPM Packages

VPM package listing for [Avatar Toolbox](https://github.com/meowvelyn/toolbox),
hosted on **Cloudflare Workers Static Assets** and deployed with **Cloudflare Workers Builds**.

## Cloudflare setup

Connect this repository in Cloudflare's **Workers & Pages → Create → Import a repository**
flow. Use the following production build settings:

| Setting | Value |
| --- | --- |
| Repository | `meowvelyn/vpm` |
| Production branch | `main` |
| Worker name | `meowvelyn-vpm` |
| Root directory | Repository root |
| Build command | `python3 scripts/build_listing.py` |
| Deploy command | `npx wrangler@4 deploy --config wrangler.generated.json` |
| Build variable `VPM_PUBLIC_URL` | `https://vpm.YOUR-DOMAIN/index.json` |

Set `VPM_PUBLIC_URL` as a **build variable**, since the URL is embedded in the
static files at build time. Replace `YOUR-DOMAIN` with the real domain represented
by `@` in your DNS settings; `@` itself is not a hostname in this configuration.

Cloudflare Workers Builds supplies its own deployment authentication. No
Cloudflare secrets in GitHub are needed. The Worker name in the dashboard must
match `name` in `wrangler.json`.

The build generates the canonical listing URL, VCC install link, and custom-domain
route from `VPM_PUBLIC_URL`. Use a hostname in an active Cloudflare zone in the
same account. Deployment creates the domain route, DNS record, and certificate.
If the hostname already serves another application, resolve that conflict before
deploying.

Worker name: `meowvelyn-vpm`. Its static asset directory is `_site/`.
The `workers.dev` address remains enabled. No runtime Worker code or database is
required. Disable preview branch builds initially; these settings target production.

## Updating packages

Cloudflare automatically builds when commits are pushed to `main` in this
repository. A new release in the separate `meowvelyn/toolbox` repository does
not trigger that build. After publishing a Toolbox release, trigger a fresh
build of this Worker in Cloudflare to refresh the listing. There is no hourly
GitHub Actions deployment or polling workflow.

## Package listing

The listing identity and package repository are configured in `source.json`.
Its `url` can hold a default; `VPM_PUBLIC_URL` overrides it. No domain is assumed
until one is configured.

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
$env:VPM_PUBLIC_URL = 'https://vpm.YOUR-DOMAIN/index.json'
python scripts/build_listing.py
npx wrangler@4 login
npx wrangler@4 deploy --config wrangler.generated.json
```

Generated `_site/` and `wrangler.generated.json` files are ignored by Git.
Optional `GITHUB_TOKEN` authenticates API reads; it is not forwarded to ZIP downloads.
