import sys, logging

from core.Application import Application


# Set all lib loggers to critical
for name in logging.root.manager.loggerDict:
    logging.getLogger(name).setLevel(logging.CRITICAL)

logging.basicConfig(
    # filename=LOG_FILE,
    stream=sys.stdout,
    level=logging.DEBUG,
    # format="[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s",
    format="[%(asctime)s] %(message)s",
)

app = Application()
app()

