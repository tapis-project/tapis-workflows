import sys, logging

from core.PipelineService import PipelineService


# Set all lib loggers to critical
for name in logging.root.manager.loggerDict:
    logging.getLogger(name).setLevel(logging.CRITICAL)

logging.basicConfig(
    # filename=LOG_FILE,
    stream=sys.stdout,
    level=logging.DEBUG,
    format="[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s",
)

service = PipelineService()
service.start()

