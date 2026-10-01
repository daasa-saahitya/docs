#!/usr/bin/env python3
"""
YAML alignment and metadata inference for lyrics files.

Two jobs:
1. Normalise every lyrics YAML into one canonical, valid-indentation form.
2. Fill in category / on-who / types metadata from the folder path and title,
   so filtering works before the metadata is hand-written.
"""

import re
import sys
import yaml
from pathlib import Path

# ── Controlled vocabularies ──────────────────────────────────────────────

CATEGORIES = [
    'Dasara Pada',
    'Sampradaya Haadu',
    'Suladi',
    'Stuti',
    'Stotra',
    'Gadya',
    'Kavya',
    'Kathe',
]

TYPES = [
    'Aavahana',
    'Aagamana',
    'Namaskaara',
    'Pooje',
    'Aarati',
    'Kathe',
    'Vairagya',
    'Parihara',
]

ON_WHO = ['Devaru', 'Devi', 'Yatigalu', 'Dasaru']

# 'on' alone would be parsed by YAML 1.1 as the boolean true, so the key is explicit.
ON_KEY = 'on_who'

PATH_CATEGORY = {
    'devara nama': 'Dasara Pada',
    'gurugalu nama': 'Dasara Pada',
    'suladigalu': 'Suladi',
    'stutigalu': 'Stuti',
    'stotragalu': 'Stotra',
    'kavyagalu': 'Kavya',
    'gatagal': 'Gadya',
    'vishesha dinagalu': 'Sampradaya Haadu',
}

PATH_ON_WHO = {
    'devara nama': 'Devaru',
    'gurugalu nama': 'Yatigalu',
    'suladigalu/devaru': 'Devaru',
    'suladigalu/devi': 'Devi',
    'suladigalu/gurugalu': 'Yatigalu',
    'suladigalu/prarthanagalu': 'Devaru',
    'vishesha dinagalu/varamahalakshmi': 'Devi',
    'vishesha dinagalu/gowri tritiya': 'Devi',
    'vishesha dinagalu/managala gowri': 'Devi',
    'vishesha dinagalu/deevige amavasya': 'Devi',
    'vishesha dinagalu/naga panchami': 'Devi',
    'vishesha dinagalu/krishnaashtami': 'Devaru',
    'vishesha dinagalu/ganesha chaturthi': 'Devaru',
}

TYPE_KEYWORDS = [
    ('aarati', 'Aarati'),
    ('arati', 'Aarati'),
    ('hasege', 'Aarati'),
    ('namaskaara', 'Namaskaara'),
    ('namaskara', 'Namaskaara'),
    ('aavahana', 'Aavahana'),
    ('avahana', 'Aavahana'),
    ('aagamana', 'Aagamana'),
    ('agamina', 'Aagamana'),
    ('naivedya', 'Pooje'),
    ('poojipa', 'Pooje'),
    ('pooja', 'Pooje'),
    ('pooje', 'Pooje'),
    ('vairagya', 'Vairagya'),
    ('parihara', 'Parihara'),
    ('kathe', 'Kathe'),
]

# ── Canonical emission ───────────────────────────────────────────────────

TOP_ORDER = [
    'title_kn', 'author_kn', 'category', ON_KEY, 'types',
    'raga_kn', 'tala_kn', 'ankita_kn', 'verses',
]

VERSE_ORDER = ['type', 'number', 'subtitle_kn', 'kn']

RESERVED = {
    'null', 'true', 'false', 'yes', 'no', 'on', 'off', '~',
    'y', 'n', 'none',
}

NUMERIC = re.compile(r'^[-+]?(\d[\d_]*\.?[\d_]*|\.\d+)([eE][-+]?\d+)?$')


def scalar(value):
    """Render a Python scalar as a single-line, always-valid YAML scalar."""
    if value is None:
        return "''"
    if isinstance(value, bool):
        return 'true' if value else 'false'
    if isinstance(value, (int, float)):
        return str(value)

    text = str(value)
    if text == '':
        return "''"

    quote = (
        text[0] in '-?:,[]{}#&*!|>%@`"\'' or text[0] == ' '
        or text[-1] == ' '
        or ': ' in text
        or ' #' in text
        or text.endswith(':')
        or text.lower() in RESERVED
        or bool(NUMERIC.match(text))
    )
    if quote:
        return "'" + text.replace("'", "''") + "'"
    return text


def block_scalar(text, indent):
    """Render a multi-line string as a valid literal block scalar."""
    pad = ' ' * indent
    lines = [line.rstrip() for line in str(text).strip().split('\n')]
    while lines and not lines[-1]:
        lines.pop()

    header = '|'
    if lines and lines[0][:1] == ' ':
        header += str(indent)

    out = [header]
    for line in lines:
        out.append(f'{pad}{line}' if line else '')
    return '\n'.join(out)


def emit_list(key, values, indent):
    """Render a YAML sequence under `key` at the given indent."""
    pad = ' ' * indent
    return '\n'.join(f'{pad}- {scalar(v)}' for v in values)


# ── Normalisation ────────────────────────────────────────────────────────

def as_list(value):
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return [str(v).strip() for v in value if str(v).strip()]
    text = str(value).strip()
    return [text] if text else []


def as_text(value):
    if value is None:
        return ''
    if isinstance(value, (list, tuple)):
        return '\n'.join(str(v) for v in value)
    return str(value).strip()


def match_value(candidate, vocabulary):
    """Snap a loosely-written value onto the controlled vocabulary."""
    key = candidate.strip().lower()
    if not key:
        return ''
    for option in vocabulary:
        if key == option.lower():
            return option
    return candidate.strip()


