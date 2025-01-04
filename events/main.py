import asyncio
import logging
import os

from pathlib import Path

from events_w3 import init_web3, subscribe_to_events
from utils.initializer import init
from utils.log_util import set_module_log_level

logger = logging.getLogger('main')


async def initialize():
    # Get the absolute path to the current file (this script)
    current_file_path = os.path.abspath(__file__)
    # Get the micro-service name from the parent directory
    app_name = Path(current_file_path).parent.name

    init(app_name)
    set_module_log_level('urllib3')
    set_module_log_level('web3')
    set_module_log_level('aiokafka')

    await init_web3(app_name)
    logger.info('Service %s initialized successfully', app_name)

async def main():
    try:
        await initialize()
    except Exception as e:
        print('Failed to Initialize', str(e))
        exit(0)

    try:
        await subscribe_to_events()
    # except KeyboardInterrupt: logger.error(f'\nExiting as KeyboardInterrupt\n')
    except Exception as e:
        logger.exception(e)
        logger.log(logging.DEBUG, '=' * 100)


if __name__ == "__main__":
    asyncio.run(main())
