import sys
import logging
from logging.handlers import RotatingFileHandler
from logging import StreamHandler
import os.path

from cwrouter.config import Config, DEFAULT_CONFIG_DIR, ensure_config_dir_exists
from cwrouter.stats import Stats
from cwrouter.put import PutMetrics
from cwrouter.exceptions import PutException, StatsLookupException, DocumentParseException, EmptyStatsException


class ExitStatus:
    OK = 0
    ERROR = 1
    NO_CONFIG = 2


def setup_logger():
    ensure_config_dir_exists()
    logger = logging.getLogger(__name__)

    rfhandler = RotatingFileHandler(os.path.join(DEFAULT_CONFIG_DIR, "cwrouter.log"),
                                    maxBytes=10 * (2 ** 20),  # 10 MB
                                    backupCount=1)  # keep 1 extra file
    rfhandler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(rfhandler)

    shandler = StreamHandler(sys.stderr)
    shandler.setFormatter(logging.Formatter('%(message)s'))
    logger.addHandler(shandler)

    logger.setLevel(logging.INFO)

    return logger


def main(config=Config(), logger=setup_logger()):
    if config.is_new():
        logger.error(
                "cwrouter is stopping because you have no config! skeleton written to %s. fill in your credentials.",
                config.path)
        config.save()
        return ExitStatus.NO_CONFIG

    config.load()
    stat_url = config['stats_url']

    try:
        last_stats = config.last_stats()
    except EmptyStatsException:
        last_stats = Stats(recv_bytes=0, sent_bytes=0)

    try:
        new_stats = Stats.from_request(stats_url=stat_url)
    except StatsLookupException as e:
        logger.error(e)
        return ExitStatus.ERROR
    except DocumentParseException as e:
        logger.error(e)
        return ExitStatus.ERROR

    delta = Stats.delta(last_stats, new_stats)

    try:
        pm = PutMetrics.build_from_creds(config['aws_access_key_id'], config['aws_secret_access_key'])
        pm.put(config['namespace'], delta)
    except PutException as e:
        logger.error(e)
        return ExitStatus.ERROR
    logger.info(str(delta))

    config.update_last_stats(new_stats)
    config.save()
    return ExitStatus.OK
