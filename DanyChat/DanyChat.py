import aiohttp
from aiohttp import web, WSCloseCode
import asyncio
import tempfile
from datetime import datetime
import sys
import ssl

httphostname = "localhost"
wshostname = "localhost"
port = int(443)

connected_clients = set()
messages = []

async def http_handler(request):
    #return web.Response(text='Hello, world')
    #return web.FileResponse('web/index.html')
    now = datetime.today().strftime('%Y-%m-%d %H:%M:%S')
    with open("web/index.html", "rt") as fin:
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as fout:
        #with open("run/index.html", "wt") as fout:
            for line in fin:
                line = line.replace('localhost', wshostname)
                line = line.replace('443', str(port))
                line = line.replace('NOW', now)
                fout.write(line)
            return web.FileResponse(fout.name, headers={'Content-Type': 'text/html'})
    return web.Response(text='File not found', status = 404)
    
# https://stackoverflow.com/questions/53689602/python-3-websockets-server-http-server-run-forever-serve-forever
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
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ssl_cert = "cert/certificate.crt"
    ssl_key = "cert/private.key"
    ssl_context.load_cert_chain(ssl_cert, keyfile=ssl_key)

    # https://stackoverflow.com/questions/77937445/how-to-setup-an-aiohttp-server-using-mtls-self-signed-ssl-ca-certificates
    runner = create_runner()
    await runner.setup()
    site = web.TCPSite(runner, host, port, ssl_context=ssl_context)
    await site.start()


def main():
    global httphostname, wshostname, port
    if len(sys.argv) > 1:
        httphostname = sys.argv[1]
    if len(sys.argv) > 2:
        wshostname = sys.argv[2]
    if len(sys.argv) > 3:
        port = int(sys.argv[3])
    print("Server starting [http:" + httphostname + " ws:" + wshostname + " port:" + str(port) + "]")

    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(start_server(host=httphostname, port=port))
        loop.run_forever()
    except KeyboardInterrupt:
        pass

    print("Server shutting down")

if __name__ == "__main__":
    main()