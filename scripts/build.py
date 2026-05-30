#!/usr/bin/env python3
"""
Daasa Saahitya - Site Builder
Reads YAML lyrics files, transliterates Kannada → Tamil (with superscripts),
Devanagari, and IAST English, then generates static HTML pages.
"""

import os
import re
import sys
import json
import yaml
import shutil
from pathlib import Path
from datetime import datetime

# ─────────────────────────────────────────────
#  KANNADA → TAMIL MAPPING (with superscripts)
# ─────────────────────────────────────────────
# Format: kannada_char → tamil_equivalent
# Superscripts encode phonetic distinctions missing from Tamil script.

KN_VOWELS = {
    'ಅ': 'அ',  'ಆ': 'ஆ',  'ಇ': 'இ',  'ಈ': 'ஈ',
    'ಉ': 'உ',  'ಊ': 'ஊ',  'ಋ': 'ரு', 'ೠ': 'ரூ',
    'ಎ': 'எ',  'ಏ': 'ஏ',  'ಐ': 'ஐ',
    'ಒ': 'ஒ',  'ಓ': 'ஓ',  'ಔ': 'ஔ',
    'ಅಂ': 'அம்', 'ಅಃ': 'அஹ',
}

KN_VOWEL_SIGNS = {
    'ಾ': 'ா',  'ಿ': 'ி',  'ೀ': 'ீ',
    'ು': 'ு',  'ೂ': 'ூ',  'ೃ': 'ரு',
    'ೆ': 'ெ',  'ೇ': 'ே',  'ೈ': 'ை',
    'ೊ': 'ொ',  'ೋ': 'ோ',  'ೌ': 'ௌ',
    'ಂ': 'ம்', 'ಃ': 'ஹ', '್': '்',
    '಼': '',
}

# Consonant map: kannada → (tamil_base, superscript_or_empty)
KN_CONSONANTS_TAMIL = {
    'ಕ': ('க', ''),   'ಖ': ('க', '²'),  'ಗ': ('க', '³'),  'ಘ': ('க', '⁴'),
    'ಙ': ('ங', ''),
    'ಚ': ('ச', ''),   'ಛ': ('ச', '²'),
    'ಜ': ('ஜ', ''),   'ಝ': ('ஜ', '²'),
    'ಞ': ('ஞ', ''),
    'ಟ': ('ட', ''),   'ಠ': ('ட', '²'),  'ಡ': ('ட', '³'),  'ಢ': ('ட', '⁴'),
    'ಣ': ('ண', ''),
    'ತ': ('த', ''),   'ಥ': ('த', '²'),  'ದ': ('த', '³'),  'ಧ': ('த', '⁴'),
    'ನ': ('ன', ''),
    'ಪ': ('ப', ''),   'ಫ': ('ப', '²'),  'ಬ': ('ப', '³'),  'ಭ': ('ப', '⁴'),
    'ಮ': ('ம', ''),
    'ಯ': ('ய', ''),   'ರ': ('ர', ''),   'ಲ': ('ல', ''),   'ವ': ('வ', ''),
    'ಶ': ('ஶ', ''),   'ಷ': ('ஷ', ''),   'ಸ': ('ஸ', ''),   'ಹ': ('ஹ', ''),
    'ಳ': ('ள', ''),
    'ಱ': ('ற', ''),   'ೞ': ('ழ', ''),
}

# Special conjuncts (must be checked BEFORE individual consonants)
SPECIAL_CONJUNCTS_TAMIL = {
    'ಜ್ಞ': 'க்³ஞ',
    'ಕ್ಷ': 'க்ஷ',
    'ಶ್ರೀ': 'ஸ்ரீ',
    'ಶ್ರ': 'ஸ்ர',
}

