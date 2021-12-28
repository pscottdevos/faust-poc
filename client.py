#! /usr/bin/env python3
import asyncio
import atexit
import itertools
import json
import random
from collections import defaultdict, OrderedDict
import sys
from time import sleep, time

import aiohttp
import faust
from pynput.keyboard import Key, Listener

from server import KeyModel, ValueModel
from utils.term import get_term_reader_protocol #, print, json


fapp = faust.App('faust poc', broker='kafka://', store='memory://')


class Rnd(object):
    
    R = 4.0

    def __init__(self, transform=lambda x: x, seed=None):
        while not seed or 0 < seed >=1:
            seed = time() % 1
        self.seed = seed
        self.transform = transform

    def __call__(self):
        self.seed = self.R * self.seed * (1.0 - self.seed)
        return self.transform(self.seed)


fpoc_topic = fapp.topic("fpoc",
    key_type=KeyModel,
    key_serializer="json",
    value_type=ValueModel,
    partitions=5,
)


url = "http://localhost:6066/values"
async def http(key, value, log=True):
    if log:
        print(f"sending {(key, value)} via http")
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                url, json={"key": key, "value": value}
            ) as response:
                result = await response.text()
                if log:
                    print("response:", result)
        except aiohttp.ClientConnectionError:
            if log:
                print(f"Could not connect to {url}")

async def kafka(key, value, log=True):
    if log:
        print(f"sending {(key, value)} via kafka")
    await fpoc_topic.send(key=KeyModel(i=key), value=ValueModel(**value))


RATE = 1
SENDER = http
SENDERS = {"'h'": http, "'k'": kafka}
EXIT = False
def on_key(key):
    global EXIT, RATE, SENDER
    if key == b'\x1b[A':
        RATE *= 10
        print(f"rate = {RATE}")
    elif key == b'\x1b[B':
        RATE /= 10
        print(f"rate = {RATE}")
    elif key == b'q':
        print("exiting by request of user")
        EXIT = True
    else:
        print(key)


async def main():
    xrnd = Rnd(lambda x: int(10*x))
    yrnd = Rnd(lambda y: 100 + int(10*y))
    xcnt = defaultdict(int)
    for i, x, y in ( (i, xrnd(), yrnd()) for i in itertools.count() ):
        if EXIT:
            sys.exit()
        log = not i % RATE
        xcnt[x] += 1
        await SENDER(i, {"x": x, "y": str(y)}, log)
        await asyncio.sleep(1.0/RATE if RATE < 10000 else 0)
        if log:
            print(json.dumps(OrderedDict(sorted(xcnt.items())), indent=2))
    

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    try:
        pipe_transport = loop.connect_read_pipe(
            get_term_reader_protocol(on_key), sys.stdin
        )
        loop.run_until_complete(pipe_transport)
        loop.run_until_complete(main())
    finally:
        loop.close()
