#!/usr/bin/env python3
"""
Daasa Saahitya - site builder.

Reads lyrics YAML, auto-transliterates Kannada to Tamil / Devanagari / IAST,
and generates a static site: one page per song plus a filterable index.

    python scripts/build.py .
"""

import json
import re
import shutil
import sys
from datetime import date
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent))
from align import (  # noqa: E402
    ANKITAS, AUTHORS, CATEGORIES, FESTIVALS, ON_KEY, ON_WHO, TYPES,
)

# ──────────────────────────────────────────────────────────────────────────
#  Kannada → Tamil (with superscripts)
# ──────────────────────────────────────────────────────────────────────────

KN_VOWELS = {
    'ಅ': 'அ', 'ಆ': 'ஆ', 'ಇ': 'இ', 'ಈ': 'ஈ',
    'ಉ': 'உ', 'ಊ': 'ஊ', 'ಋ': 'ரு', 'ೠ': 'ரூ',
    'ಎ': 'எ', 'ಏ': 'ஏ', 'ಐ': 'ஐ',
    'ಒ': 'ஒ', 'ಓ': 'ஓ', 'ಔ': 'ஔ',
    'ಅಂ': 'அம்', 'ಅಃ': 'அஹ',
}

KN_VOWEL_SIGNS = {
    'ಾ': 'ா', 'ಿ': 'ி', 'ೀ': 'ீ',
    'ು': 'ு', 'ೂ': 'ூ', 'ೃ': 'ரு',
    'ೆ': 'ெ', 'ೇ': 'ே', 'ೈ': 'ை',
    'ೊ': 'ொ', 'ೋ': 'ோ', 'ೌ': 'ௌ',
    'ಂ': 'ம்', 'ಃ': 'ஹ', '್': '்', '಼': '',
}

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

SPECIAL_CONJUNCTS_TAMIL = {
    'ಜ್ಞ': 'க்³ஞ', 'ಕ್ಷ': 'க்ஷ', 'ಶ್ರೀ': 'ஸ்ரீ', 'ಶ್ರ': 'ஸ்ர',
}

# ──────────────────────────────────────────────────────────────────────────
#  Kannada → Devanagari
# ──────────────────────────────────────────────────────────────────────────

KN_TO_DEV = {
    'ಅ': 'अ', 'ಆ': 'आ', 'ಇ': 'इ', 'ಈ': 'ई',
    'ಉ': 'उ', 'ಊ': 'ऊ', 'ಋ': 'ऋ', 'ೠ': 'ॠ',
    'ಎ': 'ए', 'ಏ': 'ए', 'ಐ': 'ऐ',
    'ಒ': 'ओ', 'ಓ': 'ओ', 'ಔ': 'औ',
    'ಾ': 'ा', 'ಿ': 'ि', 'ೀ': 'ी',
    'ು': 'ु', 'ೂ': 'ू', 'ೃ': 'ृ',
    'ೆ': 'े', 'ೇ': 'े', 'ೈ': 'ै',
    'ೊ': 'ो', 'ೋ': 'ो', 'ೌ': 'ौ',
    'ಂ': 'ं', 'ಃ': 'ः', '್': '्', '಼': '',
    'ಕ': 'क', 'ಖ': 'ख', 'ಗ': 'ग', 'ಘ': 'घ', 'ಙ': 'ङ',
    'ಚ': 'च', 'ಛ': 'छ', 'ಜ': 'ज', 'ಝ': 'झ', 'ಞ': 'ञ',
    'ಟ': 'ट', 'ಠ': 'ठ', 'ಡ': 'ड', 'ಢ': 'ढ़', 'ಣ': 'ण',
    'ತ': 'त', 'ಥ': 'थ', 'ದ': 'द', 'ಧ': 'ध', 'ನ': 'न',
    'ಪ': 'प', 'ಫ': 'फ', 'ಬ': 'ब', 'ಭ': 'भ', 'ಮ': 'म',
    'ಯ': 'य', 'ರ': 'र', 'ಲ': 'ल', 'ವ': 'व',
    'ಶ': 'श', 'ಷ': 'ष', 'ಸ': 'स', 'ಹ': 'ह',
    'ಳ': 'ळ', 'ಱ': 'र', 'ೞ': 'ल',
    'ಜ್ಞ': 'ज्ञ', 'ಕ್ಷ': 'क्ष', 'ಶ್ರೀ': 'श्री',
}

