#!/usr/bin/env python3
"""
Transliterate Kannada lyrics to Tamil, Devanagari, and IAST.
Writes the transliterated text back into the same YAML file for manual editing.

Usage:
    python transliterate.py                    # Process all YAML files in lyrics/
    python transliterate.py path/to/song.yml   # Process a specific file
"""

import sys
import yaml
from pathlib import Path

# Import transliteration functions from build.py
from build import (
    transliterate_to_tamil,
    transliterate_to_devanagari,
    transliterate_to_iast,
)


def transliterate_field(text, engine):
    """Transliterate a possibly multi-line string."""
    if not text:
        return ''
    lines = text.split('\n')
    return '\n'.join(engine(line) for line in lines)


def process_yaml_file(yaml_path):
    """
    Read a YAML lyrics file, add transliterated fields, and write back.
    Only adds fields that don't already exist (preserves manual edits).
    """
    with open(yaml_path, encoding='utf-8') as f:
        content = f.read()

    data = yaml.safe_load(content)
    if not data:
        print(f"  Skipping empty file: {yaml_path}")
        return False

    modified = False

    # Fields to transliterate
    fields = ['title', 'author', 'raga', 'tala', 'ankita']

    for field in fields:
        kn_val = data.get(f'{field}_kn', '')
        if not kn_val:
            continue

        # Tamil
        if not data.get(f'{field}_ta'):
            data[f'{field}_ta'] = transliterate_field(str(kn_val), transliterate_to_tamil)
            modified = True

        # Devanagari
        if not data.get(f'{field}_hi'):
            data[f'{field}_hi'] = transliterate_field(str(kn_val), transliterate_to_devanagari)
            modified = True

        # IAST
        if not data.get(f'{field}_en'):
            data[f'{field}_en'] = transliterate_field(str(kn_val), transliterate_to_iast)
            modified = True

    # Process verses
    verses = data.get('verses', [])
    for verse in verses:
        # Verse text - use original Kannada text, do NOT modify it
        kn_text = verse.get('kn', '')
        if kn_text:
            # Only generate transliterations if they don't exist
            if not verse.get('ta'):
                verse['ta'] = transliterate_field(kn_text, transliterate_to_tamil)
                modified = True

            if not verse.get('hi'):
                verse['hi'] = transliterate_field(kn_text, transliterate_to_devanagari)
                modified = True

            if not verse.get('en'):
                verse['en'] = transliterate_field(kn_text, transliterate_to_iast)
                modified = True

        # Verse type (if in Kannada)
        vtype = verse.get('type', '')
        if vtype and is_kannada(vtype):
            if not verse.get('type_ta'):
                verse['type_ta'] = transliterate_to_tamil(vtype)
                modified = True
            if not verse.get('type_hi'):
                verse['type_hi'] = transliterate_to_devanagari(vtype)
                modified = True
            if not verse.get('type_en'):
                verse['type_en'] = transliterate_to_iast(vtype)
                modified = True

        # Subtitle
        subtitle_kn = verse.get('subtitle_kn', '')
        if subtitle_kn:
            if not verse.get('subtitle_ta'):
                verse['subtitle_ta'] = transliterate_field(subtitle_kn, transliterate_to_tamil)
                modified = True
            if not verse.get('subtitle_hi'):
                verse['subtitle_hi'] = transliterate_field(subtitle_kn, transliterate_to_devanagari)
                modified = True
            if not verse.get('subtitle_en'):
                verse['subtitle_en'] = transliterate_field(subtitle_kn, transliterate_to_iast)
                modified = True

    if modified:
        # Write back to YAML with proper formatting
        write_yaml_file(yaml_path, data)
        return True

    return False


def is_kannada(text):
    """Check if text contains Kannada characters."""
    for char in text:
        if 'ಀ' <= char <= '೿':
            return True
    return False


def extract_kannada_only(text):
    """
    Extract only the Kannada portion of text (stops at first non-Kannada script line).
    This handles cases where Tamil/other scripts were accidentally appended.
    """
    if not text:
        return ''

    lines = text.strip().split('\n')
    kannada_lines = []

    for line in lines:
        # Check if this line contains Kannada characters
        has_kannada = any('ಀ' <= char <= '೿' for char in line)
        # Check if this line contains Tamil characters
        has_tamil = any('஀' <= char <= '௿' for char in line)
        # Check if this line contains Devanagari characters
        has_devanagari = any('ऀ' <= char <= 'ॿ' for char in line)

        # Only include lines that have Kannada and don't have Tamil/Devanagari
        if has_kannada and not has_tamil and not has_devanagari:
            kannada_lines.append(line)
        elif not has_kannada and not has_tamil and not has_devanagari:
            # Neutral lines (punctuation, whitespace) - include if we have Kannada context
            if kannada_lines:
                kannada_lines.append(line)

    return '\n'.join(kannada_lines)


