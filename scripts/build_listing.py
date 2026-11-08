"""Build a VPM listing from public, stable Toolbox GitHub releases."""
import hashlib
import io
import json
import os
from pathlib import Path
import re
import urllib.request
from urllib.parse import urlsplit
import zipfile
from render_website import render_website

REPOSITORY = "meowvelyn/toolbox"
PACKAGE = "net.lynuwu.toolbox"
SOURCE_PATH = Path(__file__).resolve().parents[1] / "source.json"


def public_url(source):
    url = os.environ.get("VPM_PUBLIC_URL", source.get("url", "")).strip()
    parsed = urlsplit(url)
    if (parsed.scheme != "https" or not parsed.hostname or parsed.username
            or parsed.password or parsed.port or parsed.path != "/index.json"
            or parsed.query or parsed.fragment):
        raise ValueError("Set VPM_PUBLIC_URL to https://YOUR-HOSTNAME/index.json")
    return url


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
        "url": public_url(source),
        "packages": {PACKAGE: {"versions": versions}},
    }


def main():
    listing = build_listing(releases())
    output = SOURCE_PATH.parent / "_site"
    output.mkdir(exist_ok=True)
    (output / "index.json").write_text(
        json.dumps(listing, indent=2) + "\n", encoding="utf-8"
    )
    source = json.loads(SOURCE_PATH.read_text(encoding="utf-8"))
    render_website(SOURCE_PATH.parent, output, listing, source)
    (output / "_headers").write_text(
        "/*\n  X-Content-Type-Options: nosniff\n"
        "/index.json\n  Access-Control-Allow-Origin: *\n"
        "  Cache-Control: public, max-age=300\n"
        "  Content-Type: application/json; charset=utf-8\n",
        encoding="utf-8",
    )
    root = SOURCE_PATH.parent
    config = json.loads((root / "wrangler.json").read_text(encoding="utf-8"))
    hostname = urlsplit(listing["url"]).hostname
    config["routes"] = ([] if hostname.endswith(".workers.dev") else [
        {"pattern": hostname, "custom_domain": True}
    ])
    (root / "wrangler.generated.json").write_text(
        json.dumps(config, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Built listing with {len(listing['packages'][PACKAGE]['versions'])} version(s)")


if __name__ == "__main__":
    main()
