"""Unit tests for coordinator parsing functions."""

import base64
import json as json_mod
from datetime import date

from custom_components.uk_bins.coordinator import (
    _extract_uk_postcode,
    _parse_clackmannanshire_search,
    _parse_east_dunbartonshire_html,
    _parse_east_renfrewshire_page2,
    _parse_east_renfrewshire_results,
    _parse_east_renfrewshire_table,
    _parse_falkirk_json,
    _parse_falkirk_search,
    _parse_ics_collections,
    _parse_north_ayrshire_attrs,
    _parse_south_ayrshire_page2,
    _parse_south_ayrshire_page3,
    _parse_west_lothian_addresses,
    _parse_west_lothian_form,
    _parse_west_lothian_page2,
    format_east_dun_address,
)

# ---------------------------------------------------------------------------
# East Dunbartonshire — address formatter
# ---------------------------------------------------------------------------


def testformat_east_dun_address_full():
    item = {"addressLine1": "1 Main Street", "town": "Bearsden", "postcode": "G61 1AA"}
    assert format_east_dun_address(item) == "1 Main Street, Bearsden, G61 1AA"


def testformat_east_dun_address_no_postcode():
    item = {"addressLine1": "2 High Road", "town": "Milngavie"}
    assert format_east_dun_address(item) == "2 High Road, Milngavie"


def testformat_east_dun_address_missing_fields():
    assert format_east_dun_address({}) == ""


# ---------------------------------------------------------------------------
# East Dunbartonshire — HTML parser
# ---------------------------------------------------------------------------

EAST_DUN_HTML = """
<table>
  <tr>
    <td class="food-caddy">Food caddy</td>
    <td><div><span>Monday, 21 April 2025</span></div></td>
  </tr>
  <tr>
    <td class="garden-bin">Green bin</td>
    <td><div><span>Wednesday, 23 April 2025</span></div></td>
  </tr>
  <tr>
    <td class="rubbish-bin">Grey bin</td>
    <td><div><span>Friday, 25 April 2025</span></div></td>
  </tr>
</table>
"""


def test_parse_east_dunbartonshire_html_returns_all_bins():
    results = _parse_east_dunbartonshire_html(EAST_DUN_HTML)
    assert len(results) == 3


def test_parse_east_dunbartonshire_html_bin_classes():
    results = _parse_east_dunbartonshire_html(EAST_DUN_HTML)
    classes = {r.bin_class for r in results}
    assert classes == {"food-caddy", "garden-bin", "rubbish-bin"}


def test_parse_east_dunbartonshire_html_dates():
    results = _parse_east_dunbartonshire_html(EAST_DUN_HTML)
    by_class = {r.bin_class: r.next_date for r in results}
    assert by_class["food-caddy"] == date(2025, 4, 21)
    assert by_class["garden-bin"] == date(2025, 4, 23)
    assert by_class["rubbish-bin"] == date(2025, 4, 25)


def test_parse_east_dunbartonshire_html_bad_date_skipped():
    html = '<td class="food-caddy">Food caddy</td><td><span>not a date</span></td>'
    results = _parse_east_dunbartonshire_html(html)
    assert results == []


def test_parse_east_dunbartonshire_html_empty():
    assert _parse_east_dunbartonshire_html("") == []


# ---------------------------------------------------------------------------
# Clackmannanshire — search result parser
# ---------------------------------------------------------------------------

CLACKS_SEARCH_HTML = """
<ul>
  <li><a href="/environment/wastecollection/id/12345/">1 High Street, Alloa</a></li>
  <li><a href="/environment/wastecollection/id/67890/">2 High Street, Alloa</a></li>
</ul>
"""


def test_parse_clackmannanshire_search_finds_properties():
    results = _parse_clackmannanshire_search(CLACKS_SEARCH_HTML)
    assert len(results) == 2


