import sys
import cwrouter
import logging
from logging.handlers import RotatingFileHandler
import os.path
import requests

from cwrouter.config import Config, DEFAULT_CONFIG_DIR, ensure_config_dir_exists
from cwrouter.stats import Stats
from cwrouter.put import put
from cwrouter.exceptions import PutException, StatsLookupException

class ExitStatus:
    OK = 0
    ERROR = 1
    NO_CONFIG = 2

def setup_logger():
    ensure_config_dir_exists(DEFAULT_CONFIG_DIR)
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler = RotatingFileHandler(os.path.join(DEFAULT_CONFIG_DIR, "cwrouter.log"),
                                      maxBytes=10*(2**10),  # 10 MB
                                      backupCount=1)        # keep 1 extra file
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger

def main():
    config = Config()
    logger = setup_logger()

    if config.is_new():
        logger.error("cwrouter is stopping because you have no config! skeleton written to %s. fill in your credentials.", config.path)
        config.save()
        return ExitStatus.NO_CONFIG

    config.load()
    stat_url = config['stats_url']
    last_stats = config.last_stats()

    try:
        new_stats = Stats.from_request(stats_url=stat_url)
    except StatsLookupException:
        logger.exception() #raises the exception
        return ExitStatus.ERROR

    if last_stats.is_empty():
        delta = Stats(None, recv_bytes=0, trans_bytes=0)
    else:
        delta = Stats.delta(last_stats, new_stats)

    try:
        put(delta, config)
    except PutException:
        logger.exception() #raises the exception
        return ExitStatus.ERROR
    logger.info("Sent %s" % str(delta))

    config.update_last_stats(new_stats)
    config.save()
    return ExitStatus.OK

if __name__ == "__main__":
    sys.exit(main())
