from http.server import SimpleHTTPRequestHandler
import socketserver
import os

PORT = int(os.environ.get("PORT", 8080))
DIRECTORY = os.path.join(os.path.dirname(__file__), "site")


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)


with socketserver.TCPServer(("0.0.0.0", PORT), Handler) as httpd:
    print(f"Serving on port {PORT}")
    httpd.serve_forever()