def test_parse_clackmannanshire_search_ids():
    results = _parse_clackmannanshire_search(CLACKS_SEARCH_HTML)
    assert results[0] == ("12345", "1 High Street, Alloa")
    assert results[1] == ("67890", "2 High Street, Alloa")


def test_parse_clackmannanshire_search_strips_whitespace():
    html = '<a href="/environment/wastecollection/id/99/">  Flat 1  </a>'
    results = _parse_clackmannanshire_search(html)
    assert results[0][1] == "Flat 1"


def test_parse_clackmannanshire_search_empty():
    assert _parse_clackmannanshire_search("<html>No results</html>") == []


# ---------------------------------------------------------------------------
# ICS parser (used by Clackmannanshire)
# ---------------------------------------------------------------------------


def _make_ics(events: list[str]) -> str:
    body = "\n".join(events)
    return f"BEGIN:VCALENDAR\n{body}\nEND:VCALENDAR"


def _make_event(summary: str, dtstart: str, rrule: str = "") -> str:
    lines = [
        "BEGIN:VEVENT",
        f"SUMMARY:{summary}",
        f"DTSTART;VALUE=DATE:{dtstart}",
    ]
    if rrule:
        lines.append(f"RRULE:{rrule}")
    lines.append("END:VEVENT")
    return "\n".join(lines)


def test_ics_future_event_no_rrule():
    ics = _make_ics([_make_event("Grey bin", "20260501")])
    results = _parse_ics_collections(ics, date(2026, 4, 1))
    assert len(results) == 1
    assert results[0].next_date == date(2026, 5, 1)
    assert results[0].name == "Grey bin"


def test_ics_past_event_no_rrule_excluded():
    ics = _make_ics([_make_event("Grey bin", "20250101")])
    results = _parse_ics_collections(ics, date(2026, 4, 1))
    assert results == []


def test_ics_weekly_rrule_advances_past_events():
    # starts 2026-01-05 (Monday), collected every week; today is 2026-04-20
    ics = _make_ics([_make_event("Green bin", "20260105", "FREQ=WEEKLY;INTERVAL=1")])
    results = _parse_ics_collections(ics, date(2026, 4, 20))
    assert len(results) == 1
    # result must be >= today and on a Monday
    assert results[0].next_date >= date(2026, 4, 20)
    assert results[0].next_date.weekday() == 0  # Monday


def test_ics_fortnightly_rrule():
    # starts 2026-01-05, fortnightly; today is 2026-01-12 (between occurrences)
    ics = _make_ics([_make_event("Blue bin", "20260105", "FREQ=WEEKLY;INTERVAL=2")])
    results = _parse_ics_collections(ics, date(2026, 1, 12))
    assert len(results) == 1
    assert results[0].next_date == date(2026, 1, 19)


def test_ics_rrule_until_expired():
    # UNTIL in the past → no future occurrences
    ics = _make_ics(
        [_make_event("Food caddy", "20250101", "FREQ=WEEKLY;INTERVAL=1;UNTIL=20250401")]
    )
    results = _parse_ics_collections(ics, date(2026, 4, 20))
    assert results == []


def test_ics_rrule_until_still_valid():
    # starts 2026-04-13, weekly, UNTIL 2026-12-31; today is 2026-04-20
    ics = _make_ics([_make_event("Grey bin", "20260413", "FREQ=WEEKLY;INTERVAL=1;UNTIL=20261231")])
    results = _parse_ics_collections(ics, date(2026, 4, 20))
    assert len(results) == 1
    assert results[0].next_date == date(2026, 4, 20)


def test_ics_multiple_events():
    ics = _make_ics(
        [
            _make_event("Grey bin", "20260420"),
            _make_event("Blue bin", "20260421"),
        ]
    )
    results = _parse_ics_collections(ics, date(2026, 4, 19))
    names = {r.name for r in results}
    assert names == {"Grey bin", "Blue bin"}


def test_ics_event_today_included():
    ics = _make_ics([_make_event("Grey bin", "20260420")])
    results = _parse_ics_collections(ics, date(2026, 4, 20))
    assert len(results) == 1
    assert results[0].next_date == date(2026, 4, 20)


