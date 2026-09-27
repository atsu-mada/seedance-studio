#!/usr/bin/env python3
"""Small, dependency-free validators for the Seedance HTML knowledge base.

The package keeps the user-invocable entry point short. The HTML documents are
the registered knowledge surface; this module loads and validates that surface.
"""
from __future__ import annotations

import argparse
import json
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urldefrag, urlparse


MAP_NAME = "data/knowledge-map.json"
HTML_SUFFIX = ".html"
TOPIC_KEYS = {"id", "path", "anchor", "legacy_sections", "source_refs", "status"}
MAP_KEYS = {"schema_version", "skill_name", "topics"}


class TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.in_pre = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"br", "hr", "p", "div", "li", "tr", "h1", "h2", "h3", "h4", "h5", "h6"}:
            self.parts.append("\n")
        if tag == "pre":
            self.in_pre = True

    def handle_endtag(self, tag: str) -> None:
        if tag == "pre":
            self.in_pre = False
        if tag in {"p", "div", "li", "tr", "h1", "h2", "h3", "h4", "h5", "h6"}:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        self.parts.append(data)

    def text(self) -> str:
        return re.sub(r"\n{3,}", "\n\n", "".join(self.parts)).strip()


class DocumentParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.attrs: dict[str, dict[str, str]] = {}
        self.links: list[tuple[str, str, str]] = []
        self.resources: list[tuple[str, str]] = []
        self.ids: set[str] = set()
        self.duplicate_ids: set[str] = set()
        self.code_blocks: list[str] = []
        self._tag_stack: list[str] = []
        self._code: list[str] | None = None
        self._current_link: tuple[str, str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key: value or "" for key, value in attrs}
        self.attrs[tag] = values
        if "id" in values and values["id"]:
            identifier = values["id"]
            if identifier in self.ids:
                self.duplicate_ids.add(identifier)
            self.ids.add(identifier)
        if tag == "link":
            self.resources.append((tag, values.get("href", "")))
        elif tag == "img":
            self.resources.append((tag, values.get("src", "")))
        if tag == "a":
            self._current_link = (values.get("href", ""), "")
        if tag == "code" and self._tag_stack and self._tag_stack[-1] == "pre":
            self._code = []
        self._tag_stack.append(tag)

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self._current_link:
            href, label = self._current_link
            self.links.append((href, label, "a"))
            self._current_link = None
        if tag == "code" and self._code is not None:
            self.code_blocks.append("".join(self._code))
            self._code = None
        if self._tag_stack:
            self._tag_stack.pop()

    def handle_data(self, data: str) -> None:
        if self._current_link:
            href, label = self._current_link
            self._current_link = (href, label + data)
        if self._code is not None:
            self._code.append(data)


def parse_html(path: Path) -> tuple[str, DocumentParser, TextExtractor]:
    source = path.read_text(encoding="utf-8")
    parser = DocumentParser()
    parser.feed(source)
    extractor = TextExtractor()
    extractor.feed(source)
    return source, parser, extractor


