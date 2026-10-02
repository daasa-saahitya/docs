# ದಾಸ ಸಾಹಿತ್ಯ · Daasa Sāhitya

A beautifully rendered, multi-script treasury of Haridāsa devotional literature.  
Live site → **https://daasa-saahitya.github.io/docs/**

---

## How it works

```
You edit/add a .yml file in lyrics/
        ↓
Push to GitHub (or commit from the GitHub web/app)
        ↓
GitHub Actions auto-runs scripts/build.py
        ↓
Site regenerates in docs/ and goes live in ~2 minutes
```

## Finding a song on the homepage

The index has no folders. Everything is one flat list you narrow down. Every
filter is a tag input: click one, type a few letters, then press Enter or click
the suggestion to drop it in as a chip. Click the `×` on a chip to remove it.

They sit in two columns — **Category** beside **Type**, **Author** beside
**Ankita** — with **On whom?** and **Festival / Vrata / Jayanti** spanning the
full width above and between them.

- **Search bar + Search button** — matches title, author, ankita and the opening
  line, in any script. Results refresh when you press Search, so half-finished
  selections do not shuffle the list.
- **On whom?** — the deity, Devi, Yatigalu or Dasaru the song is addressed to.
  One flat list: Vishnu, Dashavatara, Varaha, Narasimha, Vamana, Parasurama,
  Rama, Krishna, Padmanabha, Kapila, Dattatreya, Keshavaadi Rupa, Venkatesha,
  Ranga, Hanuma, Bheema, Madhwacharya, Saraswati, Garuda, Sesha, Rudra, Ganesha,
  Subrahmanya, Bhutarajaru, Lakshmi, Durga, Parvati, Bharati,
  Padmanabha Teertharu, Rayaru, Vyasarajaru, Vadirajaru, Sripadarajaru,
  Jayateertharu, Purandara Dasaru, Vijaya Dasaru, Jagannatha Dasaru,
  Gopala Dasaru.
- **Category** — Haadu, Stuti, Suladi, Sloka, Stotra, Kavya, Gadya, Kathe.
- **Type** — Aavahana (Baaro/Baare), Aagamana (Banda/Bandalu), Namaskaara,
  Pooja, Naivedya, Udi Tumbuva, Uruttani, Aarati, Huva / Varava Kodu, Laali,
  Vairagya, Ninda Stuti, Parihara, others.
- **Festival / Vrata / Jayanti** — the 28 occasions in `FESTIVALS`
  (Rama Navami, Krishna Jayanti, Mangala Gowri, Vara Mahalakshmi, Guru
  Poornima, Navaratri, Deepavali, …).
- **Author** — Purandara Dasaru, Raghavendra Teertharu, Vijaya Dasaru, Gopala
  Dasaru, Jagannatha Dasaru, Guru Jagannatha Dasaru, Sripadarajaru, Dhanvantari
  Vittala Dasaru, Vadirajaru, Guru Govinda Vittala Dasaru, Beluru Vaikunta
  Vittala Dasaru.
- **Ankita** — Sampradaya, Purandara Vittala, Hayavadana, Vijaya Vittala,
  Jagannatha Vittala, Gopala Vittala, Ranga Vittala, Sree Krishna, Madhwesha
  Vittala, Madhwesha Krishna, Bheemesha Krishna.
- `/` focuses search, `Esc` resets everything.

Tags combine with AND across filters and OR within a single filter. Each
combination is written to the URL, so you can bookmark or share exactly what you
are looking for.

Each dropdown lists the canonical vocabulary above **first, in that order**, and
then anything else the songs actually use. That is on purpose: it keeps the
existing songs filterable while you re-tag them by hand. The ~59 songs still
tagged with the older wording (`Devaru`, `Sampradaya Haadu`, `Pooje`) still
show up as their own tags. Once a song uses the canonical spelling it lines up
with the dropdown and the duplicate spellings drop away.

### What a result row shows

Title · author · ankita · type · the opening line of the song. No other tags.

---

## Folder structure

```
lyrics/                   ← ONLY edit here
  Devara Nama/
  Gurugalu Nama/
  Suladigalu/
  Vishesha Dinagalu/
  Kavyagalu/
  Stutigalu/
  Stotragalu/
  ... (add as many subfolders as you want)
    song-name.yml

Folder names are only a convenience for you. They are not navigation on the
site — they are read once by scripts/align.py to guess category / on_who /
festivals.

scripts/align.py          ← YAML normaliser + metadata inference (run --apply)
scripts/build.py          ← transliteration + site builder (auto-generates docs/)
templates/                ← HTML layout (edit for design changes)
css/style.css             ← all styles
js/index.js               ← filter + search logic
js/tabs.js                ← tab switching
docs/                     ← AUTO-GENERATED. Never edit manually (published by GitHub Pages)
.github/workflows/build.yml ← automation trigger
```

