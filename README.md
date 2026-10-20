# Amharic Document Digitization & Semantic Retrieval

Senior project — ingests scanned Amharic PDFs, OCRs and normalizes the text,
and lets users semantically search the corpus with results highlighted back
to the source page. See [`ARCHITECTURE.md`](ARCHITECTURE.md) for the full
system design: component diagram, data contracts, schema, search flow, auth
boundary, and the riskiest decisions the team should discuss explicitly.

## Team & lanes

| Lane | Owner | Directory | Status |
|---|---|---|---|
| A — Preprocessing | Kibreab | [`preprocessing/`](preprocessing/) | not started |
| B — OCR + normalization | Ferid | [`ocr/`](ocr/) | not started |
| C — Backend + retrieval | Semir | [`backend/`](backend/) | Phase 1 POC done — see [`backend/poc/`](backend/poc/) |
| D — Frontend | Yassin | [`frontend/`](frontend/) | delivered, tested against a mock backend only — real-backend integration pending |

Each lane directory has its own README pointing at the exact section of
`ARCHITECTURE.md` that defines its inputs/outputs — those contracts are the
whole coordination surface between lanes, freeze them before building.
