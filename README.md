# London's mental health services: who provides care, and where is more support needed?

A data pipeline from the CQC API into DuckDB and a Streamlit app, showing who provides London's registered mental health services and where none are registered locally.

## 1. About me and why I'm applying

I started my career in the NHS as a mental health practitioner, working across different psychiatric settings, including inpatient units and crisis services. I then moved into mental health research, working on improving the referral pathway for patients with complex trauma, and co-authored a systematic review on how they seek help (Rowe et al., 2026). Seeing how data could influence the redesign of a whole care pathway really fascinated me; I decided to upskill and  completed my master's in Computer Science. I now work as a data analyst at a therapeutic clinic, building Power BI dashboards that help management with scheduling and planning.

I mostly work at the reporting end, and I've seen how much the answers depend on how the data was collected and structured long before it reaches a dashboard. I want to be able to work across the whole data cycle, from pulling the data in to the final output. I'm applying to the Data School because I'm eager to learn that properly and apply it on placements. My NHS work taught me to work closely with people and research made me approach my work systematically, and now I would like to strengthen the engineering and consulting skills.

## 2. What I built and who is the audience

A data pipeline and a Streamlit dashboard on the CQC (Care Quality Commission) register, the public list of registered health and care services in England. It pulls every currently registered mental health and substance misuse service in London from the CQC API, keeps the raw records, models them in DuckDB with SQL, tests the results, and shows them in the app.

It's for service planners in London, for example at an ICB, who need to know what's registered where and who provides it. It's also useful for anyone looking for a registered mental health service.

The question: who provides London's registered mental health services (NHS or independent), where are they, and where might more support be needed? It starts with which boroughs have no service of a given type registered locally, and I'm open about what the register can't show.

The dashboard lets you:
- see how many services there are, and how many are run by the NHS or by independent providers
- compare who provides each type of service, and how that differs across London's ICBs
- see which boroughs have the most services
- see which needs have no local service in the most boroughs, borough by borough
- look up services by borough, who they're for and who provides them, on a map and in a table

