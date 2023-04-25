from typing import List, Union
from owe_python_sdk.events import Event, EventHandler, EventExchange


class EventPublisher:
    def __init__(self, exchange: EventExchange):
        self.exchange = exchange

    def add_subscribers(
        self,
        subscribers: Union[
            EventHandler,
            List[EventHandler]
        ],
        events: List[str] = []
    ):
        self.exchange.add_subscribers(subscribers, events)

    def publish(self, event: Event, *args):
        events = [event, *args]
        self.exchange.publish(events)