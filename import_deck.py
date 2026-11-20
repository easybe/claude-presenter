#!/usr/bin/env python3
"""Convert a downloaded Claude Slides deck into deck-data.json for the
Claude Presenter.

The deck folder must hold the files at their served paths:

    <deck>/project/deck.json
    <deck>/project/deck.css            (decks with a "format" key)
    <deck>/project/slides/<id>.html

Usage:

    python3 -I import_deck.py <deck folder> <output.json> [source url]
"""

import html
import json
import re
import sys
from pathlib import Path

ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
ASIDE_RE = re.compile(r"<aside\b[^>]*>(.*?)</aside>\s*", re.S | re.I)
TAG_RE = re.compile(r"<[^>]+>")
BLOB_RE = re.compile(r"""(?:src|poster)=["']/?_blob/""", re.I)


def notes_text(raw):
    """Turn the inner HTML of an <aside> into plain text paragraphs."""
    text = re.sub(r"<br\s*/?>", "\n", raw, flags=re.I)
    text = re.sub(r"</p\s*>", "\n\n", text, flags=re.I)
    text = html.unescape(TAG_RE.sub("", text))
    paragraphs = [" ".join(p.split()) for p in re.split(r"\n\s*\n", text)]
    return "\n\n".join(p for p in paragraphs if p)


def split_slide(source):
    """Return the slide HTML without its notes, and the notes text."""
    asides = list(ASIDE_RE.finditer(source))
    if not asides:
        return source.strip(), ""
    last = asides[-1]
    body = source[: last.start()] + source[last.end():]
    return body.strip(), notes_text(last.group(1))


def main(argv):
    if len(argv) not in (3, 4):
        sys.exit(__doc__)
    root = Path(argv[1]) / "project"
    out = Path(argv[2])
    source_url = argv[3] if len(argv) == 4 else ""

    index = json.loads((root / "deck.json").read_text(encoding="utf-8"))
    css_path = root / "deck.css"
    css = css_path.read_text(encoding="utf-8") if css_path.exists() else ""

    slide_dir = root / "slides"
    order = [i for i in index.get("order", []) if ID_RE.match(i)]
    present = sorted(p.stem for p in slide_dir.glob("*.html") if ID_RE.match(p.stem))
    # A slide file that the order leaves out shows last, as in Slides.
    ids = [i for i in order if i in present] + [i for i in present if i not in order]

    slides = []
    for slide_id in ids:
        raw = (slide_dir / f"{slide_id}.html").read_text(encoding="utf-8")
        if re.search(r"<section\b[^>]*\bhidden\b", raw, re.I):
            continue
        body, notes = split_slide(raw)
        if BLOB_RE.search(body):
            print(f"warning: slide {slide_id} uses uploaded images; "
                  "copy them into the reader and rewrite their src",
                  file=sys.stderr)
        slides.append({"id": slide_id, "html": body, "notes": notes})

    faces = []
    for face in index.get("faces", {}).values():
        href = face.get("href", "")
        if href.startswith("https://fonts.googleapis.com/css2?") and href not in faces:
            faces.append(href)

    data = {
        "title": index.get("title") or "Untitled deck",
        "source": source_url,
        "size": index.get("size", "16:9"),
        "css": css,
        "faces": faces,
        "slides": slides,
    }
    out.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n",
                   encoding="utf-8")
    with_notes = sum(1 for s in slides if s["notes"])
    print(f"{out}: {len(slides)} slides, {with_notes} with notes")


if __name__ == "__main__":
    main(sys.argv)