# ─────────────────────────────────────────────
#  KANNADA → DEVANAGARI MAPPING
# ─────────────────────────────────────────────
KN_TO_DEV = {
    # Vowels
    'ಅ': 'अ', 'ಆ': 'आ', 'ಇ': 'इ', 'ಈ': 'ई',
    'ಉ': 'उ', 'ಊ': 'ऊ', 'ಋ': 'ऋ', 'ೠ': 'ॠ',
    'ಎ': 'ए', 'ಏ': 'ए', 'ಐ': 'ऐ',
    'ಒ': 'ओ', 'ಓ': 'ओ', 'ಔ': 'औ',
    # Vowel signs
    'ಾ': 'ा', 'ಿ': 'ि', 'ೀ': 'ी',
    'ು': 'ु', 'ೂ': 'ू', 'ೃ': 'ृ',
    'ೆ': 'े', 'ೇ': 'े', 'ೈ': 'ै',
    'ೊ': 'ो', 'ೋ': 'ो', 'ೌ': 'ौ',
    'ಂ': 'ं', 'ಃ': 'ः', '್': '्', '಼': '',
    # Consonants
    'ಕ': 'क', 'ಖ': 'ख', 'ಗ': 'ग', 'ಘ': 'घ', 'ಙ': 'ङ',
    'ಚ': 'च', 'ಛ': 'छ', 'ಜ': 'ज', 'ಝ': 'झ', 'ಞ': 'ञ',
    'ಟ': 'ट', 'ಠ': 'ठ', 'ಡ': 'ड', 'ಢ': 'ढ़', 'ಣ': 'ण',
    'ತ': 'त', 'ಥ': 'थ', 'ದ': 'द', 'ಧ': 'ध', 'ನ': 'न',
    'ಪ': 'प', 'ಫ': 'फ', 'ಬ': 'ब', 'ಭ': 'भ', 'ಮ': 'म',
    'ಯ': 'य', 'ರ': 'र', 'ಲ': 'ल', 'ವ': 'व',
    'ಶ': 'श', 'ಷ': 'ष', 'ಸ': 'स', 'ಹ': 'ह',
    'ಳ': 'ळ', 'ಱ': 'र', 'ೞ': 'ल',
    # Special conjuncts
    'ಜ್ಞ': 'ज्ञ', 'ಕ್ಷ': 'क्ष', 'ಶ್ರೀ': 'श्री',
}

# ─────────────────────────────────────────────
#  KANNADA → IAST (Latin) MAPPING
# ─────────────────────────────────────────────
KN_TO_IAST = {
    # Vowels (standalone)
    'ಅ': 'a', 'ಆ': 'ā', 'ಇ': 'i', 'ಈ': 'ī',
    'ಉ': 'u', 'ಊ': 'ū', 'ಋ': 'ṛ', 'ೠ': 'ṝ',
    'ಎ': 'e', 'ಏ': 'ē', 'ಐ': 'ai',
    'ಒ': 'o', 'ಓ': 'ō', 'ಔ': 'au',
    # Vowel signs (mātras)
    'ಾ': 'ā', 'ಿ': 'i', 'ೀ': 'ī',
    'ು': 'u', 'ೂ': 'ū', 'ೃ': 'ṛ',
    'ೆ': 'e', 'ೇ': 'ē', 'ೈ': 'ai',
    'ೊ': 'o', 'ೋ': 'ō', 'ೌ': 'au',
    'ಂ': 'ṃ', 'ಃ': 'ḥ', '್': '', '಼': '',
    # Consonants (base form, 'a' vowel implicit, added in transliteration logic)
    'ಕ': 'k', 'ಖ': 'kh', 'ಗ': 'g', 'ಘ': 'gh', 'ಙ': 'ṅ',
    'ಚ': 'c', 'ಛ': 'ch', 'ಜ': 'j', 'ಝ': 'jh', 'ಞ': 'ñ',
    'ಟ': 'ṭ', 'ಠ': 'ṭh', 'ಡ': 'ḍ', 'ಢ': 'ḍh', 'ಣ': 'ṇ',
    'ತ': 't', 'ಥ': 'th', 'ದ': 'd', 'ಧ': 'dh', 'ನ': 'n',
    'ಪ': 'p', 'ಫ': 'ph', 'ಬ': 'b', 'ಭ': 'bh', 'ಮ': 'm',
    'ಯ': 'y', 'ರ': 'r', 'ಲ': 'l', 'ವ': 'v',
    'ಶ': 'ś', 'ಷ': 'ṣ', 'ಸ': 's', 'ಹ': 'h',
    'ಳ': 'ḷ', 'ಱ': 'ṟ', 'ೞ': 'ḻ',
    'ಜ್ಞ': 'jñ', 'ಕ್ಷ': 'kṣ', 'ಶ್ರೀ': 'śrī',
}

