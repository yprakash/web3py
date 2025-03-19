import logging
import os
import signal

from dotenv import load_dotenv
from utils.log_util import setup_logging

logger = logging.getLogger(__name__)


def graceful_exit(*args):
    global _CONSUME_EVENTS
    _CONSUME_EVENTS = False
    logger.info('Exiting gracefully... _CONSUME_EVENTS set to False')


def register_shutdown_scripts():
    signal.signal(signal.SIGINT, graceful_exit)
    signal.signal(signal.SIGTERM, graceful_exit)


def create_root_dirs(parent_dir=None, path=None):
    if not parent_dir:
        parent_dir = os.path.dirname(path)
    if not os.path.exists(parent_dir):
        os.makedirs(parent_dir, exist_ok=True)


def finalize(app_name):
    logger.info('Finalizing %s service..', app_name)


def init(app_name):
    setup_logging(app_name)
    logger.info('Initializing %s service..', app_name)
    # register_shutdown_scripts()
    load_envs(app_name)


def load_envs(app_name):
    env_path = '.env'
    load_dotenv(dotenv_path=env_path)

    # Load ms specific env file (if it exists) with override set to True
    env_path = env_path + '.' + app_name
    load_dotenv(dotenv_path=env_path, override=True)


def get_env(key, default=None, throw=True):
    # though configparser can Organize (configuration settings into sections/hierarchical),
    # all other ways are Not cloud-native and Less secure for sensitive data
    val = os.getenv(key, default)
    if val is None:
        if throw and default is None:
            raise RuntimeError(f'env variable "{key}" not found. Please check')
        val = default
    return val
