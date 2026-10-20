"""Unit tests for coordinator parsing functions."""

from datetime import date

from custom_components.east_dunbartonshire.coordinator import _parse_html, format_address

# ---------------------------------------------------------------------------
# East Dunbartonshire — address formatter
# ---------------------------------------------------------------------------


def test_format_address_full():
    item = {"addressLine1": "1 Main Street", "town": "Bearsden", "postcode": "G61 1AA"}
    assert format_address(item) == "1 Main Street, Bearsden, G61 1AA"


def test_format_address_no_postcode():
    item = {"addressLine1": "2 High Road", "town": "Milngavie"}
    assert format_address(item) == "2 High Road, Milngavie"


def test_format_address_missing_fields():
    assert format_address({}) == ""


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


def test_parse_html_returns_all_bins():
    results = _parse_html(EAST_DUN_HTML)
    assert len(results) == 3


def test_parse_html_bin_classes():
    results = _parse_html(EAST_DUN_HTML)
    classes = {r.bin_class for r in results}
    assert classes == {"food-caddy", "garden-bin", "rubbish-bin"}


def test_parse_html_dates():
    results = _parse_html(EAST_DUN_HTML)
    by_class = {r.bin_class: r.next_date for r in results}
    assert by_class["food-caddy"] == date(2025, 4, 21)
    assert by_class["garden-bin"] == date(2025, 4, 23)
    assert by_class["rubbish-bin"] == date(2025, 4, 25)


def test_parse_html_bad_date_skipped():
    html = '<td class="food-caddy">Food caddy</td><td><span>not a date</span></td>'
    results = _parse_html(html)
    assert results == []


def test_parse_html_empty():
    assert _parse_html("") == []
