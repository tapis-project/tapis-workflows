from abc import ABC, abstractmethod


class AbstractBuildHandler(ABC):
    @abstractmethod
    def handle(self, build_context):
        pass