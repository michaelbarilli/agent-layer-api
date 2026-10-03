# Agent Layer Dataset #001 MVP

Source: Herefordshire Council NNDR snapshots, 1 Aug 2026 and 1 Sep 2026.
Licence recorded by project: OGL-3.0.

## Build result
- August records: 3666
- September records: 3686
- New properties: 42
- Removed properties: 22
- Modified properties: 58

## Files
- agent_layer.db — SQLite MVP database
- current_properties.jsonl — normalized September records
- changes_aug_to_sep.jsonl — derived change events
- api.py — minimal read-only JSON API

## Run locally
Place api.py and agent_layer.db in the same folder:
python api.py

Then:
GET http://127.0.0.1:8080/v1/health
GET http://127.0.0.1:8080/v1/authorities
GET http://127.0.0.1:8080/v1/commercial-property/search?postcode=HR4
GET http://127.0.0.1:8080/v1/commercial-property/changes?limit=10


## Intelligence/API upgrade
Event-level change table added with correction classification and confidence. FastAPI app is in `app.py`; machine discovery is in `llms.txt`.

### Event counts
- RATEPAYER_CHANGED: 46
- NEW_PROPERTY: 42
- LIABILITY_START_CHANGED: 34
- REMOVED_PROPERTY: 22
- ADDRESS_CHANGED: 7
- LIKELY_NAME_CORRECTION: 3
- POSTCODE_CHANGED: 2
