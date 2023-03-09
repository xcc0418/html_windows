from tornado.httpserver import HTTPServer
from tornado.wsgi import WSGIContainer
from main import app
from tornado.ioloop import IOLoop
# import ctypes

# kernel32 = ctypes.windll.kernel32
# kernel32.SetConsoleMode(kernel32.GetStdHandle(-10), 128)

s = HTTPServer(WSGIContainer(app))
s.listen(80)  # 监听2021端口
IOLoop.current().start()