---

## Adding a new song (from your Android tablet)

### Option A — GitHub website in browser (easiest)
1. Go to https://github.com/daasa-saahitya/docs
2. Navigate to `lyrics/<category>/`
3. Click **Add file → Create new file**
4. Name it: `your-song-name.yml`
5. Paste your content (see `templates/song-template.yml`)
6. (Optional but recommended) After committing, the build will run; if you want to ensure indentation is perfect, run `python scripts/align.py --apply` locally before committing.
7. Click **Commit changes** → site rebuilds automatically

### Option B — GitHub mobile app
1. Open the GitHub app → your repo
2. Browse to `lyrics/<category>/`
3. Tap **+** → **Create file**
4. Same as above

### Option C — Edit existing song
Same steps, just navigate to the existing `.yml` file and tap the **pencil** (edit) icon.

---

## Song file format

Only write **Kannada text** — the build script auto-generates Tamil, Devanagari, and IAST transliterations.

See `templates/song-template.yml` for a copy-paste starter.

### Filterable metadata

These fields drive the index page. `scripts/align.py` fills them in from the
folder path and the title when they are empty, so you only need to write what it
cannot guess. `author_kn` and `ankita_kn` double as the Author and Ankita filter
values, so spell those two the same way in every file.

```yaml
category:               # one of the CATEGORIES below
  - Haadu

on_who:                 # any name from ON_WHO below
  - Lakshmi

types:                  # any of the TYPES below
  - Aarati
  - Pooja

festivals:              # any of the FESTIVALS below
  - Vara Mahalakshmi

ankita_kn: ಪುರಂದರ ವಿಠ್ಠಲ   # one of the ANKITAS below
```

All four lists live at the top of `scripts/align.py`, in the order the dropdowns
should show them — edit them there, not here.

| list | values |
|------|--------|
| `CATEGORIES` | Haadu, Stuti, Suladi, Sloka, Stotra, Kavya, Gadya, Kathe |
| `TYPES` | Aavahana (Baaro/Baare), Aagamana (Banda/Bandalu), Namaskaara, Pooja, Naivedya, Udi Tumbuva, Uruttani, Aarati, Huva / Varava Kodu, Laali, Vairagya, Ninda Stuti, Parihara, others |
| `ON_WHO` | Vishnu, Dashavatara, Varaha, Narasimha, Vamana, Parasurama, Rama, Krishna, Padmanabha, Kapila, Dattatreya, Keshavaadi Rupa, Venkatesha, Ranga, Hanuma, Bheema, Madhwacharya, Saraswati, Garuda, Sesha, Rudra, Ganesha, Subrahmanya, Bhutarajaru, Lakshmi, Durga, Parvati, Bharati, Padmanabha Teertharu, Rayaru, Vyasarajaru, Vadirajaru, Sripadarajaru, Jayateertharu, Purandara Dasaru, Vijaya Dasaru, Jagannatha Dasaru, Gopala Dasaru |
| `FESTIVALS` | Rama Navami, Krishna Jayanti, Mangala Gowri, Vara Mahalakshmi, Vamana Jayanti, Swarna Gowri Vrata, Jyeshta Devi Vrata, Gowri Tritiya, Diwashi Gowri Vrata, Ananta Chaturdashi, Guru Poornima, Navaratri, Makara Shankaranti, Deepavali, Ganesha Chaturthi, Saraswati Pooja, Mahalaya Paksha, Adhika Maasa, Chaturmaasya, Ekadashi, Surya Grahana, Chandra Grahana, Dhanvantri Jayanti, Srinivasa Kalyana, Yugaadi, Naga Chaturthi, Garuda Panchami, Shivaratri |
| `AUTHORS` | Purandara Dasaru, Raghavendra Teertharu, Vijaya Dasaru, Gopala Dasaru, Jagannatha Dasaru, Guru Jagannatha Dasaru, Sripadarajaru, Dhanvantari Vittala Dasaru, Vadirajaru, Guru Govinda Vittala Dasaru, Beluru Vaikunta Vittala Dasaru |
| `ANKITAS` | Sampradaya, Purandara Vittala, Hayavadana, Vijaya Vittala, Jagannatha Vittala, Gopala Vittala, Ranga Vittala, Sree Krishna, Madhwesha Vittala, Madhwesha Krishna, Bheemesha Krishna |

