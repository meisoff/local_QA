import asyncio
import os
from contextlib import asynccontextmanager

import aiormq
from dotenv import load_dotenv

load_dotenv()

AMQP_USER = os.getenv("AMQP_USER")
AMQP_PASSWORD = os.getenv("AMQP_PASSWORD")
AMQP_ADDRESS = os.getenv("AMQP_ADDRESS")
AMQP_VHOST = os.getenv("AMQP_VHOST")
AMQP_PORT = os.getenv("AMQP_PORT")


async def wait_for_rabbitmq():
    max_retries = 10
    retry_delay = 5

    for _ in range(max_retries):
        try:
            url = (
                    f"amqp://{AMQP_USER}:{AMQP_PASSWORD}@{AMQP_ADDRESS}:{AMQP_PORT}/{AMQP_VHOST}"
            )
            connection = await aiormq.connect(url)
            await connection.close()
            print("RabbitMQ is up and running.")
            return True
        except Exception as e:
            print(f"Connection to RabbitMQ failed: {e}")
            print("Connection to RabbitMQ failed. Retrying...")
            await asyncio.sleep(retry_delay)

    print("Failed to connect to RabbitMQ after multiple retries.")
    return False


@asynccontextmanager
async def get_connection(local: bool = False) -> aiormq.abc.AbstractConnection:
    if local:
        connection = await aiormq.connect("amqp://localhost")
    else:
        if not await wait_for_rabbitmq():
            raise SystemExit("Unable to connect to RabbitMQ. Exiting...")

        url = (
                f"amqp://{AMQP_USER}:{AMQP_PASSWORD}"
                + f"@{AMQP_ADDRESS}:{AMQP_PORT}/{AMQP_VHOST}"
        )
        connection = await aiormq.connect(url)

    try:
        yield connection
    finally:
        await connection.close()
