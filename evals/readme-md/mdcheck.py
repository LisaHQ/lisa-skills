"""Generic Markdown checks for README outcomes: links, anchors, fences, and headings.

Standard library only. problems() lists what is wrong with one file;
new_problems() keeps only the problems its original did not already have, so
an improve-mode outcome is not blamed for the owner's existing mistakes.
Anchors follow GitHub's heading slugs, including -1, -2 suffixes for repeats.
"""
from __future__ import annotations

import re
import unicodedata
from collections import Counter
from pathlib import PurePosixPath
from urllib.parse import unquote

FENCE = re.compile(r"^\s*(`{3,}|~{3,})(.*)$")
QUOTE = re.compile(r"^(?:\s{0,3}>\s?)+")
ATX = re.compile(r"^ {0,3}(#{1,6})(?:[ \t]+(.*?))?(?:[ \t]+#+)?[ \t]*$")
SETEXT = re.compile(r"^ {0,3}(=+|-+)[ \t]*$")
NOT_PARAGRAPH = re.compile(r"^\s*(?:[-*+]\s|\d+[.)]\s|>|#|\||<|$)")
HTML_HEADING = re.compile(r"<h([1-6])\b[^>]*>(.*?)(?:</h\1>|$)", re.I)
HTML_ID = re.compile(r"""<[a-zA-Z][^>]*\s(?:id|name)\s*=\s*["']([^"']+)["']""")
INLINE_CODE = re.compile(r"``.*?``|`[^`]*`")
INLINE_LINK = re.compile(r"""\]\(\s*(<[^>]*>|[^)\s]+)(?:\s+(?:"[^"]*"|'[^']*'|\([^)]*\)))?\s*\)""")
REF_DEF = re.compile(r"^\s{0,3}\[([^\]^][^\]]*)\]:\s*(<[^>]*>|\S+)")
HTML_REF = re.compile(r"""\b(?:src|href)\s*=\s*["']([^"']+)["']""", re.I)
EXTERNAL = re.compile(r"^(?:[a-z][a-z0-9+.-]*:|//)", re.I)


def split_code(text: str) -> tuple[list[str], list[tuple[int, str, bool]]]:
    """Return (one prose line per input line, with code and HTML comments blanked; fences).

    Each fence is (opening line number, info string, closed). Fences inside
    blockquotes and list items count too.
    """
    prose, fences, fence, comment = [], [], None, False
    for number, line in enumerate(text.splitlines(), 1):
        body = QUOTE.sub("", line)
        m = FENCE.match(body)
        if fence is not None:
            if m and m.group(1)[0] == fence[1][0] and len(m.group(1)) >= len(fence[1]) and not m.group(2).strip():
                fences.append((fence[0], fence[2], True))
                fence = None
            prose.append("")
            continue
        if comment:
            prose.append("")
            comment = "-->" not in line
            continue
        if m:
            fence = (number, m.group(1), m.group(2).strip())
            prose.append("")
            continue
        line = re.sub(r"<!--.*?-->", "", line)
        if "<!--" in line:
            line, comment = line.split("<!--", 1)[0], True
        prose.append(line)
    if fence is not None:
        fences.append((fence[0], fence[2], False))
    return prose, fences


def slug(heading: str) -> str:
    """GitHub's anchor for a heading's text."""
    t = re.sub(r"!\[([^\]]*)\]\([^)]*\)", r"\1", heading)
    t = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", t)
    t = re.sub(r"<[^>]+>", "", t)
    t = t.replace("`", "").replace("*", "")
    t = re.sub(r"(?<!\w)_|_(?!\w)", "", t)
    kept = [ch for ch in t.strip().lower()
            if ch in " -" or unicodedata.category(ch)[0] in "LMN" or unicodedata.category(ch) == "Pc"]
    return "".join(kept).replace(" ", "-")


