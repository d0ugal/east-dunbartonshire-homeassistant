# East Dunbartonshire

A [Home Assistant](https://www.home-assistant.io/) custom integration for East Dunbartonshire Council services.

## Features

- **Bin collections** — sensors and calendar for upcoming bin collection dates, looked up by address
- **Planning applications** — nearby planning applications shown as map pins, filtered to applications modified in the last 90 days

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
- **Geo location entities** — one per nearby planning application (within your configured search radius), shown as map pins; each entity includes `address`, `description`, `date_modified`, and `url` attributes

## Example automations

These examples use the `east_dunbartonshire_planning` source to identify planning application geo location entities. Replace `notify.mobile_app_your_phone` with your own notification service.

### Alert when a new application appears

Triggers whenever a new planning application geo location entity is created (i.e. a fresh application enters your search radius).

```yaml
automation:
  - alias: "New nearby planning application"
    trigger:
      - platform: event
        event_type: state_changed
    condition:
      - condition: template
        value_template: >
          {{ trigger.event.data.entity_id.startswith('geo_location.')
             and trigger.event.data.new_state is not none
             and trigger.event.data.new_state.attributes.get('source') == 'east_dunbartonshire_planning'
             and trigger.event.data.old_state is none }}
    action:
      - service: notify.mobile_app_your_phone
        data:
          title: "New planning application nearby"
          message: >
            {{ trigger.event.data.new_state.name }}
            {{ trigger.event.data.new_state.attributes.address }}
            {{ trigger.event.data.new_state.attributes.description }}
          data:
            url: "{{ trigger.event.data.new_state.attributes.url }}"
```

### Weekly digest

Sends a summary every Monday morning listing all current nearby applications.

```yaml
automation:
  - alias: "Weekly planning applications digest"
    trigger:
      - platform: time
        at: "09:00:00"
    condition:
      - condition: time
        weekday:
          - mon
      - condition: template
        value_template: >
          {{ states.geo_location
             | selectattr('attributes.source', 'eq', 'east_dunbartonshire_planning')
             | list | count > 0 }}
    action:
      - service: notify.mobile_app_your_phone
        data:
          title: "Nearby planning applications"
          message: >
            {% set apps = states.geo_location
               | selectattr('attributes.source', 'eq', 'east_dunbartonshire_planning')
               | sort(attribute='attributes.date_modified', reverse=True) | list %}
            {{ apps | count }} application(s) in the last 90 days:
            {% for app in apps %}
            - {{ app.name }}: {{ app.attributes.address }} ({{ app.attributes.date_modified }})
            {% endfor %}
```

### Alert for specific application types

Notifies only when the application description matches keywords you care about (e.g. extensions, new builds).

```yaml
automation:
  - alias: "Planning application keyword alert"
    trigger:
      - platform: event
        event_type: state_changed
    condition:
      - condition: template
        value_template: >
          {% set desc = trigger.event.data.new_state.attributes.get('description', '') | lower %}
          {{ trigger.event.data.entity_id.startswith('geo_location.')
             and trigger.event.data.new_state is not none
             and trigger.event.data.new_state.attributes.get('source') == 'east_dunbartonshire_planning'
             and trigger.event.data.old_state is none
             and desc is search('dwellinghouse|extension|erection|conversion') }}
    action:
      - service: notify.mobile_app_your_phone
        data:
          title: "Planning application: residential works nearby"
          message: >
            {{ trigger.event.data.new_state.name }}
            {{ trigger.event.data.new_state.attributes.address }}
            {{ trigger.event.data.new_state.attributes.description }}
          data:
            url: "{{ trigger.event.data.new_state.attributes.url }}"
```

### Persistent notification in the HA dashboard

Creates a dismissible notification in the Home Assistant UI for each new application.

```yaml
automation:
  - alias: "Planning application persistent notification"
    trigger:
      - platform: event
        event_type: state_changed
    condition:
      - condition: template
        value_template: >
          {{ trigger.event.data.entity_id.startswith('geo_location.')
             and trigger.event.data.new_state is not none
             and trigger.event.data.new_state.attributes.get('source') == 'east_dunbartonshire_planning'
             and trigger.event.data.old_state is none }}
    action:
      - service: persistent_notification.create
        data:
          title: "Planning application: {{ trigger.event.data.new_state.name }}"
          message: >
            **{{ trigger.event.data.new_state.attributes.address }}**

            {{ trigger.event.data.new_state.attributes.description }}

            [View application]({{ trigger.event.data.new_state.attributes.url }})
          notification_id: "planning_{{ trigger.event.data.new_state.name }}"
```
