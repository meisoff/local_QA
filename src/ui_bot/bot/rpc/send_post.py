import os

import aiohttp


async def send_message(message):
    external_api_url = os.getenv("EXTERNAL_API_URL")
    if external_api_url:
        # payload = {"message": message}
        async with aiohttp.ClientSession() as session:
            async with session.get(
                external_api_url
            ) as response:
                print(
                    f" [x] Sent POST request to {external_api_url}. "
                    f"Response: {response.status}"
                )
