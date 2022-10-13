import logging

from typing import List, Union

from core.events import EventHandler, Event
from core.events.ExchangeConfig import ExchangeConfig


class EventExchange:
    def __init__(self, config: ExchangeConfig=None):
        # If no config is provided use the default exchange config
        if config == None:
            config = ExchangeConfig()

        self._set_config(config)

    def add_subscribers(
        self,
        subscribers: Union[
            EventHandler, 
            List[EventHandler]
        ],
        events: List[str] = []
    ):
        if type(subscribers) == List:
            for subscriber in subscribers:
                self.add_subscriber(subscriber, events)
            return

        self._add_subscriber(subscribers, events)

    def _add_subscriber(self, subscriber: EventHandler, events):
        key = id(subscriber)
        
        self.subscribers[key] = {
            "handler": subscriber,
            "events": events
        }

    def publish(self, events: List[Event]):
        for e in events:
            for key in self.subscribers:
                subscriber = self.subscribers[key]
                if e.type in subscriber["events"]:
                    try:
                        subscriber["handler"].handle(e)
                    except Exception as exception:
                        logging.error(f"ERROR: {str(exception)}")

        # Reset on the configured reset event
        if e.type in self._config.reset_on:
            self.reset()

    def _set_config(self, config: ExchangeConfig):
        self._config = config
        self._set_initial_state()

    def reset(self):
        self._set_initial_state()

    def _set_initial_state(self):
        self.subscribers = {}