# Unicode ranges for classification
KANNADA_CONSONANTS = set(KN_CONSONANTS_TAMIL.keys())
KANNADA_VOWEL_SIGNS = set(KN_VOWEL_SIGNS.keys())
KANNADA_VOWELS = set(KN_VOWELS.keys())
HALANTA = '್'  # virama
ANUSVARA = 'ಂ'

def is_kannada_consonant(ch):
    return ch in KANNADA_CONSONANTS

def is_vowel_sign(ch):
    return ch in KANNADA_VOWEL_SIGNS

# ─────────────────────────────────────────────
#  VARGA-BASED NASAL MAPPING
# ─────────────────────────────────────────────
# Anusvara (ಂ) becomes the nasal of the same varga as the following consonant

# Kannada consonants grouped by varga
KA_VARGA = {'ಕ', 'ಖ', 'ಗ', 'ಘ', 'ಙ'}  # velar - nasal ಙ
CA_VARGA = {'ಚ', 'ಛ', 'ಜ', 'ಝ', 'ಞ'}  # palatal - nasal ಞ
TA_VARGA = {'ಟ', 'ಠ', 'ಡ', 'ಢ', 'ಣ'}  # retroflex - nasal ಣ
THA_VARGA = {'ತ', 'ಥ', 'ದ', 'ಧ', 'ನ'}  # dental - nasal ನ
PA_VARGA = {'ಪ', 'ಫ', 'ಬ', 'ಭ', 'ಮ'}  # labial - nasal ಮ

# Nasal consonants for each varga in different scripts
VARGA_NASALS = {
    'ka': {'kn': 'ಙ', 'hi': 'ङ', 'ta': 'ங', 'iast': 'ṅ'},
    'ca': {'kn': 'ಞ', 'hi': 'ञ', 'ta': 'ஞ', 'iast': 'ñ'},
    'Ta': {'kn': 'ಣ', 'hi': 'ण', 'ta': 'ண', 'iast': 'ṇ'},
    'ta': {'kn': 'ನ', 'hi': 'न', 'ta': 'ந', 'iast': 'n'},
    'pa': {'kn': 'ಮ', 'hi': 'म', 'ta': 'ம', 'iast': 'm'},
}

def get_varga(consonant):
    """Return the varga name for a Kannada consonant."""
    if consonant in KA_VARGA:
        return 'ka'
    elif consonant in CA_VARGA:
        return 'ca'
    elif consonant in TA_VARGA:
        return 'Ta'
    elif consonant in THA_VARGA:
        return 'ta'
    elif consonant in PA_VARGA:
        return 'pa'
    return None

# ─────────────────────────────────────────────
#  ANUSVARA HELPER
# ─────────────────────────────────────────────

def get_varga_nasal_for_anusvara(chars, pos, script):
    """
    Look ahead from position pos to find the next Kannada consonant,
    determine its varga, and return the appropriate nasal for the target script.
    Script should be 'ta', 'hi', or 'iast'.
    Returns None if anusvara should be kept as-is (no following varga consonant).
    """
    n = len(chars)
    j = pos + 1
    while j < n:
        if chars[j] in KANNADA_CONSONANTS:
            varga = get_varga(chars[j])
            if varga:
                return VARGA_NASALS[varga][script]
            break
        elif chars[j].isspace() or chars[j] in '|।॥':
            break
        j += 1
    return None


# ─────────────────────────────────────────────
#  TRANSLITERATION ENGINES
# ─────────────────────────────────────────────

