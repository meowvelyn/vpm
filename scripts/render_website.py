"""Render the limited Scriban syntax used by VRChat's HTML listing template.

Supports property values, if/else and for blocks; unknown expressions fail the
build. JavaScript package data is serialized separately as JSON.
"""
import html
import json
from pathlib import Path
import re
import shutil


def render_html(template, context):
    tokens = []
    for part in re.split(r"({{.*?}})", template, flags=re.DOTALL):
        if part.startswith("{{"):
            tokens.extend(("code", item.strip()) for item in
                          part[2:-2].strip().strip("~").strip().split(";")
                          if item.strip())
        else:
            tokens.append(("text", part))

    def parse(position=0):
        nodes = []
        while position < len(tokens):
            kind, value = tokens[position]
            position += 1
            if kind == "text":
                nodes.append(("text", value))
            elif value in ("else", "end"):
                return nodes, position, value
            elif value.startswith("if "):
                yes, position, stop = parse(position)
                no = []
                if stop == "else":
                    no, position, stop = parse(position)
                if stop != "end":
                    raise ValueError("Unclosed template if block")
                nodes.append(("if", value[3:].strip(), yes, no))
            elif value.startswith("for "):
                match = re.fullmatch(r"for (\w+) in ([\w.]+)", value)
                if not match:
                    raise ValueError(f"Unsupported loop: {value}")
                body, position, stop = parse(position)
                if stop != "end":
                    raise ValueError("Unclosed template for block")
                nodes.append(("for", *match.groups(), body))
            else:
                nodes.append(("value", value))
        return nodes, position, None

    def resolve(expression, values):
        if expression.startswith('"'):
            return json.loads(expression)
        if not re.fullmatch(r"[\w.]+", expression):
            raise ValueError(f"Unsupported template expression: {expression}")
        result = values
        for key in expression.split("."):
            result = result.get(key, "") if isinstance(result, dict) else ""
        return result

    def render(nodes, values):
        output = []
        for node in nodes:
            kind = node[0]
            if kind == "text":
                output.append(node[1])
            elif kind == "value":
                value = resolve(node[1], values)
                output.append(html.escape(str(value if value is not None else "")))
            elif kind == "if":
                output.append(render(node[2] if resolve(node[1], values) else node[3], values))
            elif kind == "for":
                for item in resolve(node[2], values):
                    output.append(render(node[3], dict(values, **{node[1]: item})))
        return "".join(output)

    nodes, _, stop = parse()
    if stop:
        raise ValueError(f"Unexpected template {stop}")
    return render(nodes, context)


def render_website(root: Path, output: Path, listing, source):
    website = root / "Website"
    shutil.copytree(website, output, dirs_exist_ok=True)
    packages = []
    client_packages = {}
    for name, package in listing["packages"].items():
        versions = package["versions"]
        if not versions:
            continue
        latest = max(versions, key=lambda value: tuple(map(int, value.split("."))))
        manifest = versions[latest]
        dependencies = manifest.get("vpmDependencies", {})
        author = manifest.get("author") or {}
        if isinstance(author, str):
            author = {"name": author}
        packages.append({
            "Name": name,
            "DisplayName": manifest.get("displayName", name),
            "Description": manifest.get("description", ""),
            "ZipUrl": manifest["url"],
            "Type": ("Avatar" if "com.vrchat.avatars" in dependencies else
                     "World" if "com.vrchat.worlds" in dependencies else "Any"),
        })
        client_packages[name] = {
            "name": name,
            "displayName": manifest.get("displayName", name),
            "description": manifest.get("description", ""),
            "version": latest,
            "author": {"name": author.get("name", ""), "url": author.get("url", "")},
            "dependencies": dependencies,
            "keywords": manifest.get("keywords") or [],
            "license": manifest.get("license", ""),
            "licensesUrl": manifest.get("licensesUrl", ""),
        }
    author = source.get("author") or {}
    info_link = source.get("infoLink") or {}
    context = {
        "listingInfo": {
            "Name": listing["name"], "Url": listing["url"],
            "Description": source.get("description", ""),
            "BannerImage": bool(source.get("bannerUrl")),
            "BannerImageUrl": source.get("bannerUrl", ""),
            "Author": {key.title(): value for key, value in author.items()},
            "InfoLink": {key.title(): value for key, value in info_link.items()},
        },
        "packages": packages,
    }
    page = render_html((website / "index.html").read_text(encoding="utf-8"), context)
    (output / "index.html").write_text(page, encoding="utf-8")
    script = (website / "app.js").read_text(encoding="utf-8")
    script = script.replace("__LISTING_URL_JSON__", json.dumps(listing["url"]))
    script = script.replace("__PACKAGES_JSON__", json.dumps(client_packages))
    (output / "app.js").write_text(script, encoding="utf-8")
