import openpyxl
import pymysql
import requests
import json
import datetime
import os


class Quantity():
    def __init__(self):
        self.s = requests.Session()
        login_url = 'https://erp.lingxing.com/api/passport/login'
        # 请求头
        headers = {'Host': 'erp.lingxing.com',
                   'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:95.0) Gecko/20100101 Firefox/95.0'
            , 'Referer': 'https://erp.lingxing.com/login',
                   'Accept': 'application/json, text/plain, */*',
                   'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
                   'Accept-Encoding': 'gzip, deflate, br',
                   'Content-Type': 'application/json;charset=utf-8',
                   'X-AK-Request-Id': 'e7f7b81a-fafd-4031-8964-00376ae24d07',
                   'X-AK-Company-Id': '90136229927150080',
                   'X-AK-Request-Source': 'erp',
                   'X-AK-ENV-KEY': 'SAAS-10',
                   'X-AK-Version': '1.0.0.0.0.023',
                   'X-AK-Zid': '109810',
                   'Content-Length': '114',
                   'Origin': 'https://erp.lingxing.com',
                   'Connection': 'keep-alive'}
        # 传递用户名和密码
        data = {'account': 'IT-Test', 'pwd': 'IT-Test'}
        data = json.dumps(data)
        self.s.post(login_url, headers=headers, data=data)
        self.auth_token = None

    def sql(self):
        self.connection = pymysql.connect(host='3354n8l084.goho.co',  # 数据库地址
                                          port=24824,
                                          user='test_user',  # 数据库用户名
                                          password='a123456',  # 数据库密码
                                          db='storage',  # 数据库名称
                                          charset='utf8',
                                          cursorclass=pymysql.cursors.DictCursor)
        # 使用 cursor() 方法创建一个游标对象 cursor
        self.cursor = self.connection.cursor()

    def sql_close(self):
        self.cursor.close()
        self.connection.close()

    def change_file_name(self, path, change_name, time_now):
        os.rename(path, f'F:/html_windows/static/测试文件/{change_name}_{time_now}.xlsx')
        return f'../../../static/测试文件/{change_name}_{time_now}.xlsx', f'{change_name}_{time_now}.xlsx', f'{change_name}_{time_now}'

    def python_create_table(self):
        str_table = ''
        for i in range(1, 11):
            table_id = f"tr_control{i}"
            str_th = '<th class="th_control" ><div class="header_text"><div class="header_text"><span>后端生成</span></div></th>'
            str_tr = f'<tr class="tr_control" id="{table_id}">{str_th}{str_th}{str_th}</tr>'
            str_table += str_tr
        return str_table

