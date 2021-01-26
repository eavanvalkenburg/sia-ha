"""The sia hub."""
import asyncio
from datetime import timedelta
from typing import Tuple
import logging

from pysiaalarm.aio import SIAAccount, SIAClient, SIAEvent

from homeassistant.core import Event, EventOrigin
from homeassistant.const import CONF_PORT
from homeassistant.core import Event, HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.typing import EventType

from .const import (
    CONF_ACCOUNT,
    CONF_ACCOUNTS,
    CONF_ENCRYPTION_KEY,
    EVENT_CODE,
    EVENT_ACCOUNT,
    EVENT_ZONE,
    EVENT_PORT,
    EVENT_MESSAGE,
    EVENT_ID,
    EVENT_TIMESTAMP,
    DOMAIN,
    SIA_EVENT,
)

_LOGGER = logging.getLogger(__name__)


class SIAHub:
    """Class for SIA Hubs."""

    def __init__(
        self, hass: HomeAssistant, hub_config: dict, entry_id: str, title: str
    ):
        """Create the SIAHub."""
        self._hass = hass
        self._port = int(hub_config[CONF_PORT])
        self.entry_id = entry_id
        self._title = title
        self._accounts = hub_config[CONF_ACCOUNTS]

        self.sia_accounts = [
            SIAAccount(a[CONF_ACCOUNT], a.get(CONF_ENCRYPTION_KEY), (300, 150))
            for a in self._accounts
        ]
        self.sia_client = SIAClient(
            "", self._port, self.sia_accounts, self.async_create_and_fire_event
        )

    async def async_setup_hub(self):
        """Add a device to the device_registry, register shutdown listener, load reactions."""
        device_registry = await dr.async_get_registry(self._hass)
        port = self._port
        for acc in self._accounts:
            account = acc[CONF_ACCOUNT]
            device_registry.async_get_or_create(
                config_entry_id=self.entry_id,
                identifiers={(DOMAIN, port, account)},
                name=f"{port} - {account}",
            )

    async def async_shutdown(self, _: Event):
        """Shutdown the SIA server."""
        await self.sia_client.stop()

    async def async_create_and_fire_event(self, event: SIAEvent):
        """Create a event on HA's bus, with the data from the SIAEvent."""
        event_data = {
            EVENT_PORT: self._port,
            EVENT_ACCOUNT: event.account,
            EVENT_ZONE: event.ri,
            EVENT_CODE: event.code,
            EVENT_MESSAGE: event.message,
            EVENT_ID: event.id,
            EVENT_TIMESTAMP: event.timestamp,
        }
        self._hass.bus.async_fire(
            f"{SIA_EVENT}_{self._port}_{event.account}",
            event_data,
            origin=EventOrigin.remote,
        )
