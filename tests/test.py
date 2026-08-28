from loguru import logger

logger.add("msg.log")

logger.info("info msg")
logger.warning("warning msg")
logger.error("error msg")
logger.critical("critical msg")