# ──────────────────────────────────────────────────────────────────────────
#  Kannada → IAST
# ──────────────────────────────────────────────────────────────────────────

KN_TO_IAST = {
    'ಅ': 'a', 'ಆ': 'ā', 'ಇ': 'i', 'ಈ': 'ī',
    'ಉ': 'u', 'ಊ': 'ū', 'ಋ': 'ṛ', 'ೠ': 'ṝ',
    'ಎ': 'e', 'ಏ': 'ē', 'ಐ': 'ai',
    'ಒ': 'o', 'ಓ': 'ō', 'ಔ': 'au',
    'ಾ': 'ā', 'ಿ': 'i', 'ೀ': 'ī',
    'ು': 'u', 'ೂ': 'ū', 'ೃ': 'ṛ',
    'ೆ': 'e', 'ೇ': 'ē', 'ೈ': 'ai',
    'ೊ': 'o', 'ೋ': 'ō', 'ೌ': 'au',
    'ಂ': 'ṃ', 'ಃ': 'ḥ', '್': '', '಼': '',
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

IAST_TO_PLAIN = {
    'ā': 'a', 'ī': 'i', 'ū': 'u', 'ṛ': 'ri', 'ṝ': 'ri',
    'ē': 'e', 'ō': 'o', 'ṃ': 'm', 'ḥ': 'h',
    'ṅ': 'n', 'ñ': 'n', 'ṭ': 't', 'ḍ': 'd', 'ṇ': 'n',
    'ś': 'sh', 'ṣ': 'sh', 'ḷ': 'l', 'ṟ': 'r', 'ḻ': 'l',
}

KANNADA_CONSONANTS = set(KN_CONSONANTS_TAMIL)
HALANTA = '್'
ANUSVARA = 'ಂ'

KA_VARGA = {'ಕ', 'ಖ', 'ಗ', 'ಘ', 'ಙ'}
CA_VARGA = {'ಚ', 'ಛ', 'ಜ', 'ಝ', 'ಞ'}
TA_VARGA = {'ಟ', 'ಠ', 'ಡ', 'ಢ', 'ಣ'}
THA_VARGA = {'ತ', 'ಥ', 'ದ', 'ಧ', 'ನ'}
PA_VARGA = {'ಪ', 'ಫ', 'ಬ', 'ಭ', 'ಮ'}

VARGA_NASALS = {
    'ka': {'kn': 'ಙ', 'hi': 'ङ', 'ta': 'ங', 'iast': 'ṅ'},
    'ca': {'kn': 'ಞ', 'hi': 'ञ', 'ta': 'ஞ', 'iast': 'ñ'},
    'Ta': {'kn': 'ಣ', 'hi': 'ण', 'ta': 'ண', 'iast': 'ṇ'},
    'ta': {'kn': 'ನ', 'hi': 'न', 'ta': 'ந', 'iast': 'n'},
    'pa': {'kn': 'ಮ', 'hi': 'म', 'ta': 'ம', 'iast': 'm'},
}


def iast_to_plain(text):
    for iast, plain in IAST_TO_PLAIN.items():
        text = text.replace(iast, plain).replace(iast.upper(), plain.upper())
    return text


def get_varga(consonant):
    for varga, letters in (
        ('ka', KA_VARGA), ('ca', CA_VARGA), ('Ta', TA_VARGA),
        ('ta', THA_VARGA), ('pa', PA_VARGA),
    ):
        if consonant in letters:
            return varga
    return None


def varga_nasal(chars, pos, script):
    """Anusvara takes the nasal of the varga of the consonant that follows."""
    for char in chars[pos + 1:]:
        if char in KANNADA_CONSONANTS:
            varga = get_varga(char)
            return VARGA_NASALS[varga][script] if varga else None
        if char.isspace() or char in '|।॥':
            break
    return None


def transliterate_to_tamil(text):
    if not text:
        return ''

    result = []
    chars = list(text)
    i, n = 0, len(chars)

    while i < n:
        if ''.join(chars[i:i + 3]) in SPECIAL_CONJUNCTS_TAMIL:
            result.append(SPECIAL_CONJUNCTS_TAMIL[''.join(chars[i:i + 3])])
            i += 3
            continue
        if ''.join(chars[i:i + 2]) in SPECIAL_CONJUNCTS_TAMIL:
            result.append(SPECIAL_CONJUNCTS_TAMIL[''.join(chars[i:i + 2])])
            i += 2
            continue

        char = chars[i]

        if char == ANUSVARA:
            nasal = varga_nasal(chars, i, 'ta')
            if nasal:
                result.append(nasal + '்')
            else:
                result.append(KN_VOWEL_SIGNS[char])
            i += 1
            continue

        if char in KN_VOWELS:
            result.append(KN_VOWELS[char])
            i += 1
            continue

        if char in KN_CONSONANTS_TAMIL:
            base, sup = KN_CONSONANTS_TAMIL[char]
            i += 1

            if i < n and chars[i] == HALANTA:
                result.append(base + '்')
                i += 1
            elif i < n and chars[i] in KN_VOWEL_SIGNS:
                result.append(base + KN_VOWEL_SIGNS[chars[i]])
                i += 1
            else:
                result.append(base)

            if sup:
                result.append(sup)
            continue

        if char in KN_VOWEL_SIGNS:
            result.append(KN_VOWEL_SIGNS[char])
        else:
            result.append(char)
        i += 1

    output = ''.join(result)
    for initial in ('ன', 'ங', 'ண'):
        output = re.sub(r'(^|[\s।॥|])' + initial, r'\1ந', output)
    return output


def transliterate_to_devanagari(text):
    if not text:
        return ''

    special = {k: v for k, v in KN_TO_DEV.items() if len(k) > 1}
    result = []
    chars = list(text)
    i, n = 0, len(chars)

    while i < n:
        matched = next(
            (length for length in (3, 2) if ''.join(chars[i:i + length]) in special),
            None,
        )
        if matched:
            result.append(special[''.join(chars[i:i + matched])])
            i += matched
            continue

        char = chars[i]
        if char == ANUSVARA:
            nasal = varga_nasal(chars, i, 'hi')
            result.append(nasal + '्' if nasal else KN_TO_DEV[char])
        elif char in KN_TO_DEV:
            result.append(KN_TO_DEV[char])
        else:
            result.append(char)
        i += 1

    return ''.join(result)


def transliterate_to_iast(text):
    if not text:
        return ''

    special = {k: v for k, v in KN_TO_IAST.items() if len(k) > 1}
    result = []
    chars = list(text)
    i, n = 0, len(chars)

    while i < n:
        matched = next(
            (length for length in (3, 2) if ''.join(chars[i:i + length]) in special),
            None,
        )
        if matched:
            result.append(special[''.join(chars[i:i + matched])])
            i += matched
            continue

        char = chars[i]

        if char == ANUSVARA:
            result.append(varga_nasal(chars, i, 'iast') or KN_TO_IAST[char])
            i += 1
            continue

        if char in KANNADA_CONSONANTS:
            result.append(KN_TO_IAST[char])
            i += 1
            if i < n and chars[i] == HALANTA:
                i += 1
            elif i < n and chars[i] in KN_VOWEL_SIGNS and chars[i] != ANUSVARA:
                result.append(KN_TO_IAST[chars[i]])
                i += 1
            else:
                # The inherent 'a'. 'ಂ' is itself listed in KN_VOWEL_SIGNS, so it
                # is deliberately kept out of the branch above: an anusvara is a
                # coda on this syllable, not its vowel, and it has to become the
                # nasal of whatever follows. Written in this order
                # ಪುರಂದರ -> puraṅdara; treating 'ಂ' as a vowel sign gave
                # 'purṃdara', and dropping the inherent 'a' gave 'purndara'.
                result.append('a')
                if i < n and chars[i] == ANUSVARA:
                    result.append(
                        varga_nasal(chars, i, 'iast') or KN_TO_IAST[ANUSVARA])
                    i += 1
        elif char in KN_TO_IAST:
            result.append(KN_TO_IAST[char])
            i += 1
        else:
            result.append(char)
            i += 1

    return ''.join(result)


# ──────────────────────────────────────────────────────────────────────────
#  Lyrics loading + transliteration
# ──────────────────────────────────────────────────────────────────────────

TRANSLIT = {
    'ta': transliterate_to_tamil,
    'hi': transliterate_to_devanagari,
    'en': transliterate_to_iast,
}

LANGUAGES = [
    ('hi', 'देवनागरी'),
    ('kn', 'ಕನ್ನಡ'),
    ('ta', 'தமிழ்'),
    ('en', 'English (IAST)'),
]

VERSE_TYPE_LABELS = {
    'pallavi':     {'kn': 'ಪಲ್ಲವಿ',     'ta': 'பல்லவி',   'hi': 'पल्लवि',    'en': 'Pallavi'},
    'anupallavi':  {'kn': 'ಅನುಪಲ್ಲವಿ',  'ta': 'அனுபல்லவி', 'hi': 'अनुपल्लवि', 'en': 'Anupallavi'},
    'charana':     {'kn': 'ಚರಣ',        'ta': 'சரண',      'hi': 'चरण',       'en': 'Caraṇa'},
    'madhyamakala': {'kn': 'ಮಧ್ಯಮಕಾಲ',  'ta': 'மத்யமகால', 'hi': 'मध्यमकाल',  'en': 'Madhyamakāla'},
    'dhruva':      {'kn': 'ಧ್ರುವ',      'ta': 'த்ருவ',    'hi': 'ध्रुव',     'en': 'Dhruva'},
    'mathya':      {'kn': 'ಮಠ್ಯ',      'ta': 'மட்ய',     'hi': 'मठ्य',      'en': 'Maṭhya'},
    'rupaka':      {'kn': 'ರೂಪಕ',      'ta': 'ரூபக',     'hi': 'रूपक',      'en': 'Rūpaka'},
    'jhampe':      {'kn': 'ಝಂಪೆ',      'ta': 'ஜம்பே',    'hi': 'झंपे',      'en': 'Jhampe'},
    'trividi':     {'kn': 'ತ್ರಿವಿಡಿ',   'ta': 'த்ரிவிடி',  'hi': 'त्रिविडि',   'en': 'Triviḍi'},
    'atta':        {'kn': 'ಅಟ್ಟ',       'ta': 'அட்ட',     'hi': 'अट्ट',      'en': 'Aṭṭa'},
}


def transliterate(text, lang):
    if not text:
        return ''
    return '\n'.join(TRANSLIT[lang](line) for line in str(text).split('\n'))


def verse_label(vtype, lang, number=None):
    if vtype in VERSE_TYPE_LABELS:
        label = VERSE_TYPE_LABELS[vtype].get(lang) or vtype.capitalize()
    elif lang == 'kn':
        label = vtype
    else:
        label = TRANSLIT[lang](vtype)
    return f'{label} {number}' if number else label


def load_lyrics(path):
    """Load one YAML file into a normalised record with all four scripts."""
    with open(path, encoding='utf-8') as handle:
        raw = yaml.safe_load(handle) or {}

    record = {
        'title': {},
        'author': {},
        'raga': {},
        'tala': {},
        'ankita': {},
        'verses': [],
    }

    for field in ('title', 'author', 'raga', 'tala', 'ankita'):
        kannada = str(raw.get(f'{field}_kn') or '').strip()
        record[field]['kn'] = kannada
        for lang in TRANSLIT:
            override = raw.get(f'{field}_{lang}')
            record[field][lang] = str(override) if override else transliterate(kannada, lang)

    for verse in raw.get('verses') or []:
        verse = dict(verse)
        kannada = str(verse.get('kn') or '').strip()
        rendered = {'kn': kannada, 'type': str(verse.get('type') or '').strip(),
                    'number': verse.get('number'), 'subtitle': {}}

        for lang in TRANSLIT:
            override = verse.get(lang) or verse.get(f'text_{lang}')
            rendered[lang] = str(override) if override else transliterate(kannada, lang)

        subtitle_kn = str(verse.get('subtitle_kn') or '').strip()
        rendered['subtitle']['kn'] = subtitle_kn
        for lang in TRANSLIT:
            override = verse.get(f'subtitle_{lang}')
            rendered['subtitle'][lang] = str(override) if override else transliterate(subtitle_kn, lang)

        record['verses'].append(rendered)

    for field in ('category', ON_KEY, 'types', 'festivals'):
        values = raw.get(field)
        if values is None:
            values = raw.get('on') if field == ON_KEY else None
        record[field] = values if isinstance(values, list) else ([values] if values else [])

    return record


def plain_title(record):
    return iast_to_plain(record['title']['en']).strip().title()


def plain_author(record):
    return iast_to_plain(record['author']['en']).strip().title()


def plain_ankita(record):
    """The signature line ("ankita") as written in Roman letters."""
    return iast_to_plain(record['ankita']['en']).strip()


def preview_line(record):
    for verse in record['verses']:
        text = verse['en'].strip()
        if text:
            words = text.split()
            return iast_to_plain(' '.join(words[:4])) + ('…' if len(words) > 4 else '')
    return ''


def slugify(text):
    slug = re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')
    return slug or 'song'


# ──────────────────────────────────────────────────────────────────────────
#  HTML output
# ──────────────────────────────────────────────────────────────────────────

def escape(text):
    return (str(text).replace('&', '&amp;').replace('<', '&lt;')
            .replace('>', '&gt;').replace('"', '&quot;'))


def lines_to_html(text):
    return '<br>\n'.join(line for line in (text or '').strip().split('\n'))


def render_verses(record, lang):
    html = ''
    for verse in record['verses']:
        subtitle = verse['subtitle'][lang] or verse['subtitle']['kn']

        if verse['type'] == 'subtitle':
            if subtitle:
                html += f'<h3 class="verse-subtitle">{escape(subtitle)}</h3>\n'
            continue

        label = subtitle or (verse_label(verse['type'], lang) if verse['type'] else '')
        body = lines_to_html(verse[lang] or verse['kn'])
        if verse['number'] not in (None, ''):
            body += f'<span class="verse-number">॥{verse["number"]}॥</span>'

        label_html = f'<div class="verse-label">{escape(label)}</div>\n' if label else ''
        kind = slugify(verse['type']) if verse['type'] else 'plain'
        html += (f'<div class="verse verse-{kind}">\n  {label_html}'
                 f'<div class="verse-text">{body}</div>\n</div>\n')
    return html


def render_badges(record):
    badges = []
    for value in record['category']:
        badges.append(f'<span class="badge badge-category">{escape(value)}</span>')
    for value in record[ON_KEY]:
        badges.append(f'<span class="badge badge-on">{escape(value)}</span>')
    for value in record['types']:
        badges.append(f'<span class="badge badge-type">{escape(value)}</span>')
    for value in record.get('festivals') or []:
        badges.append(f'<span class="badge badge-festival">{escape(value)}</span>')
    return ''.join(badges)


def render_song_page(record, song, output_dir, template):
    tabs = ''.join(
        f'<button class="tab-btn{" active" if index == 0 else ""}" data-target="{lang}">{label}</button>'
        for index, (lang, label) in enumerate(LANGUAGES)
    )

    panels = ''
    for index, (lang, _) in enumerate(LANGUAGES):
        active = ' active' if index == 0 else ''
        meta = ''
        if record['raga'][lang] or record['tala'][lang]:
            raga = record['raga'][lang] or record['raga']['kn']
            tala = record['tala'][lang] or record['tala']['kn']
            meta = ('<div class="song-meta-row">'
                    f'<span class="meta-item raga">{escape(raga)}</span>'
                    f'<span class="meta-item tala">{escape(tala)}</span></div>')
        ankita = record['ankita'][lang] or record['ankita']['kn']

        panels += f'''
<div class="lang-panel{active}" id="panel-{lang}" data-lang="{lang}">
  <div class="song-header">
    <h1 class="song-title">{escape(record['title'][lang] or record['title']['kn'])}</h1>
    <h2 class="song-author">{escape(record['author'][lang] or record['author']['kn'])}</h2>
    <div class="song-badges">{render_badges(record)}</div>
    {'<h3 class="song-ankita">' + escape(ankita) + '</h3>' if ankita else ''}
    <div class="song-meta">{meta}</div>
  </div>
  <div class="song-body">
    {render_verses(record, lang)}
  </div>
</div>
'''

    html = template
    for token, value in (
        ('{{CSS}}', '../css/style.css'),
        ('{{JS}}', '../js/tabs.js'),
        ('{{HOME}}', '../index.html'),
        ('{{PAGE_TITLE}}', escape(record['title']['kn'] or song['title'])),
        ('{{BREADCRUMB}}', f'<a href="../index.html">Home</a> › {escape(record["title"]["kn"] or song["title"])}'),
        ('{{TABS}}', tabs),
        ('{{PANELS}}', panels),
    ):
        html = html.replace(token, value)

    out_path = output_dir / song['href']
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html, encoding='utf-8')
    return out_path


