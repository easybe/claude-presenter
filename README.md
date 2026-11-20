# Claude Presenter

A claude.ai artifact that shows a slide deck one slide at a time and
reads each slide's speaker notes aloud in a Claude voice.

The page itself is `index.html`. The deck it shows is a separate file,
`deck-data.json`, published next to it. An artifact page cannot load
another artifact by its link, so a deck gets into the reader by being
copied: Claude reads the deck's files and republishes the reader with a
new `deck-data.json`.

## Presenting

The Start presentation button shows the current slide full screen and
reads its notes. A click on the slide, the right arrow key, Space, Enter
or Page Down moves to the next slide and reads its notes. The left arrow
key and Page Up move back. Escape stops the voice while it is reading.
Otherwise, it ends the presentation.

## Importing a Claude Slides deck

1. Read the deck's files with the Artifact tool (`action: "read"`,
   `paths`: `project/deck.json`, `project/deck.css` and every
   `project/slides/<id>.html` named in the index's `order`).
2. Convert them, pointing at the folder the read saved them in:

       python3 -I import_deck.py <saved folder> <scratch>/deck-data.json \
           https://claude.ai/artifact/<deck id>

3. Republish the reader with `files: {"deck-data.json": "<scratch>/deck-data.json"}`.

The speaker notes are taken from each slide's `<aside>`. Slides marked
`hidden` are skipped. Reveal steps (`.fragment`) are all shown at once,
since nothing advances them.

Slides that use uploaded images (`/_blob/<id>`) need those images copied
into the reader's own asset store, and their `src` rewritten. The import
script warns when a slide has any.

## Where reading aloud works

The reader uses the `tts` artifact capability. It works in Chrome and
Edge on claude.ai and in the main window of the Claude desktop app. In
Safari, Firefox, the mobile apps and the Claude Code artifact pane the
voice controls are hidden and the notes are shown as text only.

## License

MIT. See `LICENSE`.
