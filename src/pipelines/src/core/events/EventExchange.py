import logging

from typing import List, Union
from threading import Lock

from corevent.events import EventHandler, Event
from corevent.events.ExchangeConfig import ExchangeConfig


class EventExchange:
    def __init__(self, config: ExchangeConfig=None):
        # If no config is provided use the default exchange config
        if config == None:
            config = ExchangeConfig()

        self._set_config(config)

        self.lock = Lock()

    

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

    def publish(self, event: List[Event]):
        for key in self.subscribers:
            # Prevent allow once events to only be called once
            self.lock.acquire()
            if event.type in self._config.allow_once and event.type in self.handled_events:
                return

            self.handled_events.append(event.type)
            self.lock.release()

        subscriber = self.subscribers[key]
        if event.type in subscriber["events"]:
            try:
                subscriber["handler"].handle(event)
            except Exception as exception:
                logging.error(f"EVENT EXCHANGE ERROR: {str(exception)}")

        # Reset on the configured reset event
        if event.type in self._config.reset_on:
            self.reset()

    def _set_config(self, config: ExchangeConfig):
        self._config = config
        self._set_initial_state()

    def reset(self):
        self._set_initial_state()

    def _set_initial_state(self):
        self.subscribers = {}
        self.handled_events = []