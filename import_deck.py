#!/usr/bin/env python3
"""Convert a downloaded Claude Slides deck into deck-data.json for the
Claude Presenter.

The deck folder must hold the files at their served paths:

    <deck>/project/deck.json
    <deck>/project/deck.css            (decks with a "format" key)
    <deck>/project/slides/<id>.html

Usage:

    python3 -I import_deck.py [--language TAG] <deck folder> <output.json> [source url]

The language is a BCP 47 tag such as "de" or "pt-BR". The reader reads the
notes in it. The default is "en".
"""

import argparse
import html
import json
import re
import sys
from pathlib import Path

ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
ASIDE_RE = re.compile(r"<aside\b[^>]*>(.*?)</aside>\s*", re.S | re.I)
TAG_RE = re.compile(r"<[^>]+>")
BLOB_RE = re.compile(r"""(?:src|poster)=["']/?_blob/""", re.I)
LANGUAGE_RE = re.compile(r"^[A-Za-z]{2,3}(-[A-Za-z0-9]{2,8})*$")


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


def language_tag(value):
    """Check that value looks like a BCP 47 language tag."""
    if not LANGUAGE_RE.match(value):
        raise argparse.ArgumentTypeError(f"not a language tag: {value}")
    return value


def main(argv):
    parser = argparse.ArgumentParser(
        description="Convert a downloaded Claude Slides deck into "
                    "deck-data.json for the Claude Presenter.")
    parser.add_argument("-l", "--language", type=language_tag, default="en",
                        help='language of the notes, e.g. "de" (default: en)')
    parser.add_argument("deck", type=Path, help="downloaded deck folder")
    parser.add_argument("output", type=Path, help="deck-data.json to write")
    parser.add_argument("source", nargs="?", default="",
                        help="link to the original deck")
    args = parser.parse_args(argv[1:])
    root = args.deck / "project"
    out = args.output
    source_url = args.source

    index = json.loads((root / "deck.json").read_text(encoding="utf-8"))
    css_path = root / "deck.css"
    css = css_path.read_text(encoding="utf-8") if css_path.exists() else ""

    slide_dir = root / "slides"
    order = [i for i in index.get("order", []) if ID_RE.match(i)]
    present = sorted(p.stem for p in slide_dir.glob("*.html") if ID_RE.match(p.stem))
    # A slide file that the order leaves out shows last, as in Slides.
    ids = [i for i in order if i in present] + [i for i in present if i not in order]

    starts = {}
    for section in index.get("sections", {}).values():
        description = " ".join(str(section.get("description", "")).split())
        if section.get("start") and description:
            starts[section["start"]] = description

    slides = []
    section = None
    for slide_id in ids:
        # A section that starts on a hidden slide starts on the next shown one.
        section = starts.get(slide_id, section)
        raw = (slide_dir / f"{slide_id}.html").read_text(encoding="utf-8")
        if re.search(r"<section\b[^>]*\bhidden\b", raw, re.I):
            continue
        body, notes = split_slide(raw)
        if BLOB_RE.search(body):
            print(f"warning: slide {slide_id} uses uploaded images; "
                  "copy them into the reader and rewrite their src",
                  file=sys.stderr)
        slide = {"id": slide_id, "html": body, "notes": notes}
        if section:
            slide["section"] = section
            section = None
        slides.append(slide)

    faces = []
    for face in index.get("faces", {}).values():
        href = face.get("href", "")
        if href.startswith("https://fonts.googleapis.com/css2?") and href not in faces:
            faces.append(href)

    data = {
        "title": index.get("title") or "Untitled deck",
        "source": source_url,
        "language": args.language,
        "size": index.get("size", "16:9"),
        "css": css,
        "faces": faces,
        "slides": slides,
    }
    out.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n",
                   encoding="utf-8")
    with_notes = sum(1 for s in slides if s["notes"])
    print(f"{out}: {len(slides)} slides, {with_notes} with notes, "
          f"language {args.language}")


if __name__ == "__main__":
    main(sys.argv)
