from kafka import KafkaConsumer
from typing import Any
import json
import argparse


class KafkaConsumeManager:
    def __init__(self, host: str, port: int, topic: str, group_id: str = "default", timeout_ms: int = 1000):
        self._topic = topic
        self._timeout_ms = timeout_ms
        
        self._consumer = KafkaConsumer(
            bootstrap_servers=[f"{host}:{port}"],
            auto_offset_reset="earliest",
            enable_auto_commit=False,
            group_id=group_id,
            consumer_timeout_ms=timeout_ms,
        )
        self._consumer.subscribe(topics=[self._topic])


    def receive(self) -> Any:
        records = self._consumer.poll(self._timeout_ms, 1, True)
        if not records.values():
            return
        message = list(records.values())[0][0]
        print(message)
        # return json.loads(message.value)
    

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", type=str, default="0.0.0.0")
    parser.add_argument("--port", type=int, default=29092)
    parser.add_argument("--topic", type=str, default="log")
    parser.add_argument("--group", type=str)
    config = parser.parse_args()

    consumer = KafkaConsumeManager(
        host=config.host,
        port=config.port,
        topic=config.topic,
        group_id=config.group
    )

    while True:
        consumer.receive()
