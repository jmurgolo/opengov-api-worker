# OpenGov API Integration - Copilot Instructions

## Project Overview
This is a multi-step ETL pipeline that fetches permit/licensing records from the OpenGov PLCE API for Springfield, MA. It uses a **sequential numbered workflow** (01→02→03) where each script depends on the previous one's output.

## Architecture & Data Flow

```
01_fetch_records.py → data_records.json → 02_fetch_addresses.py → data_full_records.json
                                                                            ↓
                                                                  03_inspect_relationships.py
```

### Critical Design Pattern: Data Flattening
The API returns nested JSON (`data.attributes.field`), but we **deliberately flatten** it to top-level fields:
```python
# BAD (preserves nesting):
{"id": "123", "attributes": {"number": "969380", "status": "COMPLETE"}}

# GOOD (flattened structure):
{"id": "123", "number": "969380", "status": "COMPLETE"}
```
See [01_fetch_records.py](01_fetch_records.py#L52-L68) for the canonical implementation.

## Sequential Workflow

### Script 1: Fetch Records ([01_fetch_records.py](01_fetch_records.py))
- **Purpose**: Paginated fetch of all records (50/page, max 5 pages)
- **Output**: `data_records.json` (flattened structure)
- **Key Pattern**: Uses prepared requests to preserve custom query params without URL encoding issues
- **Runs independently** - no input files needed

### Script 2: Fetch Addresses ([02_fetch_addresses.py](02_fetch_addresses.py))
- **Purpose**: Enrich records with location data via detail API endpoint
- **Input**: `data_records.json` (from step 1)
- **Output**: `data_full_records.json`
- **Smart Filtering**: Automatically skips:
  - Records with `status == "DRAFT"`
  - Records with `number == null`
  - Already-processed records (resume on crash)
- **Incremental Saves**: Checkpoints every 20 records to prevent data loss
- **Location Resolution**: Tries `locations[0]` array first, falls back to `attributes` fields

### Script 3: Inspect Relationships ([03_inspect_relationships.py](03_inspect_relationships.py))
- **Purpose**: Debug tool to examine API relationships and data structure
- **Usage**: Set `TEST_ID` variable to inspect a specific record
- **Not part of main pipeline** - used for troubleshooting

## Configuration & Security

### API Authentication ([config.py](config.py))
- Uses **Token-based auth** (not Bearer)
- Headers: `Authorization: Token {API_KEY}`, `Accept: application/json`
- ⚠️ **API key is hardcoded** - treat as development-only code
- Community identifier embedded in BASE_URL: `https://api.plce.opengov.com/plce/v2/springfieldma`

### SSL Handling
All scripts disable SSL verification (`verify=False`) and suppress warnings:
```python
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
resp = s.get(url, verify=False)
```

## Common Patterns

### Session Management
Use `requests.Session()` for connection reuse:
```python
s = requests.Session()
s.headers.update(headers)
resp = s.get(url, verify=False)  # Reuses connection
```

### Pagination
```python
page_num = 1
page_size = 50
url = f"{BASE_URL}/records?page[number]={page_num}&page[size]={page_size}"
```

### Error Handling Philosophy
- Prints emojis for visual status (🚀, ✅, ❌, ⚠️)
- Continues on individual record failures
- Saves incrementally to prevent total data loss

## Developer Workflow

### Running the Pipeline
```powershell
python 01_fetch_records.py   # Fetch initial records
python 02_fetch_addresses.py # Enrich with addresses
```

### Debugging Failed Records
1. Check status in [data_records.json](data_records.json) - DRAFT records are auto-skipped
2. Set `TEST_ID` in [03_inspect_relationships.py](03_inspect_relationships.py#L8)
3. Run script to see raw API response structure

### Resume After Crash
Script 02 automatically resumes - it:
1. Loads existing `data_full_records.json`
2. Skips already-processed IDs
3. Continues from where it left off

## API Reference
- **Docs**: https://developer.opengov.com/catalog/plc-api/
- **List Endpoint**: `/plce/v2/{community}/records` (paginated)
- **Detail Endpoint**: `/plce/v2/{community}/records/{id}` (relationships)

## Data Files
- `data_records.json` - Flattened records from step 1
- `data_full_records.json` - Records enriched with addresses from step 2
- `data_queue.json`, `data_address_errors.json` - Legacy/unused files
