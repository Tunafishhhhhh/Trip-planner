# AGENTS.md

Personal travel-planning dashboard: a single-file Streamlit app (`app.py`) that reads and
writes plain CSV/text files in this folder. No package, no build step, no tests, no CI, not a
git repo.

## Run

- Always launch from the repo root: `streamlit run app.py`
- Every data file is opened by **relative path** (`itinerary.csv`, `title.txt`, ...). Running
  from another directory will create empty files / crash.
- `pip install -r requirements.txt` (unpinned). No virtualenv or lockfile is committed.

## Data files are the database

The app has no DB — it treats these repo files as persistent state. Edits in the UI write
straight back to disk, then call `st.rerun()`. Preserve that pattern; do not add a database.

| File | Columns / format |
| --- | --- |
| `itinerary.csv` | `day,location_name,lat,lon,note` |
| `hotels.csv` | `hotel_name,address,check_in,check_out,nights,lat,lon,note` |
| `links.csv` | `title,category,url,note` |
| `transport.csv` | `transport_name,route,status,note,origin,destination,date` |
| `settings.json` | `{"total_days": int, "start_date": "YYYY-MM-DD"}` (UI prefs) |
| `title.txt` | page title (single line) |
| `flight.txt` | free-text flight notes |

- `transport.csv` **is not read by `app.py`** — it is orphaned data (hand-edited). It also uses
  `YYYY/MM/DD` dates, unlike the ISO `YYYY-MM-DD` dates in `hotels.csv`. Don't assume it is wired
  into the UI; wiring it up would be new work.

## Other gotchas

- `generate_map.py` is a **standalone one-off script**, not imported by the app. It reads
  `itinerary.csv` and writes `travel_map.html`, and assumes the itinerary is non-empty
  (`df['lat'].iloc[0]`). The app builds its own folium map separately (the cached
  `build_map_html` helper).
- Map tiles are pinned to `Esri.WorldStreetMap` on purpose — the default OpenStreetMap tiles
  return 403. Keep Esri (or another non-OSM provider).
- Adding a place/hotel geocodes via `geopy` + Nominatim at runtime: needs internet, is slow, and
  is rate-limited. Geocoded `lat`/`lon` are stored in the CSVs.
- `hotels.csv` columns are backfilled at load time, so older rows may be missing fields.
- Day tabs and the map legend derive dates from `settings.json` `start_date`; the folium map is
  built by the cached `build_map_html(...)` and auto-fits bounds, so changing the data or start
  date invalidates it.
- The `@st.dialog` delete confirmations **do not execute under
  `streamlit.testing.v1.AppTest`** (uploaded-fragment reruns are not simulated — Streamlit's own
  dialog example fails there too). Verify delete flows manually in a browser.
- Streamlit is 1.65: `use_container_width=True` and `st.components.v1.html` emit deprecation
  warnings but still work. `st.iframe` is not a drop-in for the latter (it takes a URL).

## Conventions

- UI strings, comments, and error messages are **Traditional Chinese** — match them (not
  Simplified).
- `app.py` uses **2-space indentation** throughout. Match it.
- `.streamlit/config.toml` forces a dark theme; `app.py` CSS is written to look right in both
  light and dark.
- Streamlit session state is seeded from the files on first load and edited via `st.data_editor`
  + `st.session_state`.
