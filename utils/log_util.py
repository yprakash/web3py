import json
import logging
import logging.config
import os
import sys
from os.path import join as pjoin
from concurrent_log_handler import ConcurrentRotatingFileHandler  # This is needed to load in the Rotating File Handler

logger = logging.getLogger(__name__)


def setup_logging(app_name, default_log_config='py_logging.json', default_level=logging.DEBUG, env_key='LOG_CFG'):
    # value is None below, if it is called even before initializer.load_envs()
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
        STD_OUT_PATH_KEY = 'std.out.filename'
        if STD_OUT_PATH_KEY in config.keys():
            global _OUT_FILE_OBJ
            _OUT_FILE_OBJ = open(config[STD_OUT_PATH_KEY], 'a', 1)
            sys.stdout = _OUT_FILE_OBJ
            sys.stderr = _OUT_FILE_OBJ
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


def set_module_log_level(module, log_level=logging.INFO):
    if module:
        logging.getLogger(module).setLevel(log_level)


def close_std_out_file():
    try:
        if _OUT_FILE_OBJ:
            if not _OUT_FILE_OBJ.closed:
                _OUT_FILE_OBJ.close()
                logger.info('Closed Out file')
    except BaseException as e:
        logger.error('Failed to close standard out file. Error: %s', str(e), exc_info=1)
