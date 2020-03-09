"""Support for STIB-MIVB (Brussels public transport) information."""
import logging
from pyodstibmivb import ODStibMivb
import voluptuous as vol
import pytz
import datetime

from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import ATTR_ATTRIBUTION, DEVICE_CLASS_TIMESTAMP # TIME_MINUTES
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity

_LOGGER = logging.getLogger(__name__)

ATTRIBUTION = "Data provided by opendata.stib-mivb.be"

CONF_STOPS = "stops"
CONF_STOP_ID = "stop_id"
CONF_API_KEY = "api_key"
CONF_LANG = "lang"
CONF_MESSAGE_LANG = "message_lang"
CONF_LINE_NUMBER = "line_number"

DEFAULT_NAME = "Stib-Mivb"

SUPPORTED_LANGUAGES = ["nl", "fr"]

SUPPORTED_MESSAGE_LANGUAGES = ["en", "nl", "fr"]

TYPE_ICONS = {
    "0": "mdi:tram",
    "1": "mdi:subway",
    "3": "mdi:bus",
}

TYPES = {
    "0": "tram",
    "1": "subway",
    "3": "bus",
}


STOP_SCHEMA = vol.Schema(
    {vol.Required(CONF_STOP_ID): cv.string, vol.Required(CONF_LINE_NUMBER): cv.string}
)

STOPS_SCHEMA = vol.All(cv.ensure_list, [STOP_SCHEMA])

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_API_KEY): cv.string,
        vol.Required(CONF_LANG): vol.In(SUPPORTED_LANGUAGES),
        vol.Optional(CONF_MESSAGE_LANG): vol.In(SUPPORTED_MESSAGE_LANGUAGES),
        vol.Optional(CONF_STOPS): STOPS_SCHEMA,
    }
)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Create the sensor."""
    api_key = config[CONF_API_KEY]
    name = DEFAULT_NAME
    if config[CONF_MESSAGE_LANG]:
        message_lang = config[CONF_MESSAGE_LANG]
    else:
        message_lang = config[CONF_LANG]

    session = async_get_clientsession(hass)

    api = ODStibMivb(api_key, session)

    sensors = []
    for stop in config.get(CONF_STOPS):
        sensors.append(
            StibMivbSensor(
                api,
                stop.get(CONF_STOP_ID),
                stop.get(CONF_LINE_NUMBER),
                config[CONF_LANG],
                message_lang,
            )
        )

    async_add_entities(sensors, True)


class StibMivbSensor(Entity):
    """Representation of a Ruter sensor."""

    def __init__(self, api, stop_id, line_id, lang, message_lang):
        """Initialize the sensor."""
        self.api = api
        self.stop_id = stop_id
        self.line_id = line_id
        self.lang = lang
        self.message_lang = message_lang
        self._attributes = {ATTR_ATTRIBUTION: ATTRIBUTION}
        self._state = None
        self._stop_name = None
        # right now only available in dev
        self._unit = "min"
        #self._unit = TIME_MINUTES

    async def async_update(self):
        """Get the latest data from the StibMivb API."""
        if self._stop_name is None:
            stop_name = await self.api.get_point_detail(self.stop_id)
            self._stop_name = stop_name["points"][0]["name"][self.lang]
            self._attributes["stop_name"] = self._stop_name
        self._name = self._stop_name + " line " + self.line_id
        line_name = await self.api.get_line_long_name(self.line_id)
        if self.lang == 'nl':
            line_name = await self.api.get_translation_nl(line_name)
        self._attributes["line_name"] = line_name

        response = await self.api.get_message_by_line(self.line_id)
        for i, message in enumerate(response["messages"]):
            self._attributes[f"message_{i}"] = message["content"][0]["text"][0][
                self.lang
            ]
        type = await self.api.get_line_type(self.line_id)
        self._attributes["line_type"] = TYPES[type]
        self.__icon = TYPE_ICONS[type]
        self._attributes["line_color"] = await self.api.get_line_color(self.line_id)
        self._attributes["line_text_color"] = await self.api.get_line_text_color(
            self.line_id
        )

        response = await self.api.get_waiting_time(self.stop_id)
        state_set = False
        for i, passing_time in enumerate(response["points"][0]["passingTimes"]):
            if passing_time["lineId"] == self.line_id:
                if state_set == False:
                    next_passing_time = pytz.utc.normalize(
                        datetime.datetime.fromisoformat(
                            passing_time["expectedArrivalTime"]
                        )
                    )
                    state_set = True
                    now = pytz.utc.normalize(pytz.utc.localize(datetime.datetime.utcnow()))
                    self._state = round((next_passing_time - now).total_seconds()/60)

                self._attributes[f"next_passing_time_{i}"] = passing_time[
                    "expectedArrivalTime"
                ]
                self._attributes[f"next_passing_destination_{i}"] = passing_time[
                    "destination"
                ][self.lang]

    @property
    def device_class(self):
        """Return the device class."""
        return DEVICE_CLASS_TIMESTAMP

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def icon(self):
        """Return the icon of the sensor."""
        return self.__icon

    @property
    def device_state_attributes(self):
        """Return attributes for the sensor."""
        return self._attributes
