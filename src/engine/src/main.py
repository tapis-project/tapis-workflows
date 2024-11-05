import sys, logging

from Server import Server
from utils import lbuffer_str
from conf.constants import (
    INBOUND_EXCHANGE,
    INBOUND_QUEUE,
)

# Set all third-party library loggers to critical
for name in logging.root.manager.loggerDict:
    logging.getLogger(name).setLevel(logging.CRITICAL)


server_logger = logging.getLogger("server")
handler = logging.StreamHandler(stream=sys.stdout)
handler.setFormatter(logging.Formatter(f"{lbuffer_str('[SERVER]')} %(message)s"))
server_logger.setLevel(logging.DEBUG)
server_logger.addHandler(handler)

if __name__ == "__main__":
    server = Server(
        INBOUND_QUEUE,
        INBOUND_EXCHANGE
    )
    server()