def infer_metadata(rel_path, data):
    """Derive category / on-who / types from location and title."""
    parts = [p.lower() for p in rel_path.parts]
    folder = '/'.join(parts[:-1])
    stem = rel_path.stem.lower()

    haystack = ' '.join([
        stem,
        as_text(data.get('title_kn')).lower(),
        as_text(data.get('title_en')).lower(),
    ])

    category = ''
    for key, value in PATH_CATEGORY.items():
        if folder == key or folder.startswith(key + '/'):
            category = value
            break

    on_who = PATH_ON_WHO.get(folder, '')
    if not on_who:
        for key, value in PATH_ON_WHO.items():
            if folder.startswith(key + '/'):
                on_who = value
                break

    types = []
    for keyword, value in TYPE_KEYWORDS:
        if keyword in haystack and value not in types:
            types.append(value)
    types.sort(key=TYPES.index)

    return category, on_who, types


def normalise(data, rel_path=None):
    """Return an ordered, metadata-complete dict ready for emission."""
    data = dict(data or {})
    verses = [dict(v) for v in (data.get('verses') or [])]

    # Accept the loose spellings a hand-written file may already use.
    legacy_on = data.get('on', data.get(True))
    given_category = as_list(data.get('category'))
    given_on = as_list(legacy_on)
    given_types = as_list(data.get('types'))

    inferred_category, inferred_on, inferred_types = (
        infer_metadata(rel_path, data) if rel_path is not None else ('', '', [])
    )

    def ordered(values, vocabulary):
        seen, out = set(), []
        for value in values:
            snapped = match_value(value, vocabulary)
            if snapped and snapped.lower() not in seen:
                seen.add(snapped.lower())
                out.append(snapped)
        return out

    out = {}
    out['title_kn'] = as_text(data.get('title_kn'))
    out['author_kn'] = as_text(data.get('author_kn'))
    out['category'] = ordered(given_category or [inferred_category], CATEGORIES)
    out[ON_KEY] = ordered(given_on or [inferred_on], ON_WHO)
    out['types'] = ordered(given_types or inferred_types, TYPES)

    for field in ('raga_kn', 'tala_kn', 'ankita_kn'):
        out[field] = as_text(data.get(field))

    for verse in verses:
        verse['type'] = '' if verse.get('type') in (None, 'None', 'null', '') else as_text(verse.get('type'))
        verse['kn'] = as_text(verse.get('kn'))
        verse['subtitle_kn'] = as_text(verse.get('subtitle_kn'))

    out['verses'] = verses
    return out


def dump(data):
    """Serialise a normalised dict to canonical YAML text."""
    lines = ['# Daasa Saahitya - lyrics (aligned by scripts/align.py)', '']

    for field in ('title_kn', 'author_kn'):
        lines.append(f'{field}: {scalar(data.get(field, ""))}')

    for field in ('category', ON_KEY, 'types'):
        values = data[field]
        if values:
            lines.append(f'{field}:')
            lines.append(emit_list(field, values, 2))
        else:
            lines.append(f'{field}: []')

    for field in ('raga_kn', 'tala_kn', 'ankita_kn'):
        value = data.get(field, '')
        lines.append(f'{field}: {scalar(value)}' if value else f'{field}:')

    lines.append('verses:')
    for verse in data['verses']:
        lines.append(f'  - type: {scalar(verse.get("type", ""))}')
        if verse.get('number') not in (None, ''):
            lines.append(f'    number: {scalar(verse["number"])}')
        if verse.get('subtitle_kn'):
            lines.append(f'    subtitle_kn: {scalar(verse["subtitle_kn"])}')
        if verse.get('kn'):
            lines.append('    kn:')
            lines.append('    ' + block_scalar(verse['kn'], 6))
        for field, value in verse.items():
            if field in VERSE_ORDER or value in (None, '', []):
                continue
            if isinstance(value, str) and '\n' in value:
                lines.append(f'    {field}:')
                lines.append('    ' + block_scalar(value, 6))
            else:
                lines.append(f'    {field}: {scalar(value)}')
        lines.append('')

    return '\n'.join(lines).rstrip() + '\n'


def read(path):
    with open(path, encoding='utf-8') as handle:
        return yaml.safe_load(handle)


def align_file(path, apply=False):
    """Align one file. Returns (changed, message)."""
    original = path.read_text(encoding='utf-8')
    data = yaml.safe_load(original)
    if data is None:
        return False, 'empty file'

    lyrics_root = next(
        (p for p in [path.parent] + list(path.parents) if p.name == 'lyrics'),
        path.parent,
    )
    rel_path = path.relative_to(lyrics_root)

    aligned = dump(normalise(data, rel_path))
    if aligned == original:
        return False, 'already aligned'
    if apply:
        path.write_text(aligned, encoding='utf-8')
    return True, 'aligned'


def main():
    apply = '--apply' in sys.argv
    root = Path(__file__).parent.parent
    lyrics_dir = root / 'lyrics'

    files = sorted(list(lyrics_dir.rglob('*.yml')) + list(lyrics_dir.rglob('*.yaml')))
    changed = 0

    for path in files:
        try:
            was_changed, message = align_file(path, apply=apply)
        except Exception as error:
            print(f'  ERROR {path.relative_to(lyrics_dir)}: {error}', file=sys.stderr)
            continue
        if was_changed:
            changed += 1
            print(f'  {"Aligned" if apply else "Would align"}: {path.relative_to(lyrics_dir)}')
        elif message == 'already aligned':
            print(f'  OK: {path.relative_to(lyrics_dir)}')

    verb = 'Aligned' if apply else 'Would align'
    print(f'\n{verb} {changed} of {len(files)} files.')
    if not apply:
        print("Run with --apply to rewrite the files.")


if __name__ == '__main__':
    main()