def transliterate_to_tamil(text):
    """Convert Kannada text to Tamil with superscript notation."""
    result = []
    i = 0
    chars = list(text)
    n = len(chars)

    while i < n:
        # Check 3-char special conjuncts first
        chunk3 = ''.join(chars[i:i+3])
        chunk2 = ''.join(chars[i:i+2])

        if chunk3 in SPECIAL_CONJUNCTS_TAMIL:
            result.append(SPECIAL_CONJUNCTS_TAMIL[chunk3])
            i += 3
            continue
        if chunk2 in SPECIAL_CONJUNCTS_TAMIL:
            result.append(SPECIAL_CONJUNCTS_TAMIL[chunk2])
            i += 2
            continue

        ch = chars[i]

        # Handle anusvara - convert to varga nasal based on following consonant
        if ch == ANUSVARA:
            nasal = get_varga_nasal_for_anusvara(chars, i, 'ta')
            if nasal:
                result.append(nasal)
                result.append('்')  # Tamil halanta
            else:
                result.append(KN_VOWEL_SIGNS[ch])  # fallback to default ம்
            i += 1
            continue

        # Standalone vowel
        if ch in KN_VOWELS:
            result.append(KN_VOWELS[ch])
            i += 1
            continue

        # Consonant
        if ch in KN_CONSONANTS_TAMIL:
            base, sup = KN_CONSONANTS_TAMIL[ch]
            i += 1
            # Collect following vowel sign or halanta
            if i < n and chars[i] == HALANTA:
                # Consonant cluster: add virama THEN superscript (so circle attaches to base)
                result.append(base)
                result.append('்')
                if sup:
                    result.append(f'<sup>{sup}</sup>')
                i += 1
            elif i < n and chars[i] == ANUSVARA:
                # Anusvara after consonant - output consonant with inherent 'a',
                # then handle anusvara on next iteration
                result.append(base)
                if sup:
                    result.append(f'<sup>{sup}</sup>')
                # Don't consume anusvara - let it be processed in next iteration
            elif i < n and chars[i] in KN_VOWEL_SIGNS:
                vsign = chars[i]
                result.append(base)
                result.append(KN_VOWEL_SIGNS[vsign])
                # Place superscript AFTER the vowel sign so it renders together
                if sup:
                    result.append(f'<sup>{sup}</sup>')
                i += 1
            else:
                # Implicit 'a' vowel - superscript after base consonant
                result.append(base)
                if sup:
                    result.append(f'<sup>{sup}</sup>')
                result.append('')  # Tamil has inherent 'a' in most contexts
            continue

        # Vowel sign standalone
        if ch in KN_VOWEL_SIGNS:
            result.append(KN_VOWEL_SIGNS[ch])
            i += 1
            continue

        # Pass-through (spaces, punctuation, digits, pipe etc.)
        result.append(ch)
        i += 1

    return ''.join(result)


def transliterate_to_devanagari(text):
    """Convert Kannada text to Devanagari."""
    result = []
    i = 0
    chars = list(text)
    n = len(chars)

    # Check longest match first for special conjuncts
    special = {k: v for k, v in KN_TO_DEV.items() if len(k) > 1}

    while i < n:
        matched = False
        for length in [3, 2]:
            chunk = ''.join(chars[i:i+length])
            if chunk in special:
                result.append(special[chunk])
                i += length
                matched = True
                break
        if matched:
            continue

        ch = chars[i]

        # Handle anusvara - convert to varga nasal based on following consonant
        if ch == ANUSVARA:
            nasal = get_varga_nasal_for_anusvara(chars, i, 'hi')
            if nasal:
                result.append(nasal)
                result.append('्')  # Devanagari halanta
            else:
                result.append(KN_TO_DEV[ch])  # fallback to ं
            i += 1
            continue

        if ch in KN_TO_DEV:
            # Consonant with implicit 'a'
            if ch in KANNADA_CONSONANTS:
                result.append(KN_TO_DEV[ch])
                i += 1
            else:
                result.append(KN_TO_DEV[ch])
                i += 1
        else:
            result.append(ch)
            i += 1
    return ''.join(result)


