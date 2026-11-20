# Claude Presenter

A claude.ai artifact that shows a slide deck and reads each slide's
speaker notes aloud in a Claude voice.

The reader is `index.html`. It shows the deck in `deck-data.json`, which
is published next to it. An artifact page cannot load another artifact
by its link. So the deck is copied into the reader.

## Presenting

Start presentation shows the current slide full screen and reads its
notes. With Auto-advance checked, the reader then moves on to the next
slide.

- Next slide: click, right arrow, Space, Enter or Page Down
- Previous slide: left arrow or Page Up
- Escape: stop the voice, or end the presentation if it is silent

## Importing a Claude Slides deck

1. Read the deck with the Artifact tool (`action: "read"`). Use `paths`
   for `project/deck.json`, `project/deck.css` and every
   `project/slides/<id>.html` named in the `order` of the index.
2. Convert the saved files:

       python3 -I import_deck.py --language en <saved folder> \
           <scratch>/deck-data.json https://claude.ai/artifact/<deck id>

   The language is the BCP 47 tag of the notes, e.g. `de` or `pt-BR`.
   The default is `en`.

3. Publish `index.html` with the `tts` capability and
   `files: {"deck-data.json": "<scratch>/deck-data.json"}`.

The notes come from each slide's `<aside>`. Before the notes, the
reader says the slide title, which is the first `<h1>` or `<h2>`. On the
first slide of a section, it first says the part number and the section
description from the deck's outline. Hidden slides are skipped.
Reveal steps (`.fragment`) are all shown at once. Uploaded images
(`/_blob/<id>`) are not carried over. The script warns about them.

## Where reading aloud works

Chrome and Edge on claude.ai, and the main window of the Claude desktop
app. Elsewhere, the notes are shown as text.

## License

MIT. See `LICENSE`.