# ---------------------------------------------------------------------------
# Falkirk — search result parser
# ---------------------------------------------------------------------------

FALKIRK_SEARCH_HTML = """
<ul>
  <li><a href="/collections/111222">1 Princes Street, Falkirk, FK1 1AA</a></li>
  <li><a href="/collections/333444">2 Princes Street, Falkirk, FK1 1AB</a></li>
</ul>
"""


def test_parse_falkirk_search_finds_properties():
    results = _parse_falkirk_search(FALKIRK_SEARCH_HTML)
    assert len(results) == 2


def test_parse_falkirk_search_ids_and_names():
    results = _parse_falkirk_search(FALKIRK_SEARCH_HTML)
    assert results[0] == ("111222", "1 Princes Street, Falkirk, FK1 1AA")
    assert results[1] == ("333444", "2 Princes Street, Falkirk, FK1 1AB")


def test_parse_falkirk_search_empty():
    assert _parse_falkirk_search("<p>No results found</p>") == []


# ---------------------------------------------------------------------------
# Falkirk — JSON collection parser
# ---------------------------------------------------------------------------

FALKIRK_JSON = {
    "collections": [
        {"type": "Blue bin", "dates": ["2026-04-15", "2026-04-29", "2026-05-13"]},
        {"type": "Green bin", "dates": ["2026-04-08", "2026-04-22"]},
        {"type": "Food caddy", "dates": ["2026-04-10"]},
    ]
}


def test_parse_falkirk_json_picks_first_future_date():
    results = _parse_falkirk_json(FALKIRK_JSON, date(2026, 4, 20))
    by_type = {r.bin_class: r.next_date for r in results}
    assert by_type["Blue bin"] == date(2026, 4, 29)
    assert by_type["Green bin"] == date(2026, 4, 22)


def test_parse_falkirk_json_excludes_all_past():
    # Food caddy only has 2026-04-10 which is before today
    results = _parse_falkirk_json(FALKIRK_JSON, date(2026, 4, 20))
    types = {r.bin_class for r in results}
    assert "Food caddy" not in types


def test_parse_falkirk_json_includes_today():
    results = _parse_falkirk_json(FALKIRK_JSON, date(2026, 4, 22))
    by_type = {r.bin_class: r.next_date for r in results}
    assert by_type["Green bin"] == date(2026, 4, 22)


def test_parse_falkirk_json_empty_collections():
    assert _parse_falkirk_json({"collections": []}, date(2026, 4, 20)) == []


def test_parse_falkirk_json_missing_key():
    assert _parse_falkirk_json({}, date(2026, 4, 20)) == []


def test_parse_falkirk_json_bin_class_matches_type():
    results = _parse_falkirk_json(FALKIRK_JSON, date(2026, 4, 20))
    for r in results:
        assert r.bin_class == r.name


# ---------------------------------------------------------------------------
# North Ayrshire — ArcGIS attribute parser
# ---------------------------------------------------------------------------


def test_parse_north_ayrshire_attrs_all_bins():
    attrs = {
        "BLUE_DATE_TEXT": "21/04/2026",
        "GREY_DATE_TEXT": "28/04/2026",
        "PURPLE_DATE_TEXT": "05/05/2026",
        "BROWN_DATE_TEXT": "12/05/2026",
    }
    results = _parse_north_ayrshire_attrs(attrs)
    assert len(results) == 4


def test_parse_north_ayrshire_attrs_dates():
    attrs = {
        "BLUE_DATE_TEXT": "21/04/2026",
        "GREY_DATE_TEXT": "28/04/2026",
    }
    results = _parse_north_ayrshire_attrs(attrs)
    by_class = {r.bin_class: r.next_date for r in results}
    assert by_class["blue_bin"] == date(2026, 4, 21)
    assert by_class["grey_bin"] == date(2026, 4, 28)


