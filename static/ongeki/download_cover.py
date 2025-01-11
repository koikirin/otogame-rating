import json
import asyncio
import aiohttp
import os

PROXY = None
try:
    with open('../PROXY', 'r') as f:
        PROXY = f.read().strip()
except:
    pass

with open('data.json', 'r') as f:
    data = json.load(f)

async def download(url, path):
    try:
        async with sess.get(url, headers = {
            "Uesr-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7"
        }, timeout = 5, proxy = PROXY) as res:
            with open(path, 'wb') as f:
                f.write(await res.read())
    except Exception as e:
        print('error', e, url)

async def main():
    global sess
    async with aiohttp.ClientSession() as sess:
        for song in data["songs"]:
            img = song["imageName"]
            if os.path.exists(f'cover_ori/{img}'):
                # print('skip', img)
                continue
            url = f'https://dp4p6x0xfi5o9.cloudfront.net/ongeki/img/cover-m/{img}'
            print(url)
            await download(url, f'cover_ori/{img}')

asyncio.run(main())