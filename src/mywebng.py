try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

import sys
import entrymainng
from mylogger import Logger

logger = Logger.get_logger()


def socket_write(writer, data, content_type='text/html'):
    logger.info(f'HTTP sending {data}')
    headers = f'HTTP/1.0 200 OK\r\nContent-type: {content_type}\r\nContent-Length: {len(data)}\r\n\r\n'
    data = headers + data
    if 'esp' not in sys.platform:
        data = data.encode()
    writer.write(data)


async def serve_client(reader, writer):
    logger.info("Client connected")
    request_line = await reader.readline()
    logger.info(f"HTTP REQUEST: {request_line}")
    # We are not interested in HTTP request headers, skip them
    while await reader.readline() != b"\r\n":
        pass

    request = str(request_line)

    o = entrymainng.app_objects["controller"]
    if 'json' in request:
        response = f'{{"temp": {o.temp.read_temp()}, "humidity": {o.temp.read_humid()}, "smoke": {o.smoke.read_smoke()}, "motion": {o.motion.read_motion()}}}'
        socket_write(writer, response, 'application/json')
    else:
        response = f'''<p><span style="font-size:16px"><strong>Daniels smarta box</strong></span></p>
<p>Temperatur: {o.temp.read_temp()} &deg;C<br />
Fuktighet: {o.temp.read_humid()} %<br />
R&ouml;k: {o.smoke.read_smoke()} %<br />
R&ouml;relse: {o.motion.read_motion()}</p>'''
        socket_write(writer, response)

    await writer.drain()
    await writer.wait_closed()
    logger.info("Client disconnected")


def start_simple_web(start_loop=False):
    asyncio.create_task(asyncio.start_server(serve_client, "0.0.0.0", 80))
    if start_loop:
        loop = asyncio.get_event_loop()
        loop.run_forever()