def test_parse_north_ayrshire_attrs_missing_field_skipped():
    results = _parse_north_ayrshire_attrs({"BLUE_DATE_TEXT": "21/04/2026"})
    assert len(results) == 1
    assert results[0].bin_class == "blue_bin"


def test_parse_north_ayrshire_attrs_bad_date_skipped():
    results = _parse_north_ayrshire_attrs({"BLUE_DATE_TEXT": "not-a-date"})
    assert results == []


def test_parse_north_ayrshire_attrs_empty():
    assert _parse_north_ayrshire_attrs({}) == []


# ---------------------------------------------------------------------------
# West Lothian — address list parser
# ---------------------------------------------------------------------------


def test_parse_west_lothian_addresses_formats_correctly():
    results = _parse_west_lothian_addresses(
        [
            {
                "udprn": "12345",
                "line1": "1 Main Street",
                "town": "Livingston",
                "postcode": "EH54 5AA",
            },
        ]
    )
    assert len(results) == 1
    assert results[0] == ("12345", "1 Main Street, Livingston, EH54 5AA")


def test_parse_west_lothian_addresses_skips_empty_udprn():
    results = _parse_west_lothian_addresses(
        [
            {
                "udprn": "",
                "line1": "Flat 1",
                "town": "Bathgate",
                "postcode": "EH48 1AA",
            },
        ]
    )
    assert results == []


def test_parse_west_lothian_addresses_empty_list():
    assert _parse_west_lothian_addresses([]) == []


def test_parse_west_lothian_addresses_multiple():
    results = _parse_west_lothian_addresses(
        [
            {"udprn": "1", "line1": "1 Road", "town": "Town", "postcode": "EH1 1AA"},
            {"udprn": "2", "line1": "2 Road", "town": "Town", "postcode": "EH1 1AB"},
        ]
    )
    assert len(results) == 2
    assert results[0][0] == "1"
    assert results[1][0] == "2"


# ---------------------------------------------------------------------------
# West Lothian — form parser
# ---------------------------------------------------------------------------

WEST_LOTHIAN_FORM_HTML = """
<html><body>
<form method="post"
      action="/apiserver/formsservice/http/processsubmission?pageSessionId=aaa&amp;fsid=bbb&amp;fsn=ccc">
<input type="hidden" name="WLBINCOLLECTION_PAGENAME" value="PAGE1" />
<input type="hidden" name="WLBINCOLLECTION_PAGESESSIONID" value="aaa" />
<input type="hidden" name="WLBINCOLLECTION_NONCE" value="ccc" />
<input type="hidden" name="WLBINCOLLECTION_PAGE1_UPRN" value="" />
</form>
</body></html>
"""


def test_parse_west_lothian_form_action_url():
    _, action_url = _parse_west_lothian_form(WEST_LOTHIAN_FORM_HTML)
    assert "processsubmission" in action_url
    assert "pageSessionId=aaa" in action_url
    assert "fsid=bbb" in action_url
    assert "fsn=ccc" in action_url
    assert "&amp;" not in action_url  # HTML entities must be unescaped


def test_parse_west_lothian_form_extracts_fields():
    form_data, _ = _parse_west_lothian_form(WEST_LOTHIAN_FORM_HTML)
    assert form_data["WLBINCOLLECTION_PAGENAME"] == "PAGE1"
    assert form_data["WLBINCOLLECTION_PAGESESSIONID"] == "aaa"
    assert form_data["WLBINCOLLECTION_NONCE"] == "ccc"


def test_parse_west_lothian_form_empty_html():
    form_data, action_url = _parse_west_lothian_form("<html></html>")
    assert form_data == {}
    assert action_url == "https://www.westlothian.gov.uk/bin-collections"


# ---------------------------------------------------------------------------
# West Lothian — PAGE2 parser
# ---------------------------------------------------------------------------