## 3. The data
I used the [CQC public API](https://api-portal.service.cqc.org.uk/), which lists every registered health and care site in England, one record per site, with nested lists of service types and specialisms. It's the only open, record-level source I found for mental health services. Fingertips, which I looked at first, was already aggregated by area and year.

The list call (`/locations`) only gives an ID, name and postcode, so I filtered it to London and four mental health and substance misuse service types, then called `/locations/{id}` for each site to get the full record. From each record I use the borough, ICB, who runs it (NHS, independent or other), whether it's still registered, its location on a map, and its service types and specialisms.

The records are nested JSON, and empty fields are just left out, so they don't all look the same. The list includes services that have closed, so I only keep the registered ones. And CQC overwrites a provider's history when it changes, so this is a snapshot of today, not change over time.

CQC only registers regulated care. From working on the front line I knew some things would be missing, and they were: NHS community teams sit under their trust's head office, some private mental health clinics are registered as GP services, and charities, hostels and helplines aren't there at all. I looked beyond CQC for this support (the Charity Commission, Hub of Hope, Open Referral, council directories), but none could be searched by area and type of support, so they're future extensions.

The API needs a free key, which I keep in a local `.env` file that isn't committed. The raw responses are saved unchanged in `data/raw/`, so anyone can run the rest of the pipeline without a key.

## 4. How it works

```
CQC API → extract/extract.py → data/raw/*.json (459 files, committed)
        → sql/01_raw.sql     → raw_locations   (one row per file)
        → sql/02_staging.sql → stg_locations, stg_service_types, stg_specialisms
        → sql/03_mart.sql    → mart_services, mart_gaps + 5 summary tables for the app
        → tests/             → 6 checks
        → app/app.py         → Streamlit app
```

1. **Understanding the API first.** I mapped the CQC API from its docs: 14 read-only endpoints in three patterns (lists, single items, and "belonging to" calls), and the main entities and how they relate (one provider runs many locations, and each location has many reports). Everything my question needed was inside the Location record, so I only needed two calls: the filtered list, then one detail call per location. The docs' example responses turned out to be unreliable (swapped IDs, a London site in a Lincolnshire ICB, `"Y"` where the real data says `true`), so I used them for structure and checked values against the calls.
2. **Looking and checking first.** Made one list call and one detail call (`extract/check_api.py`) to see what came back. The list only gives an ID, name and postcode, so I did a detail call for every site.
3. **Choosing the filter.** Tested two ways of picking mental health services: by primary inspection category (339 London sites) and by service type (459). My first service type test returned 0, because of the short names from CQC's published file and the filter wants the long description. Once fixed, I chose service type because it's broader, and every record still has the category if I want to narrow it later.
4. **Extracting.** `extract/extract.py` pages through the filtered list, calls the detail endpoint for each site and saves each record untouched as its own JSON file, named by its location ID. It retries only when CQC is busy or has a server error, and skips files it already has, so it's idempotent: it can be stopped and re-run without creating duplicates. A re-run doesn't refresh existing files, so to pull fresh data, clear `data/raw/` first.
5. **Loading.** `read_json_auto` failed because the records don't all have the same fields, and `union_by_name` ran out of memory. So `sql/01_raw.sql` keeps each record untouched as one JSON value, one row per file, and staging pulls out the fields I need.
6. **Staging.** The data showed 301 of the 459 sites had closed, so `sql/02_staging.sql` keeps only the 158 currently registered ones. It gives the fields plain names, groups CQC's provider types into NHS, independent or other with a `CASE`, turns the map coordinates into numbers with `TRY_CAST`, and shortens the ICB names. Service types and specialisms go into their own tables (using `unnest`), because one site can have several.
7. **The mart.** When I joined services straight to their specialisms, 158 rows turned into 649 (fan-out), so `sql/03_mart.sql` groups each service's specialisms first, then joins, which keeps `mart_services` at one row per service. I also noticed only 32 of London's 33 areas had a service, so the empty one would have disappeared from the borough view. The mart starts from a list of all 33, so `mart_gaps` shows it as 0 (33 areas × 12 specialisms = 396 rows).
8. **Summary tables for the dashboard.** Once I'd decided which questions the dashboard should answer, I added a small summary table to the mart for each one (`mart_summary` for the headline numbers, plus `mart_specialism_run_by`, `mart_icb_run_by`, `mart_borough_run_by` and `mart_gaps_summary`).
9. **Testing.** `tests/test_pipeline.py` has 6 checks, most of them from a problem above: the mart isn't empty, every raw file is loaded (459 files = 459 rows), IDs are unique and never empty, only current services are kept, the mart is still one row per service (no fan-out), and all 33 London areas appear in the borough-by-specialism table (`mart_gaps`).

## 5. The app
The dashboard goes in this order: who provides services, where they are, where more support may be needed, then a look-up and what the register can't show.

Decisions behind it:

- Each section answers one question, and I cut charts that didn't help a planner decide anything (the most common service types, and a count of services per ICB).
- Each chart's subtitle states the finding with a number, and the ⓘ icons hold definitions, so the page stays uncluttered.
- Colours mean one thing each: purple = NHS, pink = independent, grey = other, amber = none registered locally.
- Filters use OR within a filter and AND across filters: someone picking several needs wants any service that matches, not only services that cover all of them.

I checked the results against services I know from NHS frontline work. The Tavistock Centre came back with mental health as its primary category, as I'd expect. But a private ADHD clinic I know is registered as a GP service, so a mental health filter misses it. A women's crisis house is covered under its NHS trust rather than listed as its own site, and a homelessness charity's hostels don't appear at all.

## 6. How to run it

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

python3 load.py          # builds data/cqc.duckdb from the committed raw files (no API key needed)
python3 -m pytest        # 6 tests (run load.py first)
streamlit run app/app.py
```

To refresh the data from CQC, copy `.env.example` to `.env`, add a free CQC API key, and run `python3 extract/extract.py` before `load.py`.

## 7. Limitations and what I would do next

Limitations:

- It shows supply only: where services are registered. "Where is more support needed?" is answered as a starting point (no service registered locally), without demand, and counts aren't adjusted for borough population.
- It counts registered sites, not capacity, and it's a snapshot of the register on 6 Nov 2026.
- A service with several specialisms counts in each.
- NHS community teams sit under trust head offices, so community services may look low in some boroughs.

What I would do next:
- Add demand (borough population and how common each condition is) and travel distance to the nearest service, to move from "none registered locally" to where more support is actually needed.
- Re-run the extract regularly to build up history, since the register overwrites changes.
- Separate community mental health services out, and flag head offices.
- Add tests on the summary tables (e.g. the borough counts add up to 158).

## 8. Where AI helped

I used AI as a development tool throughout. I've worked with JSON and APIs before (I've built a Django app), and I have used SQL, but it had been a while since I'd written SQL at this level, so I leaned on it quite a bit for syntax, especially for querying nested JSON in DuckDB (`->>`, `unnest`, `FILTER`). I checked what it suggested against real API responses and query results, and adapted it as the project went on.

It helped me:
- think through and refine the pipeline's structure (raw → staging → mart)
- get to grips with tools that were new to me, mainly DuckDB's JSON functions and Streamlit
- review my Python and SQL, and work through errors when things broke

The Streamlit app: AI wrote the Streamlit code from my design, scope and narrative, following the structure I use for my Tableau Public dashboards. AI works best when you understand the foundations well enough to guide it. Without that, it's easy for a project to drift out of scope.
