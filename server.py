import aiohttp
import asyncio
import fastapi
import json
import os
import uvicorn

from io import BytesIO
from pathlib import Path


ROOT: Path = Path(__file__).parent
STATIC: Path = ROOT / 'static'

PROXY = None
try:
    with open('static/PROXY', 'r') as f:
        PROXY = f.read().strip()
except:
    pass

app = fastapi.FastAPI()


import ongeki_rating as Ongeki
import chunithm_rating as Chunithm


@app.get('/ongeki/update')
async def _():
    RES_DIR: Path = STATIC / 'ongeki'

    url = 'https://dp4p6x0xfi5o9.cloudfront.net/ongeki/data.json'
    async with aiohttp.ClientSession() as sess:
        async with sess.get(url, proxy = PROXY) as res:
            with open(RES_DIR / 'data.json', 'wb') as f:
                f.write(await res.read())

        with open(RES_DIR / 'data.json', 'r') as f:
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

        for song in data["songs"]:
            img = song["imageName"]
            if os.path.exists(RES_DIR / f'cover_ori/{img}'):
                # print('skip', img)
                continue
            url = f'https://dp4p6x0xfi5o9.cloudfront.net/ongeki/img/cover-m/{img}'
            print(url)
            await download(url, RES_DIR / f'cover_ori/{img}')

        print('updated, reloading data')
        Ongeki.loadData()


@app.get('/chunithm/update')
async def _():
    RES_DIR: Path = STATIC / 'chunithm'

    url = 'https://dp4p6x0xfi5o9.cloudfront.net/chunithm/data.json'
    async with aiohttp.ClientSession() as sess:
        async with sess.get(url, proxy = PROXY) as res:
            with open(RES_DIR / 'data.json', 'wb') as f:
                f.write(await res.read())

        with open(RES_DIR / 'data.json', 'r') as f:
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

        for song in data["songs"]:
            img = song["imageName"]
            if os.path.exists(RES_DIR / f'cover_ori/{img}'):
                # print('skip', img)
                continue
            url = f'https://dp4p6x0xfi5o9.cloudfront.net/chunithm/img/cover-m/{img}'
            print(url)
            await download(url, RES_DIR / f'cover_ori/{img}')

        print('updated, reloading data')
        Chunithm.loadData()


@app.post('/ongeki/generate')
async def _generate(data: Ongeki.RequestPayload):
    img = await asyncio.to_thread(Ongeki.generate, data.data, data.params)
    output_buffer = BytesIO()
    img.save(output_buffer, 'JPEG', optimize=True)
    return fastapi.Response(output_buffer.getvalue(), media_type='image/jpeg')


@app.post('/chunithm/generate')
async def _generate(data: Chunithm.RequestPayload):
    img = await asyncio.to_thread(Chunithm.generate, data.data, data.params)
    output_buffer = BytesIO()
    img.save(output_buffer, 'JPEG', optimize=True)
    return fastapi.Response(output_buffer.getvalue(), media_type='image/jpeg')

# main
uvicorn.run(app, host='127.0.0.1', port=5150)
