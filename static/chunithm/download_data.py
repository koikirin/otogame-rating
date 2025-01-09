import asyncio
import aiohttp

async def main():
    url = 'https://dp4p6x0xfi5o9.cloudfront.net/chunithm/data.json'
    async with aiohttp.ClientSession() as sess:
        async with sess.get(url, proxy = "socks://127.0.0.1:7890") as res:
            with open('data.json', 'wb') as f:
                f.write(await res.read())

asyncio.run(main())