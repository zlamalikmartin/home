import aiohttp
from aiohttp import web, WSCloseCode
import asyncio
import sys
import ssl

connected_clients = set()
messages = []

async def http_handler(request):
    #return web.Response(text='Hello, world')
    return web.FileResponse('web/index.html')

async def websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    connected_clients.add(ws)
    print("Client " + str(request.remote) + " registered");

    for data in messages:
        await ws.send_str(data)

    async for msg in ws:
        if msg.type == aiohttp.WSMsgType.TEXT:
            if msg.data == 'close':
                await ws.close()
            else:
                messages.append(msg.data)
                for wsclient in connected_clients:
                    await wsclient.send_str(msg.data)
        elif msg.type == aiohttp.WSMsgType.ERROR:
            print('ws connection closed with exception %s' % ws.exception())
    
    connected_clients.remove(ws)
    print("Client " + str(request.remote) + " unregistered");

    return ws


def create_runner():
    app = web.Application()
    app.add_routes([
        web.get('/',   http_handler),
        web.get('/ws', websocket_handler),
    ])
    return web.AppRunner(app)


async def start_server(host, port):
    runner = create_runner()
    await runner.setup()
    site = web.TCPSite(runner, host, port)
    await site.start()


def main():
    port = 55555
    hostname = "localhost"
    if len(sys.argv) > 1:
        hostname = sys.argv[1]
    print("Server starting on " + hostname + ":" + str(port))

    loop = asyncio.get_event_loop()
    loop.run_until_complete(start_server(host=hostname, port=port))
    loop.run_forever()

if __name__ == "__main__":
    main()