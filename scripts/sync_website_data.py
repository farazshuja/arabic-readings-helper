"""Copy the catalog and its referenced story JSON files into the static website."""
import json
import shutil
from pathlib import Path

root = Path(__file__).resolve().parents[1]
source = root / 'data'
destination = root / 'website/dist/data'
catalog = json.loads((source / 'stories.json').read_text(encoding='utf-8'))
destination.mkdir(parents=True, exist_ok=True)
for record in catalog['stories']:
    story_file = (source / record['file']).resolve()
    if not story_file.is_relative_to(source.resolve()):
        raise ValueError('Story path is outside the data directory')
    output_file = destination / record['file']
    output_file.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(story_file, output_file)
shutil.copyfile(source / 'stories.json', destination / 'stories.json')
print(f"Synced {len(catalog['stories'])} stories.")
