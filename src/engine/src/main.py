import sys, logging

from Server import Server


# Set all third-party library loggers to critical
for name in logging.root.manager.loggerDict:
    logging.getLogger(name).setLevel(logging.CRITICAL)


server_logger = logging.getLogger("server")
handler = logging.StreamHandler(stream=sys.stdout)
handler.setFormatter(logging.Formatter("%(message)s"))
server_logger.setLevel(logging.DEBUG)
server_logger.addHandler(handler)
# logging.basicConfig(
#     # filename=LOG_FILE,
#     stream=sys.stdout,
#     level=logging.DEBUG,
#     # format="[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s",
#     format="[%(asctime)s] %(message)s",
# )

if __name__ == "__main__":
    server = Server()
    server()

