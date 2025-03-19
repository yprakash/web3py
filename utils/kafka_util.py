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
            # enable_idempotence=True,
            bootstrap_servers='kafka:9092',  # get_env('KAFKA_BROKER', 'kafka:9092'),
            client_id=app_name + '-publisher',
            acks='all',  # Ensures all replicas acknowledge the message
            compression_type=get_env('PUBLISH_COMPRESS_TYPE', 'gzip'),  # Optional optimization: compress messages

            # Batch size in bytes (16 KB by default) allocated per partition
            max_batch_size=get_env('PUBLISH_BATCH_SIZE', 32768),
            # linger.ms Time to wait before sending a batch: we increase the chances of messages being sent
            # together in a batch. And at the expense of this small delay, we can increase the throughput, compression,
            # and efficiency of the producer. So overall, adding a small delay may actually increase the efficiency
            linger_ms=get_env('PUBLISH_LINGER_MS', 20)
        )
        await _producer.start()
        logger.info('Connected Kafka cluster %s', _producer.client._bootstrap_servers)
        # finally: await _producer.stop()
    return _producer

async def send_and_wait(topic, key, value, ts=0):
    if ts <= 0:
        ts = int(1000 * time.time())
    if type(value) != str:
        value = json.dumps(value)
    return await _producer.send_and_wait(topic, key=key.encode('utf-8'), timestamp_ms=ts, value=value.encode('utf-8'))