def headings(prose: list[str]) -> tuple[set[str], list[int]]:
    """Return (anchors, heading levels in document order)."""
    seen: Counter = Counter()
    anchors, levels = set(), []

    def add(level: int, text: str) -> None:
        levels.append(level)
        s = slug(text)
        anchors.add(s if seen[s] == 0 else f"{s}-{seen[s]}")
        seen[s] += 1

    for i, line in enumerate(prose):
        m = ATX.match(line)
        if m:
            add(len(m.group(1)), m.group(2) or "")
        elif i and SETEXT.match(line) and prose[i - 1].strip() and not NOT_PARAGRAPH.match(prose[i - 1]) \
                and not ATX.match(prose[i - 1]):
            add(1 if line.strip()[0] == "=" else 2, prose[i - 1].strip())
        else:
            for level, text in HTML_HEADING.findall(INLINE_CODE.sub("", line)):
                add(int(level), text)
        anchors.update(HTML_ID.findall(INLINE_CODE.sub("", line)))
    return anchors, levels


def link_targets(prose: list[str]) -> list[str]:
    out = []
    for line in prose:
        line = INLINE_CODE.sub("", line)
        found = INLINE_LINK.findall(line) + HTML_REF.findall(line)
        m = REF_DEF.match(line)
        if m:
            found.append(m.group(2))
        out += [t[1:-1] if t.startswith("<") and t.endswith(">") else t for t in found]
    return out


def _normalize(base: PurePosixPath, path: str) -> str:
    parts: list[str] = []
    for part in (PurePosixPath(path.lstrip("/")) if path.startswith("/") else base / path).parts:
        if part == "..":
            if parts and parts[-1] != "..":
                parts.pop()
            else:
                parts.append("..")
        elif part not in (".", ""):
            parts.append(part)
    return "/".join(parts)


def problems(text: str, rel: str, exists) -> dict:
    """List the Markdown problems of one file.

    rel is the file's path inside the project; exists(path) says whether a
    project-relative POSIX path exists ("" is the project root).
    """
    prose, fences = split_code(text)
    anchors, levels = headings(prose)
    base = PurePosixPath(rel).parent
    broken_links, broken_anchors = [], []
    for target in link_targets(prose):
        if not target or EXTERNAL.match(target):
            continue
        path, _, frag = target.partition("#")
        path, frag = unquote(path.split("?")[0]), unquote(frag)
        if not path:
            frag = frag.removeprefix("user-content-")
            if frag and frag not in anchors and frag.lower() not in anchors:
                broken_anchors.append("#" + frag)
            continue
        norm = _normalize(base, path)
        if norm.startswith("..") or not exists(norm):
            broken_links.append(target)
    return {
        "broken_links": broken_links,
        "broken_anchors": broken_anchors,
        "unclosed_fences": sum(1 for f in fences if not f[2]),
        "untagged_fences": sum(1 for f in fences if not f[1]),
        "h1_count": levels.count(1),  # Markdown and setext H1s plus <h1> tags
        "skipped_levels": [f"H{a}->H{b}" for a, b in zip(levels, levels[1:]) if b > a + 1],
    }


def new_problems(text: str, original: str, rel: str, exists) -> dict:
    """Problems in text that original (empty in create mode) did not already have."""
    new = problems(text, rel, exists)
    old = problems(original, rel, exists) if original.strip() else None

    def extra(key: str) -> list:
        return list((Counter(new[key]) - Counter(old[key] if old else [])).elements())

    return {
        "broken_links": extra("broken_links"),
        "broken_anchors": extra("broken_anchors"),
        "unclosed_fences": max(0, new["unclosed_fences"] - (old["unclosed_fences"] if old else 0)),
        "untagged_fences": max(0, new["untagged_fences"] - (old["untagged_fences"] if old else 0)),
        "h1": new["h1_count"] != 1 and not (old and old["h1_count"] == new["h1_count"]),
        "skipped_levels": extra("skipped_levels"),
    }