def transliterate_to_iast(text):
    """Convert Kannada text to IAST romanization."""
    result = []
    i = 0
    chars = list(text)
    n = len(chars)
    special = {k: v for k, v in KN_TO_IAST.items() if len(k) > 1}

    while i < n:
        matched = False
        for length in [3, 2]:
            chunk = ''.join(chars[i:i+length])
            if chunk in special:
                result.append(special[chunk])
                i += length
                matched = True
                break
        if matched:
            continue

        ch = chars[i]

        # Handle anusvara - convert to varga nasal based on following consonant
        if ch == ANUSVARA:
            nasal = get_varga_nasal_for_anusvara(chars, i, 'iast')
            if nasal:
                result.append(nasal)
            else:
                result.append(KN_TO_IAST[ch])  # fallback to ṃ
            i += 1
            continue

        if ch in KANNADA_CONSONANTS:
            result.append(KN_TO_IAST[ch])
            i += 1
            # Check following char
            if i < n and chars[i] == HALANTA:
                # No vowel, skip halanta
                i += 1
            elif i < n and chars[i] == ANUSVARA:
                # Anusvara after consonant - add inherent 'a', let anusvara be processed next
                result.append('a')
            elif i < n and chars[i] in KN_VOWEL_SIGNS:
                result.append(KN_TO_IAST.get(chars[i], ''))
                i += 1
            else:
                result.append('a')  # inherent 'a'
        elif ch in KN_TO_IAST:
            result.append(KN_TO_IAST[ch])
            i += 1
        else:
            result.append(ch)
            i += 1

    return ''.join(result)


# ─────────────────────────────────────────────
#  YAML LOADER
# ─────────────────────────────────────────────

def load_lyrics_file(path):
    with open(path, encoding='utf-8') as f:
        return yaml.safe_load(f)

def transliterate_field(text, engine):
    """Transliterate a possibly multi-line Kannada string."""
    if not text:
        return ''
    lines = text.split('\n')
    return '\n'.join(engine(line) for line in lines)

def auto_transliterate(data, engine_name):
    """
    Given a lyrics dict and engine name ('tamil'|'devanagari'|'iast'),
    return transliterated versions of all text fields.
    """
    if engine_name == 'tamil':
        engine = transliterate_to_tamil
    elif engine_name == 'devanagari':
        engine = transliterate_to_devanagari
    else:
        engine = transliterate_to_iast

    lang_key = {'tamil': 'ta', 'devanagari': 'hi', 'iast': 'en'}[engine_name]

    result = {}
    # Title, author
    for field in ['title', 'author', 'raga', 'tala', 'description']:
        kn_val = data.get(f'{field}_kn', '')
        # If a manual override exists and is non-empty, use it; else transliterate
        manual_override = data.get(f'{field}_{lang_key}')
        if manual_override:
            result[f'{field}_{lang_key}'] = manual_override
        else:
            result[f'{field}_{lang_key}'] = transliterate_field(str(kn_val), engine) if kn_val else ''

    # Verses
    result['verses'] = []
    for verse in data.get('verses', []):
        v = dict(verse)
        kn_text = verse.get('kn', '')
        v[f'text_{lang_key}'] = verse.get(
            f'text_{lang_key}',
            transliterate_field(kn_text, engine) if kn_text else ''
        )
        if 'subtitle_kn' in verse:
            v[f'subtitle_{lang_key}'] = verse.get(
                f'subtitle_{lang_key}',
                transliterate_field(verse['subtitle_kn'], engine)
            )
        result['verses'].append(v)
    return result


# ─────────────────────────────────────────────
#  HTML GENERATION
# ─────────────────────────────────────────────

