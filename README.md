# Scottish Bins

A [Home Assistant](https://www.home-assistant.io/) custom integration for Scottish council bin collection schedules.

## Supported Councils

| Council | Status |
|---------|--------|
| Clackmannanshire | Supported |
| East Dunbartonshire | Supported |
| East Renfrewshire | Supported |
| Falkirk | Supported |
| North Ayrshire | Supported |
| South Ayrshire | Supported |
| West Lothian | Supported |
| Aberdeen City | [Vote / comment](https://github.com/d0ugal/scottish-bins-homeassistant/issues/3) |
| Aberdeenshire | [Vote / comment](https://github.com/d0ugal/scottish-bins-homeassistant/issues/11) |
| Angus | [Vote / comment](https://github.com/d0ugal/scottish-bins-homeassistant/issues/9) |
| Argyll and Bute | [Vote / comment](https://github.com/d0ugal/scottish-bins-homeassistant/issues/10) |
| City of Edinburgh | [Vote / comment](https://github.com/d0ugal/scottish-bins-homeassistant/issues/6) |
| Comhairle nan Eilean Siar (Western Isles) | [Vote / comment](https://github.com/d0ugal/scottish-bins-homeassistant/issues/15) |
| Dumfries and Galloway | [Vote / comment](https://github.com/d0ugal/scottish-bins-homeassistant/issues/12) |
| Dundee City | [Vote / comment](https://github.com/d0ugal/scottish-bins-homeassistant/issues/14) |
| East Ayrshire | [Vote / comment](https://github.com/d0ugal/scottish-bins-homeassistant/issues/13) |
| East Lothian | [Vote / comment](https://github.com/d0ugal/scottish-bins-homeassistant/issues/19) |
| Fife | [Vote / comment](https://github.com/d0ugal/scottish-bins-homeassistant/issues/4) |
| Glasgow City | [Vote / comment](https://github.com/d0ugal/scottish-bins-homeassistant/issues/2) |
| Highland | [Vote / comment](https://github.com/d0ugal/scottish-bins-homeassistant/issues/7) |
| Inverclyde | [Vote / comment](https://github.com/d0ugal/scottish-bins-homeassistant/issues/16) |
| Midlothian | [Vote / comment](https://github.com/d0ugal/scottish-bins-homeassistant/issues/23) |
| Moray | [Vote / comment](https://github.com/d0ugal/scottish-bins-homeassistant/issues/22) |
| North Ayrshire | [Vote / comment](https://github.com/d0ugal/scottish-bins-homeassistant/issues/20) |
| Orkney Islands | [Vote / comment](https://github.com/d0ugal/scottish-bins-homeassistant/issues/21) |
| Perth and Kinross | [Vote / comment](https://github.com/d0ugal/scottish-bins-homeassistant/issues/24) |
| Renfrewshire | [Vote / comment](https://github.com/d0ugal/scottish-bins-homeassistant/issues/27) |
| Scottish Borders | [Vote / comment](https://github.com/d0ugal/scottish-bins-homeassistant/issues/25) |
| Shetland Islands | [Vote / comment](https://github.com/d0ugal/scottish-bins-homeassistant/issues/26) |
| South Lanarkshire | [Vote / comment](https://github.com/d0ugal/scottish-bins-homeassistant/issues/5) |
| Stirling | [Vote / comment](https://github.com/d0ugal/scottish-bins-homeassistant/issues/31) |
| West Dunbartonshire | [Vote / comment](https://github.com/d0ugal/scottish-bins-homeassistant/issues/30) |
| West Lothian | [Vote / comment](https://github.com/d0ugal/scottish-bins-homeassistant/issues/29) |
| North Lanarkshire | Not yet investigated |
| Perth and Kinross | [Vote / comment](https://github.com/d0ugal/scottish-bins-homeassistant/issues/24) |

Upvoting an issue (👍 on the first comment) helps us prioritise which councils to add next.

## Installation

### HACS (recommended)

1. Add this repository to HACS as a custom repository
2. Search for "Scottish Bins" and install
3. Restart Home Assistant

### Manual

Copy `custom_components/scottish_bins` into your Home Assistant `custom_components` directory and restart.

## Setup

1. Go to **Settings > Devices & Services > Add Integration**
2. Search for "Scottish Bins"
3. Select your council
4. Search for your address by street, house name, or postcode
5. Select your property from the results

## Entities

Once configured, the integration creates:

- **Calendar** — shows upcoming bin collection events; works with the Home Assistant calendar card
- **Sensors** — one per bin type (e.g. Food caddy, Green bin, Grey bin), showing the date of the next collection with a `days_until` attribute