def deduplicate_text(text):
    """
    Remove duplicate content that was accidentally appended.
    Detects if the text is the same verse repeated twice.
    """
    if not text:
        return text

    lines = text.strip().split('\n')
    n = len(lines)

    # Check if text is duplicated (second half equals first half)
    if n >= 2 and n % 2 == 0:
        half = n // 2
        first_half = lines[:half]
        second_half = lines[half:]
        if first_half == second_half:
            return '\n'.join(first_half)

    return text


def write_yaml_file(yaml_path, data):
    """Write YAML with custom formatting for readability."""

    def represent_str(dumper, data):
        """Use literal block style for multi-line strings."""
        if '\n' in data:
            return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
        return dumper.represent_scalar('tag:yaml.org,2002:str', data)

    yaml.add_representer(str, represent_str)

    with open(yaml_path, 'w', encoding='utf-8') as f:
        # Write header comment
        f.write("# ──────────────────────────────────────────────────────────────────\n")
        f.write("# Daasa Saahitya - Lyrics File (Auto-transliterated)\n")
        f.write("# Edit the _ta, _hi, _en fields to correct any transliteration errors\n")
        f.write("# ──────────────────────────────────────────────────────────────────\n\n")

        # Write metadata fields in order
        meta_fields = [
            ('title_kn', 'title_ta', 'title_hi', 'title_en'),
            ('author_kn', 'author_ta', 'author_hi', 'author_en'),
            ('ankita_kn', 'ankita_ta', 'ankita_hi', 'ankita_en'),
            ('raga_kn', 'raga_ta', 'raga_hi', 'raga_en'),
            ('tala_kn', 'tala_ta', 'tala_hi', 'tala_en'),
        ]

        for field_group in meta_fields:
            for field in field_group:
                if field in data and data[field]:
                    f.write(f"{field}: {data[field]}\n")
            f.write("\n")

        # Write verses
        f.write("verses:\n")
        for verse in data.get('verses', []):
            f.write("  - type: {}\n".format(verse.get('type', '')))

            # Type translations
            if verse.get('type_ta'):
                f.write("    type_ta: {}\n".format(verse['type_ta']))
            if verse.get('type_hi'):
                f.write("    type_hi: {}\n".format(verse['type_hi']))
            if verse.get('type_en'):
                f.write("    type_en: {}\n".format(verse['type_en']))

            # Number
            if verse.get('number'):
                f.write("    number: {}\n".format(verse['number']))

            # Subtitle
            if verse.get('subtitle_kn'):
                f.write("    subtitle_kn: {}\n".format(verse['subtitle_kn']))
            if verse.get('subtitle_ta'):
                f.write("    subtitle_ta: {}\n".format(verse['subtitle_ta']))
            if verse.get('subtitle_hi'):
                f.write("    subtitle_hi: {}\n".format(verse['subtitle_hi']))
            if verse.get('subtitle_en'):
                f.write("    subtitle_en: {}\n".format(verse['subtitle_en']))

            # Lyrics in each language
            for lang in ['kn', 'ta', 'hi', 'en']:
                text = verse.get(lang, '')
                if text:
                    # Use literal block style for multi-line
                    f.write(f"    {lang}: |\n")
                    for line in text.strip().split('\n'):
                        f.write(f"      {line}\n")

            f.write("\n")


def main():
    if len(sys.argv) > 1:
        # Process specific file
        yaml_path = Path(sys.argv[1])
        if yaml_path.exists():
            if process_yaml_file(yaml_path):
                print(f"Transliterated: {yaml_path}")
            else:
                print(f"No changes needed: {yaml_path}")
        else:
            print(f"File not found: {yaml_path}")
    else:
        # Process all YAML files in lyrics/
        repo_root = Path(__file__).parent.parent
        lyrics_dir = repo_root / 'lyrics'

        yaml_files = list(lyrics_dir.rglob('*.yml')) + list(lyrics_dir.rglob('*.yaml'))

        print(f"Found {len(yaml_files)} lyrics files.\n")

        for yaml_path in sorted(yaml_files):
            rel = yaml_path.relative_to(lyrics_dir)
            try:
                if process_yaml_file(yaml_path):
                    print(f"  Transliterated: {rel}")
                else:
                    print(f"  No changes: {rel}")
            except Exception as e:
                print(f"  Error: {rel}: {e}")

        print("\nDone! Review the YAML files and edit any incorrect transliterations.")
        print("Then run 'python build.py' to generate the HTML.")


if __name__ == '__main__':
    main()
