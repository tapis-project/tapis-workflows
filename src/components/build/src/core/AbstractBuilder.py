from abc import ABC, abstractmethod


class AbstractBuilder(ABC):
    @abstractmethod
    def build(self, request):
        pass