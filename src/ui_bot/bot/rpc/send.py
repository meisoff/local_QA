from src.db.connection import get_connection


async def send_rabbit(message: str) -> None:
    async with get_connection() as connection:
        channel = await connection.channel()

        declare_ok = await channel.queue_declare("hello")
        body = bytes(message, "utf-8")
        await channel.basic_publish(
            exchange="", routing_key=declare_ok.queue, body=body
        )
        print(f" [x] Sent {message}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(send_rabbit("Hello Ed354uarde1"))
