# Council Implementation Notes

Technical notes on each council's bin collection website, for contributors adding new councils.

---

## Implemented

### East Dunbartonshire

- **Status:** Implemented
- **URL:** `https://www.eastdunbarton.gov.uk/services/a-z-of-services/bins-waste-and-recycling/bins-and-recycling/collections/`
- **Method:** GET with `?uprn=<UPRN>` query parameter; returns server-rendered HTML
- **Address search:** GET `https://www.eastdunbarton.gov.uk/umbraco/api/bincollection/GetUPRNs?address=<query>` returns JSON array with `uprn`, `addressLine1`, `town`, `postcode` fields
- **Parsing:** Regex on HTML rows: `<td class="<bin-class>"><name></td> ... <span><date></span>`. Bin class is the CSS class name.
- **Date format:** `%A, %d %B %Y` (e.g. "Monday, 21 April 2025")
- **Bin types:** `food-caddy`, `garden-bin`, `rubbish-bin` (CSS class names)

### Clackmannanshire

- **Status:** Implemented
- **URL:** `https://www.clacks.gov.uk/environment/wastecollection/`
- **Method:** GET with `?pc=<postcode>` returns server-rendered HTML with property links
- **Address search:** GET with postcode; parse `href="/environment/wastecollection/id/(\d+)/">(.*?)</a>`
- **Property page:** `https://www.clacks.gov.uk/environment/wastecollection/id/<id>/` — links to `.ics` calendar file
- **ICS parsing:** RRULE-based weekly schedule; custom parser expands `FREQ=WEEKLY` with `INTERVAL` and `UNTIL` to find next date
- **Bin types:** `Grey bin`, `Green bin`, `Blue bin`, `Food caddy` (from ICS SUMMARY field)

### Falkirk

- **Status:** Implemented
- **URL:** `https://recycling.falkirk.gov.uk/`
- **Method:** Clean REST API — no auth needed
- **Address search:** GET `https://recycling.falkirk.gov.uk/search/?query=<postcode or address>` — parse `href="/collections/(\d+)">(.*?)</a>`
- **Collection data:** GET `https://recycling.falkirk.gov.uk/api/collections/<uprn>` — returns 302 redirect to Azure blob with JSON: `{"collections": [{"type": "<name>", "dates": ["2025-04-21", ...]}, ...]}`
- **Notes:** Must pass `allow_redirects=True` to follow the Azure blob redirect
- **Bin types:** `Food caddy`, `Blue bin`, `Green bin`, `Burgundy bin`, `Black box`, `Brown bin`

---

## Investigated — Not Yet Implemented

### North Ayrshire

- **Status:** Not implemented — good candidate
- **Approach:** ArcGIS REST API, single GET per UPRN
- **API:** `https://www.maps.north-ayrshire.gov.uk/arcgis/rest/services/AGOL/YourLocationLive/MapServer/8/query?where=UPRN='<UPRN>'&outFields=*&f=json`
- **Response fields:** `COLLECTION_DAY`, `BLUE_DATE_TEXT`, `GREY_DATE_TEXT`, `PURPLE_DATE_TEXT`, `BROWN_DATE_TEXT` (dates as `dd/mm/yyyy`)
- **Remaining work:** Find how to resolve a postcode/address to UPRN (likely a separate address search API on their site or standard OS Places)
- **Notes:** The website is a React SPA but the underlying data is a public ArcGIS feature service — no scraping needed

### West Lothian

- **Status:** Not implemented — good candidate
- **Approach:** GOSSForms (GOSS Interactive CMS) — fully server-rendered multi-step POST form
- **Flow:**
  1. GET `https://www.westlothian.gov.uk/bin-collections` to extract `pageSessionId`, `fsid`, `fsn` UUIDs from the form
  2. POST PAGE1 with postcode field `WLBINCOLLECTION_PAGE1_ADDRESSLOOKUP` to get address dropdown
  3. POST PAGE2 with UPRN to get `ICALCONTENT` (inline ICS calendar data) or direct collection dates
