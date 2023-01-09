import sys, logging

from core.Dispatcher import Dispatcher


# Set all lib loggers to critical
for name in logging.root.manager.loggerDict:
    logging.getLogger(name).setLevel(logging.CRITICAL)


dispatcher_logger = logging.getLogger("dispatcher")
handler = logging.StreamHandler(stream=sys.stdout)
handler.setFormatter(logging.Formatter("[%(asctime)s] %(message)s"))
dispatcher_logger.setLevel(logging.DEBUG)
dispatcher_logger.addHandler(handler)
# logging.basicConfig(
#     # filename=LOG_FILE,
#     stream=sys.stdout,
#     level=logging.DEBUG,
#     # format="[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s",
#     format="[%(asctime)s] %(message)s",
# )

dispatcher = Dispatcher()
dispatcher()

