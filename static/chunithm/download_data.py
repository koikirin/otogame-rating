import asyncio
import aiohttp

PROXY = None
try:
    with open('../PROXY', 'r') as f:
        PROXY = f.read().strip()
except:
    pass

async def main():
    url = 'https://dp4p6x0xfi5o9.cloudfront.net/chunithm/data.json'
    async with aiohttp.ClientSession() as sess:
        async with sess.get(url, proxy = PROXY) as res:
            with open('data.json', 'wb') as f:
                f.write(await res.read())

asyncio.run(main())