VERSE_TYPE_LABELS = {
    'pallavi':    {'kn': 'ಪಲ್ಲವಿ',    'ta': 'பல்லவி',   'hi': 'पल्लवि',    'en': 'Pallavi'},
    'anupallavi': {'kn': 'ಅನುಪಲ್ಲವಿ', 'ta': 'அனுபல்லவி','hi': 'अनुपल्लवि', 'en': 'Anupallavi'},
    'charana':    {'kn': 'ಚರಣ',       'ta': 'சரண',      'hi': 'चरण',       'en': 'Caraṇa'},
    'madhyamakala':{'kn':'ಮಧ್ಯಮಕಾಲ', 'ta': 'மத்யமகால','hi': 'मध्यमकाल',  'en': 'Madhyamakāla'},
}

def verse_label(vtype, lang, number=None):
    labels = VERSE_TYPE_LABELS.get(vtype, {})
    label = labels.get(lang, vtype.capitalize())
    if number:
        label += f' {number}'
    return label

def lines_to_html(text):
    """Convert newline-separated text to HTML with <br> tags."""
    if not text:
        return ''
    lines = [l for l in text.strip().split('\n')]
    return '<br>\n'.join(lines)

def generate_song_page(data, rel_path, output_dir, template_path):
    """Generate a full HTML page for one song."""
    with open(template_path, encoding='utf-8') as f:
        template = f.read()

    # Build all 4 language panels
    langs = [
        ('kn', 'ಕನ್ನಡ', 'Kannada'),
        ('ta', 'தமிழ்', 'Tamil'),
        ('hi', 'देवनागरी', 'Devanagari'),
        ('en', 'IAST', 'IAST'),
    ]

    # Auto-transliterate missing fields
    ta_data = auto_transliterate(data, 'tamil')
    hi_data = auto_transliterate(data, 'devanagari')
    en_data = auto_transliterate(data, 'iast')

    panels_html = ''
    for idx, (lang, native_name, eng_name) in enumerate(langs):
        active = 'active' if idx == 0 else ''

        if lang == 'kn':
            title = data.get('title_kn', '')
            author = data.get('author_kn', '')
            raga = data.get('raga_kn', '')
            tala = data.get('tala_kn', '')
            desc = data.get('description_kn', '')
            verses = data.get('verses', [])
            text_key = 'kn'
            sub_key = 'subtitle_kn'
        elif lang == 'ta':
            title = ta_data.get('title_ta', '')
            author = ta_data.get('author_ta', '')
            raga = ta_data.get('raga_ta', '')
            tala = ta_data.get('tala_ta', '')
            desc = ta_data.get('description_ta', '')
            verses = ta_data['verses']
            text_key = 'text_ta'
            sub_key = 'subtitle_ta'
        elif lang == 'hi':
            title = hi_data.get('title_hi', '')
            author = hi_data.get('author_hi', '')
            raga = hi_data.get('raga_hi', '')
            tala = hi_data.get('tala_hi', '')
            desc = hi_data.get('description_hi', '')
            verses = hi_data['verses']
            text_key = 'text_hi'
            sub_key = 'subtitle_hi'
        else:
            title = en_data.get('title_en', '')
            author = en_data.get('author_en', '')
            raga = en_data.get('raga_en', '')
            tala = en_data.get('tala_en', '')
            desc = en_data.get('description_en', '')
            verses = en_data['verses']
            text_key = 'text_en'
            sub_key = 'subtitle_en'

        meta_html = ''
        if raga or tala:
            raga_html = f'<span class="meta-item raga">{raga}</span>' if raga else '<span></span>'
            tala_html = f'<span class="meta-item tala">{tala}</span>' if tala else '<span></span>'
            meta_html += f'<div class="song-meta-row">{raga_html}{tala_html}</div>\n'
        if desc:
            meta_html += f'<span class="meta-item desc">{desc}</span>'

        verses_html = ''
        for verse in verses:
            vtype = verse.get('type', '')
            vnum = verse.get('number', '')

            # Subtitle (mid-song heading)
            if vtype == 'subtitle':
                sub_text = verse.get(sub_key) or verse.get('subtitle_kn', '')
                verses_html += f'<h3 class="verse-subtitle">{sub_text}</h3>\n'
                continue

            label = verse_label(vtype, lang, vnum)
            text = verse.get(text_key) or verse.get('kn', '')
            text_html = lines_to_html(text)

            verses_html += f'''
<div class="verse verse-{vtype}">
  <div class="verse-label">{label}</div>
  <div class="verse-text">{text_html}</div>
</div>
'''

        panels_html += f'''
<div class="lang-panel {active}" id="panel-{lang}" data-lang="{lang}">
  <div class="song-header">
    <h1 class="song-title">{title}</h1>
    <h2 class="song-author">{author}</h2>
    <div class="song-meta">{meta_html}</div>
  </div>
  <div class="song-body">
    {verses_html}
  </div>
</div>
'''

    # Tab buttons
    tabs_html = ''
    for idx, (lang, native_name, eng_name) in enumerate(langs):
        active = 'active' if idx == 0 else ''
        tabs_html += f'<button class="tab-btn {active}" data-target="{lang}">{native_name}</button>\n'

    # Breadcrumb - handle nested categories
    parts = rel_path.parts
    depth = len(parts) - 1  # Number of parent folders
    back_path = '../' * depth + 'index.html'

    breadcrumb = f'<a href="{back_path}">Home</a>'
    if len(parts) >= 2:
        # Category
        cat = parts[0]
        cat_label = format_category_name(cat)
        breadcrumb += f' › <a href="{back_path}#{cat}">{cat_label}</a>'
    if len(parts) >= 3:
        # Sub-category
        subcat = parts[1]
        subcat_label = format_category_name(subcat)
        breadcrumb += f' › <a href="{back_path}#{cat}-{subcat}">{subcat_label}</a>'
    breadcrumb += f' › {data.get("title_kn", "")}'

    html = template.replace('{{TABS}}', tabs_html)
    html = html.replace('{{PANELS}}', panels_html)
    html = html.replace('{{BREADCRUMB}}', breadcrumb)
    html = html.replace('{{PAGE_TITLE}}', data.get('title_kn', 'Song'))

    out_path = output_dir / rel_path.with_suffix('.html')
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(html)

    return out_path


