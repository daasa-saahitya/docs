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
Site regenerates in site/ and goes live in ~2 minutes
```

---

## Folder structure

```
lyrics/                   ← ONLY edit here
  dasara-padagalu/
    song-name.yml
  stuti/
  suladi/
  stotra/
  guru-parampara/
  sampradaya-pooja-vidhana/
  sthri-dharma/
  ... (add as many subfolders as you want)

scripts/build.py          ← transliteration + site builder (don't edit unless needed)
templates/                ← HTML layout (edit for design changes)
css/style.css             ← all styles
js/tabs.js                ← tab switching
site/                     ← AUTO-GENERATED. Never edit manually.
.github/workflows/build.yml ← automation trigger
```

---

## Adding a new song (from your Android tablet)

### Option A — GitHub website in browser (easiest)
1. Go to https://github.com/daasa-saahitya/docs
2. Navigate to `lyrics/<category>/`
3. Click **Add file → Create new file**
4. Name it: `your-song-name.yml`
5. Paste your content (see format below)
6. Click **Commit changes** → site rebuilds automatically

### Option B — GitHub mobile app
1. Open the GitHub app → your repo
2. Browse to `lyrics/<category>/`
3. Tap **+** → **Create file**
4. Same as above

### Option C — Edit existing song
Same steps, just navigate to the existing `.yml` file and tap the **pencil** (edit) icon.

---

## Song file format

```yaml
title_kn:  ಭಾಗ್ಯದ ಲಕ್ಷ್ಮಿ ಬಾರಮ್ಮ    # Kannada title (REQUIRED)
author_kn: ಪುರಂದರದಾಸ               # Kannada author (REQUIRED)
raga_kn:   ಮಧ್ಯಮಾವತಿ              # optional
tala_kn:   ಆದಿ                     # optional
description_kn: ದಾಸರ ಪದ            # optional extra note

# You can manually override any auto-transliteration:
title_ta:  ""    # leave blank = auto-generated
title_hi:  ""
title_en:  ""

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

  - type: charana
    number: 1
    kn: |
      ಮೊದಲ ಚರಣ

  - type: charana
    number: 2
    kn: |
      ಎರಡನೆಯ ಚರಣ
```

### Verse types available
| type | meaning |
|------|---------|
| `pallavi` | Pallavi |
| `anupallavi` | Anupallavi |
| `charana` | Caraṇa (add `number: 1`, `number: 2` …) |
| `madhyamakala` | Madhyamakāla section |
| `subtitle` | Mid-song heading (use `subtitle_kn:`) |

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
python scripts/build.py .
# Open site/index.html in your browser
```

---

## GitHub Pages setup (one-time)

In your repo → **Settings → Pages**:
- Source: **Deploy from a branch**
- Branch: `main` · Folder: `/site`
- Save → your site will be at https://daasa-saahitya.github.io/docs/

---

*ಶ್ರೀ ಕೃಷ್ಣಾರ್ಪಣಮಸ್ತು*
