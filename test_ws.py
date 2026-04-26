# test_ws.py
import asyncio
import websockets
import json

async def hello():
    uri = "ws://localhost:8000/ws/stream"
    async with websockets.connect(uri) as websocket:
        await websocket.send(json.dumps({"track": [25544]}))
        while True:
            response = await websocket.recv()
            print(response)

asyncio.run(hello())