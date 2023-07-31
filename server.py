from tornado.httpserver import HTTPServer
from tornado.wsgi import WSGIContainer
from main import app
from tornado.ioloop import IOLoop
import ctypes

# 取消CMD窗口快速编辑模式
kernel32 = ctypes.windll.kernel32
kernel32.SetConsoleMode(kernel32.GetStdHandle(-10), 128)

s1 = HTTPServer(WSGIContainer(app))
s1.listen(80)  # 监听80端口
# s1 = HTTPServer(WSGIContainer(app))
# s1.listen(8081)  # 监听80端口
# s2 = HTTPServer(WSGIContainer(app))
# s2.listen(8082)  # 监听80端口
# s3 = HTTPServer(WSGIContainer(app))
# s3.listen(8083)  # 监听80端口s1 = HTTPServer(WSGIContainer(app))
# s4 = HTTPServer(WSGIContainer(app))
# s4.listen(8084)  # 监听80端口
IOLoop.current().start()
