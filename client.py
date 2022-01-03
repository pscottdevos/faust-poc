#! /usr/bin/env python3
import asyncio
import atexit
import itertools
import json
import random
import sys
from collections import defaultdict, OrderedDict
from time import time

import aiohttp
import faust
import uvloop
from pynput.keyboard import Key, Listener

from server import KeyModel, ValueModel
from protocols.term import get_term_reader_protocol
from utils.fastrnd import FastRnd


asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())


app = faust.App('faust_poc_client', broker='kafka://', store='memory://')

fpoc_topic = app.topic("fpoc-v2",
    key_type=KeyModel,
    key_serializer="json",
    value_type=ValueModel,
    partitions=5,
)


url = "http://localhost:6066/sums"
async def http(key, value, log=True):
    if log:
        print(f"sample http request from batch: {(key, value)}")
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
        print(f"sample kafka message from batch: {(key, value)}")
    await fpoc_topic.send(key=KeyModel(i=key), value=ValueModel(**value))


RATE = 1
SENDER = http
SENDERS = {b'h': http, b'k': kafka}
EXIT = False
def on_key(key):
    global EXIT, RATE, SENDER
    if key == b'\x1b[A':
        RATE *= 10
        print(f"rate = {RATE}")
    elif key == b'\x1b[B':
        RATE /= 10
        print(f"rate = {RATE}")
    elif key in (b'q', b'\x03'):
        print("exiting by request of user")
        EXIT = True
    elif key in (b'h', b'k'):
        SENDER = SENDERS[key]
    else:
        print(key)


async def main():
    xrnd = FastRnd(lambda x: int(10*x))
    yrnd = FastRnd(lambda y: 100 + int(10*y))
    rcnt = defaultdict(int)
    batch_start_time = time()
    for i, x, y in ( (i, xrnd(), yrnd()) for i in itertools.count() ):
        if EXIT:
            sys.exit()
        eob = not i % RATE # end of batch
        rcnt[y] += 1
        await SENDER(i, {"x": x, "y": str(y)}, eob)
        if RATE < 10000:
            await asyncio.sleep(1.0/RATE)
        if eob:
            current_time = time()
            rps = round(RATE / (current_time - batch_start_time), 2)
            print(f"requests per second {rps}")
            log_str = json.dumps(
                {"cumulative requests per key": OrderedDict(sorted(rcnt.items()))},
                indent=2,
            )
            print(log_str)
            print('=============================\n')
            batch_start_time = current_time 

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
