from typing import Any
import json
import random
from kafka import KafkaProducer
import argparse
import time


class KafkaProduceManager:
    def __init__(self, host: str, port: int, topic: str):
        self._topic = topic
        
        self._producer = KafkaProducer(
            acks=1,
            compression_type='gzip',
            bootstrap_servers=[f"{host}:{port}"]
        )


    def send(self, message: Any):
        self._producer.send(
            topic=self._topic,
            key=None,
            value=json.dumps(message, ensure_ascii=False, default=str).encode(),
            partition=random.randint(0, len(self._producer.partitions_for(self._topic)) - 1),
        )
        self._producer.flush()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", type=str, default="0.0.0.0")
    parser.add_argument("--port", type=int, default=29092)
    parser.add_argument("--topic", type=str, default="log")
    config = parser.parse_args()

    producer = KafkaProduceManager(
        host=config.host,
        port=config.port,
        topic=config.topic,
    )

    for i in range(10):
        producer.send(f"test log {i}")
        time.sleep(0.1)