def render_index_entry(song):
    """One result row: title, author, ankita, type, then the opening line."""
    types = ''.join(
        f'<span class="badge badge-type">{escape(value)}</span>'
        for value in song['types']
    )
    return f'''<li class="song-entry" data-id="{song['id']}">
  <a class="song-link" href="{song['href']}">
    <span class="song-title">{escape(song['title'])}</span>
    <span class="song-author">{escape(song['author'])}</span>
    <span class="song-ankita">{escape(song['ankita'])}</span>
    <span class="song-types">{types}</span>
    <span class="song-preview">{escape(song['preview'])}</span>
  </a>
</li>
'''


def render_index(template, songs, output_dir):
    entries = ''.join(render_index_entry(song) for song in songs)

    index = {
        'songs': [
            {key: song[key] for key in (
                'id', 'href', 'title', 'author', 'ankita', 'preview',
                'category', ON_KEY, 'types', 'festivals',
            )}
            for song in songs
        ],
        # Canonical vocabulary per filter, in the order the tag inputs show them.
        # The browser adds on any value the songs actually use, so a collection
        # that has not been re-tagged yet still filters correctly.
        'vocabularies': {
            'on_who': ON_WHO,
            'category': CATEGORIES,
            'type': TYPES,
            'festivals': FESTIVALS,
            'author': AUTHORS,
            'ankita': ANKITAS,
        },
    }

    # '<' is escaped so the payload can never terminate the host <script> element.
    payload = json.dumps(index, ensure_ascii=False).replace('<', '\\u003c')

    html = template
    for token, value in (
        ('{{TOTAL}}', str(len(songs))),
        ('{{BUILD_DATE}}', date.today().strftime('%d %B %Y')),
        ('{{SONGS}}', entries),
        ('{{INDEX_JSON}}', payload),
    ):
        html = html.replace(token, value)

    (output_dir / 'index.html').write_text(html, encoding='utf-8')


