try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

from nanoweb import Nanoweb
from mylogger import Logger


async def serve_client(reader, writer):
    print("Client connected")
    request_line = await reader.readline()
    print("Request:", request_line)
    # We are not interested in HTTP request headers, skip them
    while await reader.readline() != b"\r\n":
        pass

    request = str(request_line)

    logger = Logger.get_logger()
    logger.info('Showing logs')
    logs = '<br/>'.join([_ for _ in logger.get_last_records()])

    response = f'foo<br/>{logs}'
    writer.write(f'HTTP/1.0 200 OK\r\nContent-type: text/html\r\nContent-Length: {len(response)}\r\n\r\n')
    writer.write(response)

    await writer.drain()
    await writer.wait_closed()
    print("Client disconnected")


def start_simple_web(start_loop=False):
    asyncio.create_task(asyncio.start_server(serve_client, "0.0.0.0", 5050))
    if start_loop:
        loop = asyncio.get_event_loop()
        loop.run_forever()


async def api_status(request):
    """API status endpoint"""
    await request.write("""HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\r\n{"status": "running"}""".encode())


async def logs(request):
    """Return errors"""
    logger = Logger.get_logger()
    logger.info('Showing logs')
    logs = '<br/>'.join([_ for _ in logger.get_last_records()])
    await request.write(f"""HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n{logs}""".encode())

# naw = Nanoweb(port=5050)
#
# naw.routes = {
#     '/status': api_status,
#     '/logs': logs
# }
