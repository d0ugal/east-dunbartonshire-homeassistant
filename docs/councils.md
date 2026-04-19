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

- **Status:** Not implemented — excellent candidate (clean ArcGIS API)
- **Address search:** `GET https://www.maps.north-ayrshire.gov.uk/arcgis/rest/services/AGOL/CAG_VIEW/MapServer/0/query?where=UPPER(ADDRESS) LIKE UPPER('%<query>%')&outFields=ADDRESS,UPRN&orderByFields=ADDRESS ASC&returnGeometry=false&f=json`
  - Returns array of features with `attributes.ADDRESS` and `attributes.UPRN` (12-digit zero-padded, e.g. `000126025453`)
- **Collection data:** `GET https://www.maps.north-ayrshire.gov.uk/arcgis/rest/services/AGOL/YourLocationLive/MapServer/8/query?where=UPRN='<uprn_stripped>'&outFields=*&f=json`
  - **Important:** strip leading zeros from UPRN before querying this endpoint (e.g. `000126025453` → `126025453`)
  - Response fields: `BLUE_DATE_TEXT`, `GREY_DATE_TEXT`, `PURPLE_DATE_TEXT`, `BROWN_DATE_TEXT` (dates as `dd/mm/yyyy`)
- **Notes:** The main website is a React SPA but both APIs are public ArcGIS feature services — no scraping or auth needed

### West Lothian

- **Status:** Not implemented — good candidate (GOSSForms, complex but fully server-rendered)
- **Approach:** GOSSForms (GOSS Interactive CMS); 5-network-request flow using `aiohttp.ClientSession` with a cookie jar
- **Flow:**
  1. `GET https://www.westlothian.gov.uk/bin-collections` → extract `pageSessionId`, `fsid`, `fsn` UUIDs from form hidden fields
  2. `POST` PAGE1 form action (triggers cookie challenge) → 303 to `/apiserver/formsservice/http/verifycookie?...`
  3. `GET` verifycookie URL → sets `goss-formsservice-clientid` cookie → 303 back to `/bin-collections?...&fsn=<NEW>`
  4. Address lookup via JSONP: `GET /apiserver/postcode?jsonrpc={"id":1,"method":"postcodeSearch","params":{"provider":"EndPoint","postcode":"<pc>"}}&callback=cb` → strip `cb(...)` wrapper → JSON array with `udprn`, `line1`–`line5`, `town`, `postcode`
  5. `POST` PAGE1 again with new `fsn`, `WLBINCOLLECTION_PAGE1_UPRN=<udprn>`, `WLBINCOLLECTION_PAGE1_ADDRESSSTRING=<address>`, `WLBINCOLLECTION_FORMACTION_NEXT=WLBINCOLLECTION_PAGE1_NAVBUTTONS` → 303 to `/bin-collections?...&fsn=<NEW>` → follow to get PAGE2 HTML
- **PAGE2 data:** Base64-encoded JS variable `var WLBINCOLLECTIONFormData = "<base64>"` → decode → JSON → `PAGE2_1.COLLECTIONS` array with `binType`, `binName`, `nextCollectionISO` (ISO date string)
- **Bin types:** `BLUE`, `GREY`, `BROWN`, `GREEN`
- **Key implementation notes:**
  - Must use a persistent cookie jar; every POST without the `goss-formsservice-clientid` cookie bounces to verifycookie
  - `fsn` nonce changes on every response — always read from the latest redirect URL
  - `ICALCONTENT` field is empty — calendar is generated client-side in JS; use `nextCollectionISO` instead
  - Use `allow_redirects=False` on POSTs, capture `Location` header manually to get the new `fsn`

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