def load_knowledge_map(root: Path) -> tuple[dict, list[str]]:
    errors: list[str] = []
    path = root / MAP_NAME
    if not path.exists():
        return {}, [f"missing {MAP_NAME}"]
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {}, [f"{MAP_NAME}: invalid JSON: {exc}"]
    if not isinstance(data, dict):
        return {}, [f"{MAP_NAME}: top-level value must be an object"]
    if set(data) != MAP_KEYS:
        errors.append(f"{MAP_NAME}: top-level keys must be {sorted(MAP_KEYS)}")
    if data.get("schema_version") != 1:
        errors.append(f"{MAP_NAME}: schema_version must be 1")
    if data.get("skill_name") != "seedance-studio":
        errors.append(f"{MAP_NAME}: skill_name must be seedance-studio")
    topics = data.get("topics")
    if not isinstance(topics, list) or not topics:
        errors.append(f"{MAP_NAME}: topics must be a non-empty list")
        return {}, errors
    ids: set[str] = set()
    paths: set[str] = set()
    for index, topic in enumerate(topics):
        if not isinstance(topic, dict) or set(topic) != TOPIC_KEYS:
            errors.append(f"{MAP_NAME}: topic {index} keys must be {sorted(TOPIC_KEYS)}")
            continue
        topic_id = topic.get("id")
        rel = topic.get("path")
        valid_topic_id = isinstance(topic_id, str) and bool(topic_id)
        if not valid_topic_id or topic_id in ids:
            errors.append(f"{MAP_NAME}: duplicate or invalid topic id at {index}")
        if valid_topic_id:
            ids.add(topic_id)
        valid_rel = (
            isinstance(rel, str)
            and bool(rel)
            and rel.endswith(HTML_SUFFIX)
            and not Path(rel).is_absolute()
            and ".." not in Path(rel).parts
        )
        if not valid_rel:
            errors.append(f"{MAP_NAME}: invalid topic path at {index}: {rel!r}")
        if valid_rel and rel in paths:
            errors.append(f"{MAP_NAME}: duplicate topic path {rel}")
        if valid_rel:
            paths.add(rel)
        status = topic.get("status")
        if not isinstance(status, str) or status not in {"active", "historical"}:
            errors.append(f"{MAP_NAME}: invalid status for {topic_id}")
        if not isinstance(topic.get("legacy_sections"), list) or not isinstance(topic.get("source_refs"), list):
            errors.append(f"{MAP_NAME}: topic {topic_id} section/source refs must be lists")
        anchor = topic.get("anchor")
        if not isinstance(anchor, str) or not re.fullmatch(r"[a-z0-9][a-z0-9-]*", anchor):
            errors.append(f"{MAP_NAME}: invalid anchor for {topic_id}")
        if valid_rel and not (root / rel).exists():
            errors.append(f"{MAP_NAME}: registered HTML missing: {rel}")
    return (data if not errors else {}), errors


def _external_resource(href: str) -> bool:
    parsed = urlparse(href)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _validate_local_resource(
    root: Path,
    owner: Path,
    owner_rel: str,
    tag: str,
    resource: str,
    errors: list[str],
) -> None:
    if not resource:
        errors.append(f"{owner_rel}: missing local {tag} resource")
        return
    parsed = urlparse(resource)
    if parsed.scheme or parsed.netloc:
        if _external_resource(resource):
            errors.append(f"{owner_rel}: external {tag} resource is forbidden: {resource}")
        else:
            errors.append(f"{owner_rel}: non-local {tag} resource is forbidden: {resource}")
        return
    target, _fragment = urldefrag(resource)
    if not target:
        errors.append(f"{owner_rel}: {tag} resource must target a local file: {resource}")
        return
    target_path = (owner.parent / target).resolve()
    try:
        target_path.relative_to(root)
    except ValueError:
        errors.append(f"{owner_rel}: {tag} resource escapes package: {resource}")
        return
    if not target_path.exists():
        errors.append(f"{owner_rel}: missing local {tag} resource: {resource}")


