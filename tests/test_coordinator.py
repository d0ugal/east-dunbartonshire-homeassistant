"""Unit tests for coordinator parsing functions."""

from datetime import date

from custom_components.scottish_bins.coordinator import (
    BinCollection,
    _parse_clackmannanshire_search,
    _parse_east_dunbartonshire_html,
    _parse_falkirk_json,
    _parse_falkirk_search,
    _parse_ics_collections,
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
    ics = _make_ics([_make_event("Food caddy", "20250101", "FREQ=WEEKLY;INTERVAL=1;UNTIL=20250401")])
    results = _parse_ics_collections(ics, date(2026, 4, 20))
    assert results == []


def test_ics_rrule_until_still_valid():
    # starts 2026-04-13, weekly, UNTIL 2026-12-31; today is 2026-04-20
    ics = _make_ics([_make_event("Grey bin", "20260413", "FREQ=WEEKLY;INTERVAL=1;UNTIL=20261231")])
    results = _parse_ics_collections(ics, date(2026, 4, 20))
    assert len(results) == 1
    assert results[0].next_date == date(2026, 4, 20)


def test_ics_multiple_events():
    ics = _make_ics([
        _make_event("Grey bin", "20260420"),
        _make_event("Blue bin", "20260421"),
    ])
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
