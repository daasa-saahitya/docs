#!/usr/bin/env python3
"""
Cleanup script: Remove redundant transliterations from YAML lyrics files.

This script strips all _ta, _hi, _en fields from metadata and verses,
leaving only Kannada text. The build script auto-generates transliterations.

Usage:
    python cleanup.py                    # Dry run (shows what would change)
    python cleanup.py --apply            # Actually modify files
    python cleanup.py --apply --backup   # Modify files and keep .bak backups
"""

import sys
import yaml
from pathlib import Path

# Fix Windows console encoding for Unicode output
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')


def cleanup_yaml_file(yaml_path, apply=False, backup=False):
    """Remove redundant transliteration fields from a YAML file."""
    with open(yaml_path, encoding='utf-8') as f:
        content = f.read()

    data = yaml.safe_load(content)
    if not data:
        return False

    original = content
    modified = False

    # Remove redundant metadata fields (_ta, _hi, _en)
    for field in ['title', 'author', 'raga', 'tala', 'ankita', 'description']:
        for lang in ['ta', 'hi', 'en']:
            key = f'{field}_{lang}'
            if key in data and data[key]:
                if apply:
                    del data[key]
                    modified = True
                else:
                    print(f"  Would remove: {key}: {data[key]}")
                    modified = True

    # Remove redundant verse transliterations
    for verse in data.get('verses', []):
        for lang in ['ta', 'hi', 'en']:
            if lang in verse and verse[lang]:
                if apply:
                    del verse[lang]
                    modified = True
                else:
                    preview = verse[lang][:50] + '...' if len(verse[lang]) > 50 else verse[lang]
                    print(f"  Would remove verse {lang}: {preview}")
                    modified = True

            # Also check text_<lang> format
            text_key = f'text_{lang}'
            if text_key in verse and verse[text_key]:
                if apply:
                    del verse[text_key]
                    modified = True

        # Remove redundant subtitle transliterations
        for lang in ['ta', 'hi', 'en']:
            sub_key = f'subtitle_{lang}'
            if sub_key in verse and verse[sub_key]:
                if apply:
                    del verse[sub_key]
                    modified = True
                else:
                    print(f"  Would remove: {sub_key}: {verse[sub_key]}")
                    modified = True

        # Remove redundant type translations
        for lang in ['ta', 'hi', 'en']:
            type_key = f'type_{lang}'
            if type_key in verse and verse[type_key]:
                if apply:
                    del verse[type_key]
                    modified = True

    if not modified:
        return False

    if apply:
        if backup:
            backup_path = yaml_path.with_suffix('.yml.bak')
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(content)

        # Write cleaned YAML
        write_clean_yaml(yaml_path, data)

    return modified


def write_clean_yaml(yaml_path, data):
    """Write YAML with clean formatting (Kannada only)."""
    with open(yaml_path, 'w', encoding='utf-8') as f:
        f.write("# ──────────────────────────────────────────────────────────────────\n")
        f.write("# Daasa Saahitya - Lyrics File\n")
        f.write("# Transliterations are auto-generated at build time\n")
        f.write("# ──────────────────────────────────────────────────────────────────\n\n")

        # Write metadata fields in order (Kannada only)
        meta_fields = ['title_kn', 'author_kn', 'ankita_kn', 'raga_kn', 'tala_kn']

        for field in meta_fields:
            if field in data and data[field]:
                f.write(f"{field}: {data[field]}\n")
        f.write("\n")

        # Write verses
        f.write("verses:\n")
        for verse in data.get('verses', []):
            vtype = verse.get('type', '')
            f.write(f"  - type: {vtype}\n")

            if verse.get('number'):
                f.write(f"    number: {verse['number']}\n")

            if verse.get('subtitle_kn'):
                f.write(f"    subtitle_kn: {verse['subtitle_kn']}\n")

            kn_text = verse.get('kn', '')
            if kn_text:
                f.write(f"    kn: |\n")
                for line in kn_text.strip().split('\n'):
                    f.write(f"      {line}\n")

            f.write("\n")


def main():
    apply_mode = '--apply' in sys.argv
    backup_mode = '--backup' in sys.argv

    repo_root = Path(__file__).parent.parent
    lyrics_dir = repo_root / 'lyrics'

    yaml_files = list(lyrics_dir.rglob('*.yml')) + list(lyrics_dir.rglob('*.yaml'))

    print(f"Found {len(yaml_files)} YAML files.")
    print(f"Mode: {'DRY RUN' if not apply_mode else 'APPLY'}\n")

    modified_count = 0
    for yaml_path in sorted(yaml_files):
        rel = yaml_path.relative_to(lyrics_dir)
        try:
            if cleanup_yaml_file(yaml_path, apply=apply_mode, backup=backup_mode):
                print(f"  {'Would clean' if not apply_mode else 'Cleaned'}: {rel}")
                modified_count += 1
        except Exception as e:
            print(f"  Error: {rel}: {e}", file=sys.stderr)

    print(f"\n{'Would modify' if not apply_mode else 'Modified'} {modified_count} files.")
    if not apply_mode:
        print("\nRun with --apply to actually modify files.")
        print("Run with --apply --backup to keep .bak copies.")


if __name__ == '__main__':
    main()
