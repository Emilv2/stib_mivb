# Stib-Mivb sensor
This code is a custom component to integrate the Stib-Mivb (the Brussels public transport) info in Home Assistant.
This component adds sensors with the next passages in minutes in real-time for a line at a given stop.

## Install

Copy these files to custom_components/stib_mivb/

Then configure the sensors by setting up the stib platform in `configuration.yaml`.

## Register

Register on opendat.stib-mivb.be to get your api_key. You need to register your key for the NetworkDescription and OperationMonitoring api.

## Options

| Name | Type | Requirement | Description
| ---- | ---- | ------- | -----------
| platform | string | **Required** | `stib`
| api_key | string | **Required** | The access token generated at opendata.stib-mivb.be.
| lang | string | **Required** | The language of the stop names 'fr' or 'nl'
| message_lang | string | **Optional** | The language of the information messages. 'nl', 'fr' or 'en'. If not given the same as lang.
| stops | object | **Required** | List of stops and lines to display next passages of.

**Example:**

```yaml
sensor:
  - platform: stib_mivb
    api_key: '< STIB access token from opendata.stib-mivb.be >'
    lang: 'nl'   
    message_lang: 'en'   
    stops:
      - stop_id: 8301
        line_numbers: 
          - 6
          - 32
      - stop_id: 5151
        line_numbers:
          - 82
          - 97
          - 32
```

## Info
### How to get the stop ids?

Go to http://www.stib-mivb.be/horaires-dienstregeling2.html, select the line, the destination and then the stop name.
The stop id can be found at the end of the url after `_stop=`.

For example, for line 1 with direction 'Gare de l'Ouest' at 'Gare Centrale', the url is: `http://www.stib-mivb.be/horaires-dienstregeling2.html?l=fr&_line=1&_directioncode=V&_stop=8021`.
The stop id is then 8021.

Get the id for each stop you need and add them to your configuration.

### How are the sensors represented?

For each line that passes at a given station you get a new sensor following this format: `[stop]_line_[line]`.

For example with stop id 8301 and line id 6 you get this sensor:
- ` sensor.remise_schaarbeek_line_6

The state returns the waiting time in minutes for the next vehicle : 

```text
sensor.remise_schaarbeek_line_6      5
```

Other attributes are :
```json
{
  "stop_name": "REMISE SCHAARBEEK",
  "line_name": "KONING BOUDEWIJN - ELISABETH",
  "line_type": "subway",
  "line_color": "0078AD",
  "line_text_color": "FFFFFF",
  "next_passing_time_1": "2020-02-26T22:09:00+01:00",
  "next_passing_destination_1": "KONING BOUDEWIJN",
  "next_passing_time_3": "2020-02-26T22:18:00+01:00",
  "next_passing_destination_3": "KONING BOUDEWIJN",
  "line": "6",
  "unit": "min",
  "attribution": "Data provided by opendata-api.stib-mivb.be",
  "friendly_name": "stib 8021  1",
  "icon": "mdi:subway"
}
```



