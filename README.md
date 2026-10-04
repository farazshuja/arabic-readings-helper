# Arabic Readings Helper

A static Arabic reading website with beginner stories, per-line harakat toggles, copy buttons, and English/Urdu vocabulary cards. Words link to noun singular/plural forms, verb māḍī/muḍāriʿ/maṣdar forms, and Arabic roots. No database or backend is required.

## Website

[Open the reader](https://farazshuja.github.io/arabic-readings-helper/)

Every push to `main` runs `.github/workflows/pages.yml`. The workflow validates the story data, copies the latest catalog and story JSON into the static website, and deploys to GitHub Pages. The repository's Pages publishing source is **GitHub Actions**. No deployment token or manually copied data is needed.

## Local preview

```powershell
python scripts/sync_website_data.py
python -m http.server 4173 --bind 127.0.0.1 --directory website/dist
```

Open `http://127.0.0.1:4173/`. Use Python 3.10 or later. No third-party packages are required to run the website, synchronize data, or validate the supplied JSON.

## Updating content

1. Edit a story JSON in `data/stories/`, or regenerate story #1 with `python scripts/build_story.py`, story #2 with `python scripts/build_yusuf.py`, story #3 with `python scripts/build_nooh.py`, and story #4 with `python scripts/build_hud.py`. Each builder uses its editable vocalized transcription and bilingual lexicon, and updates its catalog entry while preserving other stories.
2. For a new story, add its entry to `data/stories.json` following the existing format.
3. Run `python scripts/validate_story.py` and `python scripts/sync_website_data.py` locally, then preview the changes.
4. Commit and push to `main`; GitHub Actions publishes the changes automatically.

The validator checks every catalog story, including vocabulary coverage, exact line reconstruction, source pages and checksums. It also checks contextual distinctions in Ibrahim, Yusuf, Nuh and Hud. The catalog and every referenced story are copied automatically by the synchronization script.

See [the data contract](data/README.md) and [the website guide](website/README.md).

## Repository contents

- `website/dist/`: HTML, CSS, JavaScript, and static hosting files.
- `data/`: canonical story JSON, catalog, editorial transcription and lexicon.
- `scripts/`: data generation, validation and synchronization utilities.
- `.github/workflows/`: automated Pages deployment.

Source PDFs in `books/`, temporary files, screenshots, deployment archives, and credentials are excluded from Git. PDF files are optional for rebuilding: when absent, the generator preserves the checksum recorded in the existing JSON. If the original PDF is available locally, validation also checks its checksum.
