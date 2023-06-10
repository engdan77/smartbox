from nanoweb import Nanoweb


async def api_status(request):
    """API status endpoint"""
    await request.write("""HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\r\n{"status": "running"}""".encode())

naw = Nanoweb(port=5050)

naw.routes = {
    '/api/status': api_status,
}
