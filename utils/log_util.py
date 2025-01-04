import json
import logging
import logging.config
import os
import sys
from os.path import join as pjoin
from concurrent_log_handler import ConcurrentRotatingFileHandler  # This is needed to load in the Rotating File Handler

logger = logging.getLogger(__name__)


def setup_logging(app_name, default_log_config='py_logging.json', default_level=logging.DEBUG, env_key='LOG_CFG'):
    value = os.getenv(env_key, None)
    if value:
        path = value
    else:
        CONFIG_DIR = './config'
        path = pjoin(CONFIG_DIR, default_log_config)

    if os.path.exists(path):
        print('Loading logging configuration from', path)
        with open(path, 'rt') as f:
            config = json.load(f)

        logging.config.dictConfig(config)
    else:
        logs_dir = './logs'
        if not os.path.exists(logs_dir):
            os.makedirs(logs_dir, exist_ok=True)
        log_path = logs_dir + '/pipeline.log'

        file_handler = logging.FileHandler(filename=log_path)
        stdout_handler = logging.StreamHandler(stream=sys.stdout)
        _handlers = [file_handler, stdout_handler]
        logging.basicConfig(
            level=default_level,
            format=app_name + ' %(levelname)s %(asctime)s.%(msecs)03d %(threadName)s %(name)s:%(lineno)d %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
            handlers=_handlers
        )
        print(f'Setting default logging configuration as {path} not found')