# ──────────────────────────────────────────────────────────────────────────
#  Build
# ──────────────────────────────────────────────────────────────────────────

def build(repo_root):
    repo_root = Path(repo_root).resolve()
    lyrics_dir = repo_root / 'lyrics'
    output_dir = repo_root / 'docs'
    templates_dir = repo_root / 'templates'

    if output_dir.exists():
        shutil.rmtree(output_dir, ignore_errors=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    for folder in ('css', 'js'):
        source = repo_root / folder
        if source.exists():
            shutil.copytree(source, output_dir / folder, dirs_exist_ok=True)

    song_template = (templates_dir / 'song.html').read_text(encoding='utf-8')
    index_template = (templates_dir / 'index.html').read_text(encoding='utf-8')

    yaml_files = sorted(
        list(lyrics_dir.rglob('*.yml')) + list(lyrics_dir.rglob('*.yaml')),
        key=lambda p: str(p).lower(),
    )

    songs = []
    seen_slugs = {}
    failures = []

    for yaml_path in yaml_files:
        rel = yaml_path.relative_to(lyrics_dir)
        try:
            record = load_lyrics(yaml_path)

            stem = slugify(rel.stem)
            slug = stem
            if slug in seen_slugs:
                seen_slugs[stem] += 1
                slug = f'{stem}-{seen_slugs[stem]}'
            else:
                seen_slugs[stem] = 1

            song = {
                'id': slug,
                'href': f'songs/{slug}.html',
                'title': plain_title(record) or rel.stem.replace('_', ' ').title(),
                'author': plain_author(record) or 'Unknown',
                'ankita': plain_ankita(record),
                'preview': preview_line(record),
                'category': record['category'],
                ON_KEY: record[ON_KEY],
                'types': record['types'],
                'festivals': record['festivals'],
            }

            render_song_page(record, song, output_dir, song_template)
            songs.append(song)
            print(f'  OK  {rel}  ->  {song["href"]}')
        except Exception as error:
            failures.append((rel, error))
            print(f'  FAIL {rel}: {error}', file=sys.stderr)

    songs.sort(key=lambda s: (s['category'][0] if s['category'] else '', s['title'].lower()))
    for index, song in enumerate(songs):
        song['order'] = index

    render_index(index_template, songs, output_dir)

    print(f'\nBuilt {len(songs)} songs -> {output_dir}')
    if failures:
        print(f'{len(failures)} file(s) failed.', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(build(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).parent.parent))