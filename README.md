# East Dunbartonshire

A [Home Assistant](https://www.home-assistant.io/) custom integration for East Dunbartonshire Council services.

## Features

- **Bin collections** — sensors and calendar for upcoming bin collection dates, looked up by address

More features planned: school holidays, planning applications, and more.

## Installation

### HACS (recommended)

1. Add this repository to HACS as a custom repository
2. Search for "East Dunbartonshire" and install
3. Restart Home Assistant

### Manual

Copy `custom_components/east_dunbartonshire` into your Home Assistant `custom_components` directory and restart.

## Setup

1. Go to **Settings > Devices & Services > Add Integration**
2. Search for "East Dunbartonshire"
3. Search for your address by street, house name or postcode
4. Select your property from the results

## Entities

Once configured, the integration creates:

- **Calendar** — shows upcoming bin collection events; works with the Home Assistant calendar card
- **Sensors** — one per bin type (Food caddy, Green bin, Grey bin), showing the date of the next collection with a `days_until` attribute