def format_category_name(folder_name):
    """Convert folder name to display name (e.g., 'lakshmi_devi' -> 'Lakshmi Devi')."""
    return folder_name.replace('_', ' ').replace('-', ' ').title()


def generate_index(all_songs, output_dir, template_path):
    """Generate the main index.html grouping songs by category and sub-category."""
    with open(template_path, encoding='utf-8') as f:
        template = f.read()

    # Build nested structure: category -> subcategory -> songs
    from collections import defaultdict

    # Structure: {category: {subcategory: [(rel_path, data), ...], ...}, ...}
    # If no subcategory, use '_root_' as key
    hierarchy = defaultdict(lambda: defaultdict(list))

    for rel_path, data in all_songs:
        parts = rel_path.parts
        if len(parts) >= 3:
            # Has category and subcategory: category/subcategory/song.yml
            category = parts[0]
            subcategory = parts[1]
            hierarchy[category][subcategory].append((rel_path, data))
        elif len(parts) == 2:
            # Only category: category/song.yml
            category = parts[0]
            hierarchy[category]['_root_'].append((rel_path, data))
        else:
            # No category
            hierarchy['other']['_root_'].append((rel_path, data))

    def render_song_entry(rel_path, data):
        """Render a single song entry HTML."""
        title_hi = data.get('title_hi') or transliterate_to_devanagari(data.get('title_kn', ''))
        author_hi = data.get('author_hi') or transliterate_to_devanagari(data.get('author_kn', ''))
        raga_hi = data.get('raga_hi') or transliterate_to_devanagari(data.get('raga_kn', ''))
        href = str(rel_path.with_suffix('.html'))
        return f'''
<a href="{href}" class="song-entry">
  <span class="song-entry-title">{title_hi}</span>
  <span class="song-entry-author">{author_hi}</span>
  {f'<span class="song-entry-raga">{raga_hi}</span>' if raga_hi else ''}
</a>'''

    # Generate HTML for all categories
    groups_html = ''
    total_songs = 0

    for category in sorted(hierarchy.keys()):
        subcategories = hierarchy[category]

        # Count total songs in this category
        cat_total = sum(len(songs) for songs in subcategories.values())
        total_songs += cat_total

        cat_label = format_category_name(category)

        # Build subcategory content
        subcats_html = ''

        # First, render songs directly in category (no subcategory)
        if '_root_' in subcategories:
            root_songs = sorted(subcategories['_root_'], key=lambda x: x[1].get('title_kn', ''))
            for rel_path, data in root_songs:
                subcats_html += render_song_entry(rel_path, data)

        # Then, render each subcategory
        for subcat in sorted(k for k in subcategories.keys() if k != '_root_'):
            songs = sorted(subcategories[subcat], key=lambda x: x[1].get('title_kn', ''))
            subcat_label = format_category_name(subcat)
            subcat_count = len(songs)

            songs_html = ''
            for rel_path, data in songs:
                songs_html += render_song_entry(rel_path, data)

            subcats_html += f'''
<div class="subcategory-section" id="{category}-{subcat}">
  <div class="subcategory-header">
    <h3 class="subcategory-name">{subcat_label}</h3>
    <span class="subcategory-count">{subcat_count}</span>
  </div>
  <div class="songs-list">
    {songs_html}
  </div>
</div>
'''

        groups_html += f'''
<section class="category-section" id="{category}">
  <div class="category-header">
    <h2 class="category-name">{cat_label}</h2>
    <span class="category-count">{cat_total}</span>
  </div>
  <div class="category-content">
    {subcats_html}
  </div>
</section>
'''

    html = template.replace('{{CATEGORIES}}', groups_html)
    html = html.replace('{{TOTAL}}', str(total_songs))
    html = html.replace('{{BUILD_DATE}}', datetime.now().strftime('%d %B %Y'))

    out_path = output_dir / 'index.html'
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(html)
    return out_path


