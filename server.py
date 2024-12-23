import http.server
import socketserver
import json
import urllib.parse
import dzbrowse
import mimetypes
import signal
import sys
import tags

class CustomRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        # Initialize the MIME types
        mimetypes.init()
        # Add CSS MIME type if not present
        if '.css' not in mimetypes.types_map:
            mimetypes.types_map['.css'] = 'text/css'
        super().__init__(*args, **kwargs)

    data_keys, data_content = dzbrowse.open_data_files("data_keys", "data_contents")
    # Dictionary to store our routes
    routes = {
        '/': lambda self: self.send_home_page(),
        '/hello': lambda self: self.send_hello_world(),
        '/api/users': lambda self: self.send_users_data(),
        '/style.css': lambda self: self.load_css(),
        '/tag': lambda self: self.load_tag(),
    }

    def load_tag(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        parts = self.path.split("/")
        self.wfile.write("TODO: write tags")

    def load_css(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/css')
        self.end_headers()
        with open("style.css") as fp:
            self.wfile.write(fp.read().encode())

    def do_GET(self):
        # Parse the URL to handle query parameters if needed
        parsed_path = urllib.parse.urlparse(self.path)

        path_segments = parsed_path.path.split("/")
      
        if len(path_segments) > 1 and path_segments[1] == "dz":
            dzpath = "/" + "/".join(path_segments[2:])
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            html = dzbrowse.generate_page(dzpath, self.data_keys, self.data_content)
            self.wfile.write(html.encode())
        elif parsed_path.path in self.routes:
            # Call the corresponding route handler
            self.routes[parsed_path.path](self)
        else:
            # Default 404 Not Found response
            self.send_error(404, "Page not found")

    def send_home_page(self):
        """Handle requests to the home page"""
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        
        html = """
        <!DOCTYPE html>
        <html>
        <head><title>Custom Python HTTP Server</title></head>
        <body>
            <h1>Welcome to the Custom Python HTTP Server</h1>
            <p>Available routes:</p>
            <ul>
                <li>/hello - Get a greeting</li>
                <li>/api/users - Get user data</li>
            </ul>
        </body>
        </html>
        """
        self.wfile.write(html.encode())

    def send_hello_world(self):
        """Handle requests to /hello"""
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b"Hello, World!")

    def send_users_data(self):
        """Handle requests to /api/users"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        # Sample user data
        users = [
            {"id": 1, "name": "Alice", "email": "alice@example.com"},
            {"id": 2, "name": "Bob", "email": "bob@example.com"},
            {"id": 3, "name": "Charlie", "email": "charlie@example.com"}
        ]
        
        # Convert to JSON and send
        self.wfile.write(json.dumps(users).encode())

    def do_POST(self):
        """Handle POST requests"""
        # For this example, we'll add a simple /api/submit route
        if self.path == '/api/submit':
            # Get the content length
            content_length = int(self.headers['Content-Length'])
            
            # Read the POST data
            post_data = self.rfile.read(content_length)
            
            # Send a response
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            # Echo back the received data
            response = {
                "status": "success", 
                "received_data": post_data.decode('utf-8')
            }
            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_error(404, "Endpoint not found")
    def shut_down(self):
        self._server.shutdown()


def run_server(port=8000):
    def signal_handler(signal, frame):
        nonlocal running
        print('You pressed Ctrl+C!')
        running = False

    # signal.signal(signal.SIGINT, signal_handler)

    running = True
    """Start the server"""
    with socketserver.TCPServer(("", port), CustomRequestHandler) as httpd:
        print(f"Serving at port {port}")
        print(f"Open http://localhost:{port} in your web browser")
        httpd.serve_forever()
        # while running:
        #     print(running)
        #     httpd.handle_request()
        # print("bye")
        # httpd.server_close()

if __name__ == "__main__":
    run_server()
