# POC demo output — semantic retrieval over Amharic text

Model: `intfloat/multilingual-e5-base` (768-dim). Index: 5 placeholder chunks
in `sample_chunks.json`. Each query below deliberately avoids the exact
vocabulary of its target chunk, to demonstrate a semantic match a keyword
search would miss or under-rank.

## Query 1 — "የቡና ንግድ በኢትዮጵያ ምጣኔ ሀብት ላይ ያለው ተጽእኖ"
*(the impact of the coffee trade on Ethiopia's national economy)*

| rank | similarity | text |
|---|---|---|
| **1** | **0.6759** | ቡና በኢትዮጵያ ውስጥ ትልቅ **የኢኮኖሚ** ጠቀሜታ አለው... |
| 2 | 0.6184 | የቡና ሥነ ሥርዓት የኢትዮጵያ ባህል አንድ ወሳኝ አካል ነው... |
| 3 | 0.6082 | የኢትዮጵያ ቡና በዓለም ገበያ ከፍተኛ ተፈላጊነት አለው... |

Query says **ምጣኔ ሀብት** ("national economy"); the winning chunk says
**ኢኮኖሚ** (economy, a loanword) — different lexical items, same concept.
Zero shared content words between query and top hit.

## Query 2 — "ልጆች በትምህርት ቤት ምን ይማራሉ"
*(what do children learn in school)*

| rank | similarity | text |
|---|---|---|
| **1** | **0.5611** | ትምህርት ለሀገር ልማት ወሳኝ ሚና ይጫወታል... |
| 2 | 0.5126 | የቡና ሥነ ሥርዓት የኢትዮጵያ ባህል አንድ ወሳኝ አካል ነው... |
| 3 | 0.5035 | የአማርኛ ቋንቋ በኢትዮጵያ ውስጥ በሰፊው ይነገራል... |

## Query 3 — "እንግዳ ሲመጣ የሚደረግ ወግ"
*(the custom performed when a guest arrives)*

| rank | similarity | text |
|---|---|---|
| **1** | **0.6022** | የቡና ሥነ ሥርዓት የኢትዮጵያ ባህል አንድ ወሳኝ አካል ነው፣ **እንግዶችን** ለማክበር ይካሄዳል። |
| 2 | 0.5221 | የአማርኛ ቋንቋ በኢትዮጵያ ውስጥ በሰፊው ይነገራል... |
| 3 | 0.5212 | ትምህርት ለሀገር ልማት ወሳኝ ሚና ይጫወታል... |

Query's **ወግ** ("custom/tradition") never appears in the winning chunk,
which instead says **ሥነ ሥርዓት** ("ceremony/ritual") — different word,
same concept. Query's **እንግዳ** (guest, singular) also doesn't string-match
the chunk's **እንግዶችን** (guests, inflected/plural form) — a keyword search
without stemming would miss this pairing entirely.

## To reproduce

```bash
cd backend/poc
python build_index.py
python query.py "የቡና ንግድ በኢትዮጵያ ምጣኔ ሀብት ላይ ያለው ተጽእኖ"
python query.py "ልጆች በትምህርት ቤት ምን ይማራሉ"
python query.py "እንግዳ ሲመጣ የሚደረግ ወግ"
```

## Caveat

5 chunks is not a corpus — this validates the *mechanism* (embed, store,
retrieve by cosine similarity, get a semantically correct top hit), not
retrieval quality at scale. Real validation happens once Ferid's actual
OCR'd chunks replace `sample_chunks.json`, and again once the gold query
set exists (see `ARCHITECTURE.md` Risk 5).