# ─────────────────────────────────────────────
#  MAIN BUILD
# ─────────────────────────────────────────────

def build(repo_root=None):
    if repo_root is None:
        repo_root = Path(__file__).parent.parent
    else:
        repo_root = Path(repo_root).resolve()

    lyrics_dir = repo_root / 'lyrics'
    output_dir = repo_root / 'docs'
    templates_dir = repo_root / 'templates'

    # Clean and recreate output
    if output_dir.exists():
        try:
            shutil.rmtree(output_dir)
        except PermissionError:
            # Directory may be locked, try to remove contents instead
            for item in output_dir.iterdir():
                try:
                    if item.is_dir():
                        shutil.rmtree(item)
                    else:
                        item.unlink()
                except PermissionError:
                    pass
    output_dir.mkdir(parents=True, exist_ok=True)

    # Copy static assets
    for folder in ['css', 'js']:
        src = repo_root / folder
        dest = output_dir / folder
        if dest.exists():
            shutil.rmtree(dest)
        if src.exists():
            shutil.copytree(src, dest)

    song_template = templates_dir / 'song.html'
    index_template = templates_dir / 'index.html'

    all_songs = []
    yaml_files = list(lyrics_dir.rglob('*.yml')) + list(lyrics_dir.rglob('*.yaml'))

    print(f"Found {len(yaml_files)} lyrics files.")

    for yaml_path in sorted(yaml_files):
        rel = yaml_path.relative_to(lyrics_dir)
        try:
            data = load_lyrics_file(yaml_path)
            generate_song_page(data, rel, output_dir, song_template)
            all_songs.append((rel, data))
            print(f"  OK: {rel}")
        except Exception as e:
            print(f"  FAIL: {rel}: {e}", file=sys.stderr)

    generate_index(all_songs, output_dir, index_template)
    print(f"\nBuild complete -> {output_dir}")
    print(f"  {len(all_songs)} songs processed")


if __name__ == '__main__':
    root = sys.argv[1] if len(sys.argv) > 1 else None
    build(root)
