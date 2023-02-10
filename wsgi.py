import sys

# sys.path.insert(0, 'F:\html_windows') #第二个参数为项目路径
sys.path.insert(0, 'D:\html_windows') #第二个参数为项目路径

from main import app as application # wsgi只认这个application
