try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

from mylogger import Logger
import sys


def socket_write(writer, data):
    if 'esp' not in sys.platform:
        data = data.encode()
    writer.write(data)


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
    socket_write(writer, f'HTTP/1.0 200 OK\r\nContent-type: text/html\r\nContent-Length: {len(response)}\r\n\r\n')
    socket_write(writer, response)

    await writer.drain()
    await writer.wait_closed()
    print("Client disconnected")


def start_simple_web(start_loop=False):
    asyncio.create_task(asyncio.start_server(serve_client, "0.0.0.0", 5050))
    if start_loop:
        loop = asyncio.get_event_loop()
        loop.run_forever()
