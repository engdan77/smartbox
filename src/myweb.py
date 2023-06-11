from nanoweb import Nanoweb
from mylogger import Logger


async def api_status(request):
    """API status endpoint"""
    await request.write("""HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\r\n{"status": "running"}""".encode())

async def logs(request):
    """Return errors"""
    logger = Logger.get_logger()
    logs = '<br/>'.join([_ for _ in logger.get_last_records()])
    await request.write(f"""HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n{logs}""".encode())

naw = Nanoweb(port=5050)

naw.routes = {
    '/status': api_status,
    '/logs': logs
}