def _make_wl_page2(collections: list[dict]) -> str:
    payload = {"PAGE2_1": {"COLLECTIONS": collections}}
    encoded = base64.b64encode(json_mod.dumps(payload).encode()).decode()
    return f'<script>var WLBINCOLLECTIONFormData = "{encoded}";</script>'


def test_parse_west_lothian_page2_basic():
    html = _make_wl_page2(
        [
            {
                "binType": "BLUE",
                "binName": "Blue bin",
                "nextCollectionISO": "2026-04-21",
            },
            {
                "binType": "GREY",
                "binName": "Grey bin",
                "nextCollectionISO": "2026-04-28",
            },
        ]
    )
    results = _parse_west_lothian_page2(html)
    assert len(results) == 2
    by_type = {r.bin_class: r.next_date for r in results}
    assert by_type["BLUE"] == date(2026, 4, 21)
    assert by_type["GREY"] == date(2026, 4, 28)


def test_parse_west_lothian_page2_uses_bin_name():
    html = _make_wl_page2(
        [
            {
                "binType": "BLUE",
                "binName": "Blue Recycling Bin",
                "nextCollectionISO": "2026-04-21",
            },
        ]
    )
    results = _parse_west_lothian_page2(html)
    assert results[0].name == "Blue Recycling Bin"


def test_parse_west_lothian_page2_skips_bad_date():
    html = _make_wl_page2(
        [
            {
                "binType": "BLUE",
                "binName": "Blue bin",
                "nextCollectionISO": "not-a-date",
            },
        ]
    )
    assert _parse_west_lothian_page2(html) == []


def test_parse_west_lothian_page2_no_data_var():
    assert _parse_west_lothian_page2("<html>no data here</html>") == []


def test_parse_west_lothian_page2_empty_collections():
    html = _make_wl_page2([])
    assert _parse_west_lothian_page2(html) == []


# ---------------------------------------------------------------------------
# East Renfrewshire — PAGE2 address dropdown parser
# ---------------------------------------------------------------------------

EAST_REN_PAGE2_HTML = """
<html><body>
<select name="BINDAYSV2_PAGE2_UPRN">
  <option value="">-- Select address --</option>
  <option value="000012345678">1 High Street, Barrhead, G78 1AA</option>
  <option value="000087654321">2 High Street, Barrhead, G78 1AB</option>
</select>
</body></html>
"""


def test_parse_east_renfrewshire_page2_finds_options():
    results = _parse_east_renfrewshire_page2(EAST_REN_PAGE2_HTML)
    assert len(results) == 2


def test_parse_east_renfrewshire_page2_values_and_labels():
    results = _parse_east_renfrewshire_page2(EAST_REN_PAGE2_HTML)
    assert results[0] == ("000012345678", "1 High Street, Barrhead, G78 1AA")
    assert results[1] == ("000087654321", "2 High Street, Barrhead, G78 1AB")


def test_parse_east_renfrewshire_page2_skips_blank_value():
    results = _parse_east_renfrewshire_page2(EAST_REN_PAGE2_HTML)
    values = [r[0] for r in results]
    assert "" not in values


def test_parse_east_renfrewshire_page2_no_select():
    assert _parse_east_renfrewshire_page2("<html>no form here</html>") == []


# ---------------------------------------------------------------------------
# East Renfrewshire — collection table parser
# ---------------------------------------------------------------------------

EAST_REN_TABLE_HTML = """
<table>
  <tr>
    <td>21/04/2026</td>
    <td>Tuesday</td>
    <td><img alt="Blue bin icon" /></td>
  </tr>
  <tr>
    <td>28/04/2026</td>
    <td>Tuesday</td>
    <td><img alt="Green bin icon" /><img alt="Grey bin icon" /></td>
  </tr>
</table>
"""


def test_parse_east_renfrewshire_table_single_bin():
    results = _parse_east_renfrewshire_table(EAST_REN_TABLE_HTML)
    blue = [r for r in results if r.bin_class == "Blue bin"]
    assert len(blue) == 1
    assert blue[0].next_date == date(2026, 4, 21)


