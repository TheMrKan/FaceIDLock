from http.server import BaseHTTPRequestHandler
from http.server import HTTPServer
import json

sentUpdated = False
json_response = '''{"result":"ok", "clients":"[{\\"action\\": \\"delete\\", \\"user_id\\": 12, \\"encoding\\": [-0.06188490241765976], \\"fio\\": \\"2 1\\"}]"}'''
json_response = json_response.replace(", ", ",").replace(": ", ":")
clients = json.dumps([{"action": "delete", "user_id": 18, "encoding": [-0.06188490241765976], "fio": "2 1"}])
data = {"result": "ok", "clients": clients}
#print(json.dumps(data))
print(json_response)
#print(json.loads(json_response))


class HttpGetHandler(BaseHTTPRequestHandler):
    """Обработчик с реализованным методом do_GET."""

    def do_GET(self):
        global sentUpdated
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json_response.encode())


def run(server_class=HTTPServer, handler_class=BaseHTTPRequestHandler):
    server_address = ('', 8000)
    httpd = server_class(server_address, handler_class)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        httpd.server_close()


if __name__ == "__main__":
    run(handler_class=HttpGetHandler)