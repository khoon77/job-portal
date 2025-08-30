"""
로컬 테스트 서버
CORS 헤더를 포함한 간단한 HTTP 서버
"""
from http.server import HTTPServer, SimpleHTTPRequestHandler
import os

class CORSRequestHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

def run_server(port=8080):
    os.chdir(r'C:\Users\hoon7\PycharmProjects\NewJobPortal')
    server_address = ('', port)
    httpd = HTTPServer(server_address, CORSRequestHandler)
    print(f'서버 시작: http://localhost:{port}')
    print(f'접속 URL: http://localhost:{port}/index_v1-1.html')
    print('종료하려면 Ctrl+C를 누르세요.')
    httpd.serve_forever()

if __name__ == '__main__':
    run_server()