def test_parse_east_renfrewshire_table_multiple_bins_same_row():
    results = _parse_east_renfrewshire_table(EAST_REN_TABLE_HTML)
    by_class = {r.bin_class: r.next_date for r in results}
    assert by_class["Green bin"] == date(2026, 4, 28)
    assert by_class["Grey bin"] == date(2026, 4, 28)


def test_parse_east_renfrewshire_table_total_count():
    results = _parse_east_renfrewshire_table(EAST_REN_TABLE_HTML)
    assert len(results) == 3


def test_parse_east_renfrewshire_table_strips_icon_suffix():
    results = _parse_east_renfrewshire_table(EAST_REN_TABLE_HTML)
    classes = {r.bin_class for r in results}
    assert "Blue bin" in classes
    assert "Blue bin icon" not in classes


def test_parse_east_renfrewshire_table_bad_date_skipped():
    html = '<table><tr><td>not-a-date</td><td><img alt="Blue bin icon"/></td></tr></table>'
    assert _parse_east_renfrewshire_table(html) == []


def test_parse_east_renfrewshire_table_empty():
    assert _parse_east_renfrewshire_table("") == []


# ---------------------------------------------------------------------------
# East Renfrewshire — results page parser
# ---------------------------------------------------------------------------


def _make_er_results(table_html: str) -> str:
    payload = {"RESULTS_1": {"NEXTCOLLECTIONLISTV4": table_html}}
    encoded = base64.b64encode(json_mod.dumps(payload).encode()).decode()
    return f'<script>var BINDAYSV2FormData = "{encoded}";</script>'


def test_parse_east_renfrewshire_results_basic():
    table = '<table><tr><td>21/04/2026</td><td><img alt="Blue bin icon"/></td></tr></table>'
    results = _parse_east_renfrewshire_results(_make_er_results(table))
    assert len(results) == 1
    assert results[0].bin_class == "Blue bin"
    assert results[0].next_date == date(2026, 4, 21)


def test_parse_east_renfrewshire_results_no_data_var():
    assert _parse_east_renfrewshire_results("<html>nothing here</html>") == []


def test_parse_east_renfrewshire_results_empty_table():
    assert _parse_east_renfrewshire_results(_make_er_results("")) == []


# ---------------------------------------------------------------------------
# South Ayrshire — PAGE2 address dropdown parser
# ---------------------------------------------------------------------------

SOUTH_AYR_PAGE2_HTML = """
<html><body>
<select name="BINDAYS_PAGE2_ADDRESSDROPDOWN">
  <option value="">-- Select address --</option>
  <option value="141041931">2 Thornyflat Place, Ayr, KA8 0NE</option>
  <option value="141041932">4 Thornyflat Place, Ayr, KA8 0NE</option>
</select>
</body></html>
"""


def test_parse_south_ayrshire_page2_finds_options():
    results = _parse_south_ayrshire_page2(SOUTH_AYR_PAGE2_HTML)
    assert len(results) == 2


def test_parse_south_ayrshire_page2_values_and_labels():
    results = _parse_south_ayrshire_page2(SOUTH_AYR_PAGE2_HTML)
    assert results[0] == ("141041931", "2 Thornyflat Place, Ayr, KA8 0NE")
    assert results[1] == ("141041932", "4 Thornyflat Place, Ayr, KA8 0NE")


def test_parse_south_ayrshire_page2_skips_blank_value():
    results = _parse_south_ayrshire_page2(SOUTH_AYR_PAGE2_HTML)
    assert all(v for v, _ in results)


def test_parse_south_ayrshire_page2_no_select():
    assert _parse_south_ayrshire_page2("<html>no form</html>") == []


# ---------------------------------------------------------------------------
# South Ayrshire — PAGE3 data parser
# ---------------------------------------------------------------------------