- **Notes:** Each response includes a new `fsn` nonce. The `ICALCONTENT` field in PAGE2 response contains inline ICS data — parse with the same ICS parser used for Clackmannanshire.

### Renfrewshire

- **Status:** Not implemented — moderate complexity
- **Approach:** LocalGov Drupal with `localgov_waste` module; uses Drupal AJAX form flow
- **Flow:**
  1. GET page to fetch fresh `form_build_id`
  2. POST with `X-Requested-With: XMLHttpRequest` and `_wrapper_format=drupal_ajax` — returns JSON array of HTML commands (Drupal AJAX API)
  3. Parse HTML fragment from response to get address list
  4. Second POST with UPRN/address selection to get collection dates
- **Form field:** `postcode_container[postcode]`, `form_id=ren_waste_collection_postcode_form`
- **Notes:** The Drupal AJAX response is a JSON array like `[{"command": "insert", "data": "<html>..."}]` — parse the `data` value as HTML

### Aberdeenshire

- **Status:** Not implemented — complex
- **Approach:** Server-rendered .NET with `__RequestVerificationToken` (CSRF)
- **URL:** `https://online.aberdeenshire.gov.uk/apps/waste-collections/`
- **Flow:** 2-step form (search → select address → get calendar), but the address dropdown after step 1 appears to be populated by JavaScript AJAX — the POST response HTML does not contain the address list
- **Remaining work:** Identify the AJAX endpoint used by `formControls.js` (served from Azure CDN) that fetches address options after initial search
- **Notes:** Standard POST with `PageModel.searchTerms` returns HTTP 200 but empty address table; missing `addresses` and `PageTitle` fields that are likely JS-populated

### Glasgow City

- **Status:** Blocked — Cloudflare protection
- **Notes:** The website is protected by Cloudflare's bot management. All automated requests are challenged. Not implementable without a headless browser. Issue closed.

### Midlothian

- **Status:** Not implementable — JavaScript-only
- **URL:** `https://my.midlothian.gov.uk/service/Bin_Collection_Dates`
- **Notes:** Uses AchieveForms (Granicus) embedded in an iframe. The form definition is loaded entirely client-side from the AchieveForms cloud runtime using a `FS.FormDefinition` object. No server-rendered HTML or discoverable API endpoint.

### Moray

- **Status:** Not implemented — complex scraping
- **Approach:** HTML calendar page with CSS class codes for bin types (G=Green, B=Brown, P=Purple, O=Orange)
- **Notes:** No ICS endpoint found. Would require parsing the calendar grid HTML and mapping CSS classes to bin types. Skipped for now.

### Scottish Borders

- **Status:** Not yet fully investigated
- **Notes:** Appears to have moved to a Bartec portal — likely JavaScript-heavy. Not investigated in depth.

### South Lanarkshire

- **Status:** Not implementable with current model
- **Notes:** The website only provides day-of-week + frequency (e.g. "Monday Fortnightly") rather than actual collection dates. This is incompatible with the `BinCollection.next_date` model which requires a specific date.

### Stirling

- **Status:** Blocked — WAF/CDN returns 403
- **Notes:** The entire `stirling.gov.uk` domain returns HTTP 403 to all automated requests. The homepage itself is also blocked. Likely a WAF rule blocking non-browser user agents.

---

## Not Yet Investigated

- Aberdeen City
- Angus
- Argyll and Bute
- City of Edinburgh
- Comhairle nan Eilean Siar (Western Isles)
- Dumfries and Galloway
- Dundee City
- East Ayrshire
- East Renfrewshire
- Fife
- Highland
- Inverclyde
- North Lanarkshire
- Orkney Islands
- Perth and Kinross
- Shetland Islands
- South Ayrshire
- West Dunbartonshire
