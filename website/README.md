# Qira’ah — Arabic reading

A dependency-free static website that reads the prepared story JSON. The home screen lists every story in `dist/data/stories.json`. The reader provides chapter navigation, per-line harakat toggles, copying the displayed line, and keyboard-accessible word cards with English and Urdu meanings, noun/verb forms, roots, and attached-word notes.

The complete story is loaded once and cached in browser memory. Vowel toggles and vocabulary cards require no subsequent requests. There is no database or backend. Quran reference links are optional external navigation. Arabic text uses self-hosted Scheherazade New in regular and bold weights, with system font fallbacks. Urdu uses local system fonts. The reader does not depend on a font service. The bundled font license is in `dist/fonts/OFL.txt`.

## Local preview

From the repository root:

```powershell
python -m http.server 4173 --bind 127.0.0.1 --directory website/dist
```

Open `http://127.0.0.1:4173`. Clipboard access works on localhost or HTTPS. Opening `index.html` directly with `file://` does not support the JSON fetches reliably.

## Updating the stories

The original data under the repository's `data/` directory remains the source of truth. After editing or adding a story, update `data/stories.json` with its title, counts, ID, and relative JSON filename, then run:

```powershell
python scripts/sync_website_data.py
```

Story URLs use `#story/<story-id>/<section-id>` so bookmarks and browser Back/Forward work on any static host without rewrite rules. Section IDs and vocabulary references follow the contract in `data/README.md`. Vowel states persist during this browser session's navigation; they are not stored after a reload.

The last successfully opened story and chapter are saved in browser local storage. The home screen offers a “Resume reading” link on later visits while keeping the story library visible. If storage is unavailable or the saved story is no longer in the catalog, the library still works normally.

GitHub Actions deploys `dist/` to GitHub Pages on every push to `main`, after synchronizing data from the canonical `data/` directory. The generated `dist/data/` copy is ignored by Git. All asset and JSON URLs are relative, so the reader works under the GitHub Pages repository path. Keep source PDFs, editable transcription files, scripts, and review notes outside the deployed directory. The Arabic editorial review recommendation still applies before a public release.