def _make_sa_page3(field15: dict) -> str:
    payload = {"PAGE3_1": {"FIELD15": field15}}
    encoded = base64.b64encode(json_mod.dumps(payload).encode()).decode()
    return f'<script>var BINDAYSFormData = "{encoded}";</script>'


SA_FIELD15 = {
    "success": True,
    "nextBin": [
        {
            "bin": "Food Waste Caddy",
            "binDate": "2026-04-22T22:30:00.000Z",
            "prettyDate": "Wednesday 22/04/2026",
        },
    ],
    "tableRow1": [
        {
            "bin": "Food Waste Caddy",
            "binDate": "2026-04-22T22:30:00.000Z",
            "prettyDate": "Wednesday 22/04/2026",
        },
        {
            "bin": "Blue/Blue Lidded Bin",
            "binDate": "2026-04-29T22:30:00.000Z",
            "prettyDate": "Wednesday 29/04/2026",
        },
    ],
    "tableRow2": [
        {
            "bin": "Brown Bin",
            "binDate": "2026-05-06T22:30:00.000Z",
            "prettyDate": "Wednesday 06/05/2026",
        },
    ],
}


def test_parse_south_ayrshire_page3_returns_bins():
    results = _parse_south_ayrshire_page3(_make_sa_page3(SA_FIELD15), today=date(2026, 4, 20))
    by_class = {r.bin_class: r.next_date for r in results}
    assert by_class["Food Waste Caddy"] == date(2026, 4, 22)
    assert by_class["Blue/Blue Lidded Bin"] == date(2026, 4, 29)
    assert by_class["Brown Bin"] == date(2026, 5, 6)


def test_parse_south_ayrshire_page3_deduplicates_keeping_earliest():
    field15 = {
        "success": True,
        "nextBin": [{"bin": "Food Waste Caddy", "binDate": "2026-04-22T00:00:00.000Z"}],
        "tableRow1": [{"bin": "Food Waste Caddy", "binDate": "2026-04-29T00:00:00.000Z"}],
    }
    results = _parse_south_ayrshire_page3(_make_sa_page3(field15), today=date(2026, 4, 20))
    food = [r for r in results if r.bin_class == "Food Waste Caddy"]
    assert len(food) == 1
    assert food[0].next_date == date(2026, 4, 22)


def test_parse_south_ayrshire_page3_filters_past_dates():
    field15 = {
        "success": True,
        "tableRow1": [{"bin": "Food Waste Caddy", "binDate": "2026-04-10T00:00:00.000Z"}],
    }
    results = _parse_south_ayrshire_page3(_make_sa_page3(field15), today=date(2026, 4, 20))
    assert results == []


def test_parse_south_ayrshire_page3_success_false():
    field15 = {"success": False}
    assert _parse_south_ayrshire_page3(_make_sa_page3(field15), today=date(2026, 4, 20)) == []


def test_parse_south_ayrshire_page3_no_data_var():
    assert _parse_south_ayrshire_page3("<html>nothing</html>", today=date(2026, 4, 20)) == []


def test_parse_south_ayrshire_page3_empty_rows():
    field15 = {"success": True, "nextBin": [], "tableRow1": []}
    assert _parse_south_ayrshire_page3(_make_sa_page3(field15), today=date(2026, 4, 20)) == []


# ---------------------------------------------------------------------------
# _extract_uk_postcode helper
# ---------------------------------------------------------------------------


def test_extract_uk_postcode_standard():
    assert _extract_uk_postcode("1 High Street, Barrhead, G78 1AA") == "G78 1AA"


def test_extract_uk_postcode_at_end():
    assert _extract_uk_postcode("2 Thornyflat Place, Ayr, KA8 0NE") == "KA8 0NE"


def test_extract_uk_postcode_missing():
    assert _extract_uk_postcode("somewhere without postcode") is None


def test_extract_uk_postcode_edinburgh():
    assert _extract_uk_postcode("10 Royal Mile, Edinburgh, EH1 2AB") == "EH1 2AB"
