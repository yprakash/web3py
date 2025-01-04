import asyncio
import json
import logging
import signal
import time

from web3 import Web3

from config.sc_abis import contract_ABIs
from utils.kafka_util import init_kafka, send_and_wait
from utils.initializer import get_env

logger = logging.getLogger(__name__)


async def shutdown(shutdown_event: asyncio.Event):
    logger.info("Initiating graceful %s.shutdown...", __name__)
    shutdown_event.set()


async def init_web3(app_name):
    try:
        provider_url = get_env('PROVIDER_URL')
        global w3, _max_events_default, _default_poll_interval
        _default_poll_interval = int(get_env('W3_EVENT_POLL_INTERVAL', 1))
        _max_events_default = int(get_env('W3_EVENTS_MAX', 10))
        w3 = Web3(Web3.HTTPProvider(provider_url))
        if not w3.is_connected():
            raise Exception(f'FAILED to Connect to Web3 using {provider_url}')
        logger.info('Connected to Web3:%s. gas_price %d',
                    w3.is_connected(), w3.eth.gas_price)
        await init_kafka(app_name)
    except Exception as e:
        logger.exception(e)
        logger.error('Failed to initialize Web3: %s', str(e))
        raise e


def read_contracts_from_file():
    contracts = []
    with open('config/sc_tokens.json', 'r') as file:
        sc_tokens = json.load(file)
    with open('config/sc_subscribe_events.json', 'r') as file:
        sc_events = json.load(file)

    for symbol, events in sc_events.items():
        for event in events:
            if symbol in sc_tokens and symbol in contract_ABIs:
                contracts.append((symbol, event, sc_tokens[symbol], contract_ABIs[symbol]))

    return contracts


async def subscribe_to_events():
    contracts = read_contracts_from_file()  # Read contracts and events from a text file
    listeners = []
    shutdown_event = asyncio.Event()
    asyncio.get_event_loop().add_signal_handler(signal.SIGINT, lambda: asyncio.create_task(shutdown(shutdown_event)))
    asyncio.get_event_loop().add_signal_handler(signal.SIGTERM, lambda: asyncio.create_task(shutdown(shutdown_event)))

    for symbol, event_name, address, abi in contracts:
        try:
            listeners.append(EventListener(symbol, event_name, address, abi, shutdown_event))
        except Exception as e:
            logger.error('Failed to create EventListener for %s.%s : %s', symbol, event_name, str(e))

    if not listeners:
        logger.error('Exiting as NO listeners created')
        return False
    logger.info('Created %d EventListeners. Started listening to those events', len(listeners))

    # Create a list of tasks to run all listeners concurrently
    listener_tasks = [asyncio.create_task(listener.listen_for_events()) for listener in listeners]
    await asyncio.gather(*listener_tasks)  # Run all listeners concurrently
    logger.info("All listeners are completed.")


class EventListener:
    def __init__(self, symbol, event_name, contract_address, abi,
                 shutdown_event, poll_interval=None, max_events=None):
        self.event_name = symbol + '.' + event_name
        self.shutdown_event = shutdown_event
        self.max_events = max_events if max_events is not None else _max_events_default
        self.poll_interval = poll_interval if poll_interval is not None else _default_poll_interval
        self.contract = w3.eth.contract(abi=abi, address=w3.to_checksum_address(contract_address))

        event_class = getattr(self.contract.events, event_name, None)
        if not event_class:
            raise ValueError(f"Can't create event. Event {event_name} not found in contract ABI")
        self.event_filter = event_class.create_filter(from_block='latest')
        logger.debug(f'Created event filter for {self.event_name} under contract {self.contract.address}')

    async def event_handler(self, event):
        event = json.loads(w3.to_json(event))
        value = {'gen_ts': int(1000 * time.time())}
        value.update(event)
        logger.debug('Event %s occurred: %s', self.event_name, event)
        res = await send_and_wait('events', self.event_name, value)
        if res:
            # logger.debug('Producer res= %s', res)
            return True
        logger.error('Not sent %s', value)
        return False

    async def listen_for_events(self):
        received_count, published_count, tt_process = 0, 0, 0
        while True:
            logs = await asyncio.to_thread(self.event_filter.get_new_entries)
            received_count += len(logs)
            logger.debug('got %d new_entries %s', len(logs), self.event_name)
            if logs:
                tt = time.time()
                for event in logs:
                    published = await self.event_handler(event)
                    if published:
                        published_count += 1
                tt = int(1000 * (time.time() - tt))
                tt_process += tt
                logger.debug('Time taken to process %d %s events: %d ms', len(logs), self.event_name, tt)
                if published_count >= self.max_events:
                    break
            else:
                self.poll_interval += 1

            if self.shutdown_event.is_set():
                logger.info('break in listen_for_events as shutdown_event.is_set()')
                break
            await asyncio.sleep(self.poll_interval)

        tt_avg = tt_process // received_count if received_count > 0 else tt_process
        logger.info('Received %d and published %d %s events Total tt %d Avg tt %d ms. Closed',
                    received_count, published_count, self.event_name, tt_process, tt_avg)