A value that is not on its list is **kept as typed** and shows up in the dropdown
after the canonical entries, so nothing ever disappears. `ALIASES` in the same
file maps older spellings onto the current ones when you run `--apply`
(`Sampradaya Haadu` → `Haadu`, `Pooje` → `Pooja`, and so on).

### Normalising the YAML

Lyrics YAML is indentation sensitive. `scripts/align.py` rewrites every file
with canonical 2-space indentation and literal block scalars, so a file pasted
from anywhere still parses.

```bash
python scripts/align.py            # dry run, lists what would change
python scripts/align.py --apply    # rewrite the files
```

It is idempotent and non-destructive: values you have set by hand are never
overwritten, only empty ones are filled.

### Full file format

```yaml
title_kn:  ಭಾಗ್ಯದ ಲಕ್ಷ್ಮಿ ಬಾರಮ್ಮ    # Kannada title (REQUIRED)
author_kn: ಪುರಂದರದಾಸ               # Kannada author (REQUIRED)
raga_kn:   ಮಧ್ಯಮಾವತಿ              # optional
tala_kn:   ಆದಿ                     # optional

verses:
  - type: pallavi
    kn: |
      ಲೈನ್ ಒಂದು
      ಲೈನ್ ಎರಡು

  - type: anupallavi
    kn: |
      ಅನುಪಲ್ಲವಿ ಸಾಲುಗಳು

  # Mid-song section heading:
  - type: subtitle
    subtitle_kn: ಚರಣಗಳು

  - type: None
    number: 1
    subtitle_kn: ಧ್ರುವತಾಳ
    kn: |
      ಮೊದಲ ಚರಣ

  - type: None
    number: 2
    subtitle_kn: ಮಟ್ಟತಾಳ
    kn: |
      ಎರಡನೆಯ ಚರಣ
```

### Verse types available
| type | meaning |
|------|---------|
| `pallavi` | Pallavi |
| `anupallavi` | Anupallavi |
| `None` | Caraṇa (add `number: 1`, `number: 2` … and `subtitle_kn:` for tala name) |
| `madhyamakala` | Madhyamakāla section |
| `subtitle` | Mid-song heading (use `subtitle_kn:`) |

### Correcting auto-transliteration

If the auto-generated Tamil/Devanagari/IAST has errors, add the correction to the YAML:

```yaml
title_kn: ರಾಮ ದೇವರ ಸುಳಾದಿ
title_ta: ராம தே³வர ஸுளாதி³    # only add if auto-generation is wrong
```

The build script uses your manual override when present, otherwise auto-generates.

---

## Tamil superscript system

The following Kannada consonants are transliterated with Tamil superscripts:

| Kannada | Tamil | | Kannada | Tamil |
|---------|-------|-|---------|-------|
| ಕ | க | | ತ | த |
| ಖ | க² | | ಥ | த² |
| ಗ | க³ | | ದ | த³ |
| ಘ | க⁴ | | ಧ | த⁴ |
| ಟ | ட | | ಪ | ப |
| ಠ | ட² | | ಫ | ப² |
| ಡ | ட³ | | ಬ | ப³ |
| ಢ | ட⁴ | | ಭ | ப⁴ |

Special: ಜ್ಞ → க்³ஞ · ಕ್ಷ → க்ஷ · ಶ್ರೀ → ஸ்ரீ

---

## Moving a song to a different category

In GitHub: navigate to the file → Edit → change the filename path at the top to include the new folder → Commit.  
Or: create the new file, paste content, commit; then delete the old file.

---

## Deleting a song

Navigate to the file → click the **⋮** or **trash** icon → Delete → Commit.

---

## Local preview (optional, on a laptop/desktop)

```bash
git clone https://github.com/daasa-saahitya/docs.git
cd docs
pip install pyyaml
python scripts/align.py --apply
python scripts/build.py .
# Open docs/index.html in your browser
```

---

## GitHub Pages setup (one-time)

In your repo → **Settings → Pages**:
- Source: **Deploy from a branch**
- Branch: `main` · Folder: `/docs`
- Save → your site will be at https://daasa-saahitya.github.io/docs/

---

*ಶ್ರೀ ಕೃಷ್ಣಾರ್ಪಣಮಸ್ತು*
