import json
import logging
import time

from aiokafka import AIOKafkaProducer

from utils.initializer import get_env

logger = logging.getLogger(__name__)
_producer: AIOKafkaProducer = None
_app_stats = 'app_stats'
_app_name = 'app_name'


async def init_kafka(app_name):
    global _producer
    if not _producer:
        _producer = AIOKafkaProducer(
            bootstrap_servers='kafka:9092',
            client_id=app_name + '-publisher',
            acks='all'
        )
        await _producer.start()
        logger.info('Connected Kafka cluster %s', _producer.client._bootstrap_servers)
    return _producer

async def send_and_wait(topic, key, value, ts=0):
    if ts <= 0:
        ts = int(1000 * time.time())
    if type(value) != str:
        value = json.dumps(value)
    return await _producer.send_and_wait(topic, key=key.encode('utf-8'), timestamp_ms=ts, value=value.encode('utf-8'))
