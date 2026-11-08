"""Build a VPM listing from public, stable Toolbox GitHub releases."""
import hashlib
import io
import json
import os
from pathlib import Path
import re
import urllib.request
import zipfile

REPOSITORY = "meowvelyn/toolbox"
PACKAGE = "net.lynuwu.toolbox"
LISTING_URL = "https://meowvelyn.github.io/vpm/index.json"
SOURCE_PATH = Path(__file__).resolve().parents[1] / "source.json"


def fetch(url: str, *, api: bool = False) -> bytes:
    headers = {"User-Agent": "meowvelyn-vpm-listing"}
    if api:
        headers["Accept"] = "application/vnd.github+json"
        if os.environ.get("GITHUB_TOKEN"):
            headers["Authorization"] = f"Bearer {os.environ['GITHUB_TOKEN']}"
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read()


def releases():
    page = 1
    while True:
        items = json.loads(fetch(
            f"https://api.github.com/repos/{REPOSITORY}/releases?per_page=100&page={page}",
            api=True,
        ))
        yield from items
        if len(items) < 100:
            break
        page += 1


def build_listing(items, downloader=fetch):
    source = json.loads(SOURCE_PATH.read_text(encoding="utf-8"))
    if source.get("githubRepos") != [REPOSITORY]:
        raise ValueError(f"This generator expects githubRepos to contain only {REPOSITORY}")
    versions = {}
    for release in items:
        if release.get("draft") or release.get("prerelease"):
            continue
        tag = release["tag_name"]
        if not re.fullmatch(r"v\d+\.\d+\.\d+", tag):
            continue
        version = tag[1:]
        expected_name = f"{PACKAGE}-{version}.zip"
        assets = [a for a in release["assets"] if a["name"] == expected_name]
        if len(assets) != 1:
            raise ValueError(f"Release {tag} needs exactly one asset named {expected_name}")
        url = assets[0]["browser_download_url"]
        expected_url = f"https://github.com/{REPOSITORY}/releases/download/{tag}/{expected_name}"
        if url != expected_url:
            raise ValueError(f"Unexpected asset URL for {tag}: {url}")
        data = downloader(url)
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            manifest = json.loads(archive.read("package.json"))
        if manifest.get("name") != PACKAGE or manifest.get("version") != version:
            raise ValueError(f"Package manifest does not match release {tag}")
        if manifest.get("url") != url:
            raise ValueError(f"Package download URL does not match release {tag}")
        manifest["zipSHA256"] = hashlib.sha256(data).hexdigest()
        if version in versions:
            raise ValueError(f"Duplicate version {version}")
        versions[version] = manifest
    return {
        "name": source["name"],
        "id": source["id"],
        "author": source["author"]["name"],
        "url": source["url"],
        "packages": {PACKAGE: {"versions": versions}},
    }


def main():
    listing = build_listing(releases())
    output = Path(__file__).resolve().parents[1] / "_site"
    output.mkdir(exist_ok=True)
    (output / "index.json").write_text(
        json.dumps(listing, indent=2) + "\n", encoding="utf-8"
    )
    (output / "index.html").write_text('''<!doctype html>
<html lang="en">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Evelyn's VPM Packages</title>
<style>
body{font:18px/1.6 system-ui,sans-serif;max-width:48rem;margin:5rem auto;padding:0 1.5rem;background:#161921;color:#e9edf4}
a{color:#a9c5ff}code{overflow-wrap:anywhere}
</style>
<h1>Evelyn's VPM Packages</h1>
<p>Editor tools for VRChat avatars.</p>
<p><a href="vcc://vpm/addRepo?url=https%3A%2F%2Fmeowvelyn.github.io%2Fvpm%2Findex.json">Add to VRChat Creator Companion</a></p>
<p>Or add this repository URL in VCC under Settings → Packages → Add Repository:</p>
<p><code>https://meowvelyn.github.io/vpm/index.json</code></p>
<p><a href="https://github.com/meowvelyn/toolbox">Toolbox source and documentation</a> · <a href="index.json">Package listing JSON</a></p>
</html>
''', encoding="utf-8")
    print(f"Built listing with {len(listing['packages'][PACKAGE]['versions'])} version(s)")


if __name__ == "__main__":
    main()
