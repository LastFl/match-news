#!/usr/bin/env python3
"""Rewrite relative internal href/src in generated HTML to absolute /match-news/ paths.

Relative links + Cloudflare Pages' SPA-style fallback let crawlers build endlessly nested
URLs (/match-news/matches/x/serie-a-.../matches/...). Absolute links avoid that.
Leaves absolute URLs, protocol-relative, #anchors, mailto:/tel:/data:/javascript: untouched.
Idempotent. Usage: python3 scripts/absolutize_internal_links.py [root]
"""
import posixpath, re, sys
from pathlib import Path

PREFIX = "/match-news/"
ATTR_RE = re.compile(r'(\b(?:href|src)\s*=\s*)(["\'])([^"\']*)\2')
SKIP_RE = re.compile(r'^(?:[a-zA-Z][a-zA-Z0-9+.-]*:|//|#|/|$)')


def absolutize(value: str, page_dir: str) -> str:
    if SKIP_RE.match(value):
        return value
    path, sep, frag = value.partition("#")
    path, qsep, query = path.partition("?")
    trailing = path.endswith("/") or path in ("", ".", "..") or path.endswith("/..") or path.endswith("/.")
    resolved = posixpath.normpath(posixpath.join(page_dir, path)) if path else page_dir
    if not resolved.startswith(PREFIX.rstrip("/")):
        resolved = PREFIX.rstrip("/")  # never escape above the site root
    if trailing and not resolved.endswith("/"):
        resolved += "/"
    return resolved + (qsep + query if qsep else "") + (sep + frag if sep else "")


def process(root: Path) -> int:
    changed = 0
    for f in sorted(root.rglob("*.html")):
        if ".git" in f.parts:
            continue
        rel_dir = f.parent.relative_to(root).as_posix()
        page_dir = PREFIX + ("" if rel_dir == "." else rel_dir + "/")
        text = f.read_text(encoding="utf-8")
        new = ATTR_RE.sub(lambda m: m.group(1) + m.group(2) + absolutize(m.group(3), page_dir) + m.group(2), text)
        if new != text:
            f.write_text(new, encoding="utf-8")
            changed += 1
    return changed


if __name__ == "__main__":
    root = Path(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).resolve().parents[1])
    print(f"rewrote {process(root)} files")
