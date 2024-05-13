import asyncio
import aiormq

from src.db.connection import get_connection
from src.ui_bot.bot.bot import main as bot_main
from src.ui_bot.bot.rpc.send_post import send_message


async def main():
    async with get_connection() as connection:
        channel = await connection.channel()

        async def callback(message: aiormq.abc.DeliveredMessage):
            body = str(message.body.decode("utf-8"))
            method, body = body.split(" ", 1)
            print(f"Method: {method}, Last Message: {body}", flush=True)

            if method == "send":
                await send_message(body)

        declare_ok = await channel.queue_declare("hello")
        consume_ok = await channel.basic_consume(  # noqa: F841
            declare_ok.queue, callback, no_ack=True
        )

        print("[*] Waiting for messages. To exit press CTRL+C", flush=True)

        await asyncio.Event().wait()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    #tasks = [bot_main(), main()]
    tasks = [bot_main()]
    loop.run_until_complete(asyncio.gather(*tasks))
    loop.close()
