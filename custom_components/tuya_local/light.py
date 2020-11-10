import logging
import voluptuous as vol
import asyncio
import homeassistant.helpers.config_validation as cv

from typing import Optional, Tuple
from aiotuyalan import TuyaLight, TuyaDevice
from homeassistant.components.light import (ATTR_BRIGHTNESS, ATTR_HS_COLOR,
    ATTR_COLOR_TEMP, PLATFORM_SCHEMA, SUPPORT_BRIGHTNESS, SUPPORT_COLOR_TEMP,
    SUPPORT_COLOR, LightEntity
)
from homeassistant.const import (
    CONF_NAME, CONF_HOST, CONF_PORT, CONF_TIMEOUT, EVENT_HOMEASSISTANT_STOP
)
from homeassistant.util.color import (color_temperature_kelvin_to_mired,
    color_temperature_mired_to_kelvin, color_temperature_to_hs)

CONF_GW_ID = 'gw_id'
CONF_DEVICE_ID = 'device_id'
CONF_LOCAL_KEY = 'local_key'
CONF_VERSION = 'version'
ATTR_COLOR_MODE = "color_mode"

KELVIN_MIN=2700
KELVIN_MAX=6500
MIREDS_MIN = color_temperature_kelvin_to_mired(KELVIN_MAX)
MIREDS_MAX = color_temperature_kelvin_to_mired(KELVIN_MIN)

_LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_HOST): cv.string,
    vol.Optional(CONF_PORT, default=6668): cv.port,
    vol.Optional(CONF_GW_ID, default=''): cv.string,
    vol.Required(CONF_DEVICE_ID): cv.string,
    vol.Required(CONF_LOCAL_KEY): cv.string,
    vol.Required(CONF_VERSION): cv.string,
    vol.Optional(CONF_TIMEOUT, default=30): cv.positive_int,
    vol.Optional(CONF_NAME): cv.string,
})


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None) -> None:

    entity = TuyaLightEntity(hass, config)
    async_add_entities([entity])

    async def connect_entity():
        await entity.connect()

    async def on_ha_stop(event):
        hass.loop.create_task(entity.disconnect())

    hass.async_create_task(connect_entity())
    hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, on_ha_stop)


class TuyaLightEntity(LightEntity):

    def __init__(self, hass, config):
        self._loop = hass.loop
        self._running = True
        self._connect_wait = 0
        self._connecting = False
        self._light = TuyaLight(
            hass.loop,
            config[CONF_HOST],
            config[CONF_DEVICE_ID],
            config[CONF_LOCAL_KEY],
            version=config[CONF_VERSION],
            port=config[CONF_PORT],
            gw_id=config[CONF_GW_ID],
            timeout=config[CONF_TIMEOUT]
        )

        self._light.set_on_update(self._on_device_update)
        self._light.set_on_stop(self._on_device_stop)

        if CONF_NAME in config:
            self._name = config[CONF_NAME]
        else:
            self._name = config[CONF_DEVICE_ID]

    async def connect(self):
        self._connecting = True
        while self._running:
            if self._connect_wait > 0:
                _LOGGER.warning("Connecting again in %d seconds...", self._connect_wait)
                await asyncio.sleep(self._connect_wait)

            try:
                await self._light.connect()
                break
            except Exception as err:
                _LOGGER.warning("Error occured while connecting to Tuya Device: %s", err)
                if self._connect_wait < 60:
                    self._connect_wait += 1

        self._connecting = False
        _LOGGER.info("Connected succesfully to %s", self._name)


    async def disconnect(self):
        self._running = False
        self._connecting = False
        self._connect_wait = 0
        try:
            await self._light.disconnect()
        except:
            pass

    async def _on_device_update(self):
        self._connect_wait = 0
        self.schedule_update_ha_state()

    async def _on_device_stop(self):
        if self._running:
            _LOGGER.warning("Device disconnected. Attempting to reconnect...")
            if self._connecting:
                raise Exception("Attempt to reconnect while already reconnecting (Did we get a disconnect callback twice?)")

            if self._connect_wait < 60:
                self._connect_wait += 1
            self._loop.create_task(self.connect())

    async def async_turn_on(self, **kwargs) -> None:
        set_attrs = {}
        if ATTR_HS_COLOR in kwargs:
            set_attrs['hs_color'] = (int(kwargs[ATTR_HS_COLOR][0]),
                int(TuyaDevice.scale_value(
                    kwargs[ATTR_HS_COLOR][1], 0.0, 100.0, 0.0, 255.0)))
        if ATTR_BRIGHTNESS in kwargs:
            set_attrs['brightness'] = int(kwargs[ATTR_BRIGHTNESS])
        if ATTR_COLOR_TEMP in kwargs:
            set_attrs['color_temp'] = TuyaDevice.invert_value(
                int(TuyaDevice.scale_value(kwargs[ATTR_COLOR_TEMP], MIREDS_MIN,
                    MIREDS_MAX, 0.0, 255.0)),
                0, 255)
        set_attrs['enabled'] = True

        await self._light.set_multiple(**set_attrs)

    async def async_turn_off(self, **kwargs) -> None:
        await self._light.set_enabled(False)

    @property
    def supported_features(self) -> int:
        return SUPPORT_COLOR | SUPPORT_COLOR_TEMP | SUPPORT_BRIGHTNESS

    @property
    def name(self) -> str:
        return self._name

    @property
    def available(self) -> bool:
        return self._light._dps is not None

    @property
    def is_on(self) -> Optional[bool]:
        return self._light.get_enabled()

    @property
    def unique_id(self) -> Optional[str]:
        return self._light.get_device_info()['id']

    @property
    def brightness(self) -> Optional[int]:
        return self._light.get_brightness()

    @property
    def hs_color(self) -> Optional[Tuple[float, float]]:
        if self._light.get_mode() == TuyaLight.DPS_MODE_COLOR:
            hue, saturation = self._light.get_color_hs()
            if hue is None or saturation is None:
                return None
            else:
                return (float(hue), TuyaDevice.scale_value(saturation, 0.0, 255.0, 0.0, 100.0))
        else:
            return None

    @property
    def color_temp(self) -> int:
        if self._light.get_mode() == TuyaLight.DPS_MODE_WHITE:
            return int(TuyaDevice.scale_value(
                TuyaDevice.invert_value(self._light.get_color_temp(), 0.0, 255.0),
                0.0, 255.0, MIREDS_MIN, MIREDS_MAX
            ))
        else:
            return None

    @property
    def min_mireds(self) -> int:
        return MIREDS_MIN

    @property
    def max_mireds(self) -> int:
        return MIREDS_MAX

    @property
    def should_poll(self):
        return False
