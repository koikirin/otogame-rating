import json
import asyncio
import aiohttp
import os

with open('data.json', 'r') as f:
    data = json.load(f)

versions = []
for song in data["songs"]:
    if song["version"] not in versions:
        versions.append(song["version"])

print(versions)