def validate_registered_html(root: Path) -> list[str]:
    data, errors = load_knowledge_map(root)
    if not data:
        return errors
    topics = data.get("topics", [])
    if not isinstance(topics, list) or not topics:
        return errors
    registered = {topic["path"] for topic in topics if isinstance(topic, dict) and isinstance(topic.get("path"), str)}
    index = root / "references" / "index.html"
    if "references/index.html" not in registered:
        errors.append("knowledge map must register references/index.html")
    css = root / "assets" / "knowledge-base.css"
    if not css.exists():
        errors.append("missing assets/knowledge-base.css")
    references_dir = root / "references"
    if references_dir.exists():
        for candidate in sorted(references_dir.rglob("*.html")):
            rel = candidate.relative_to(root).as_posix()
            if rel not in registered:
                errors.append(f"{rel}: unregistered HTML document")
    for topic in topics:
        if not isinstance(topic, dict) or not isinstance(topic.get("path"), str):
            continue
        rel = topic["path"]
        path = root / rel
        if not path.exists():
            continue
        try:
            source, parser, _ = parse_html(path)
        except UnicodeDecodeError as exc:
            errors.append(f"{rel}: must be UTF-8: {exc}")
            continue
        low = source.lower()
        if "<script" in low or "<iframe" in low or re.search(r"<link[^>]+href=[\"']https?://", low):
            errors.append(f"{rel}: executable or external resource markup is forbidden")
        if not re.search(r"<html\b[^>]*\blang=[\"'][a-z]{2,3}(?:-[a-z]{2})?[\"']", source, re.I):
            errors.append(f"{rel}: missing html lang")
        if not re.search(r"<title>[^<]+</title>", source, re.I):
            errors.append(f"{rel}: missing title")
        main_match = re.search(r"<main\b[^>]*\bid=[\"']([^\"']+)[\"']", source, re.I)
        if not main_match:
            errors.append(f"{rel}: missing main with stable id")
        elif main_match.group(1) != topic.get("anchor"):
            errors.append(f"{rel}: main id does not match map anchor {topic.get('anchor')!r}")
        for duplicate_id in sorted(parser.duplicate_ids):
            errors.append(f"{rel}: duplicate HTML id `{duplicate_id}`")
        for tag, resource in parser.resources:
            _validate_local_resource(root, path, rel, tag, resource, errors)
        for href, _label, _kind in parser.links:
            if not href or href.startswith("mailto:") or _external_resource(href):
                continue
            target, fragment = urldefrag(href)
            if target.startswith("#") or not target:
                if fragment and fragment not in parser.ids:
                    errors.append(f"{rel}: missing local fragment #{fragment}")
                continue
            target_path = (path.parent / target).resolve()
            try:
                target_rel = target_path.relative_to(root).as_posix()
            except ValueError:
                errors.append(f"{rel}: link escapes package: {href}")
                continue
            if not target_path.exists():
                errors.append(f"{rel}: broken link: {href}")
            if fragment and target_path.exists():
                _, target_parser, _ = parse_html(target_path)
                if fragment not in target_parser.ids:
                    errors.append(f"{rel}: broken fragment {href}")
            if target_rel.endswith(".html") and target_rel not in registered:
                errors.append(f"{rel}: HTML link is not registered in knowledge map: {target_rel}")
    if index.exists():
        source, parser, _ = parse_html(index)
        for rel in sorted(registered):
            if rel == "references/index.html":
                continue
            expected = Path(rel)
            if not any(href.split("#", 1)[0] == str(Path(".") / expected).replace("./", "") for href, _label, _kind in parser.links):
                # Index links are relative to references/, so compare the resolved path.
                if not any((index.parent / urldefrag(href)[0]).resolve() == (root / rel).resolve() for href, _label, _kind in parser.links):
                    errors.append(f"references/index.html: missing link to {rel}")
    return errors


def visible_text(path: Path) -> str:
    _source, _parser, extractor = parse_html(path)
    return extractor.text()


def html_table_rows(path: Path) -> list[list[str]]:
    source = path.read_text(encoding="utf-8")
    rows: list[list[str]] = []
    for row in re.findall(r"<tr>(.*?)</tr>", source, flags=re.I | re.S):
        cells = re.findall(r"<(?:th|td)\b[^>]*>(.*?)</(?:th|td)>", row, flags=re.I | re.S)
        if cells:
            rows.append([TextExtractorText(cell) for cell in cells])
    return rows


def TextExtractorText(fragment: str) -> str:
    parser = TextExtractor()
    parser.feed(fragment)
    return re.sub(r"\s+", " ", parser.text()).strip()


def registered_text(root: Path) -> str:
    data, errors = load_knowledge_map(root)
    if errors:
        raise ValueError("; ".join(errors))
    return "\n".join(visible_text(root / topic["path"]) for topic in data["topics"])


def cli() -> int:
    parser = argparse.ArgumentParser(description="Validate the registered Seedance HTML knowledge surface.")
    parser.add_argument("root", nargs="?", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    errors = validate_registered_html(args.root.resolve())
    if errors:
        print("Knowledge HTML errors:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Registered Seedance HTML knowledge surface passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(cli())
