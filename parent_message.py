import openpyxl
import requests
import pymysql
import json
# import datetime
import hashlib
import urllib
import base64
from Crypto.Cipher import AES
import zipfile
import time
import os
from datetime import datetime
import pandas as pd


class EncryptDate:
    def __init__(self, key):
        self.key = key.encode("utf-8")  # 初始化密钥
        self.length = AES.block_size  # 初始化数据块大小
        self.aes = AES.new(self.key, AES.MODE_ECB)  # 初始化AES,ECB模式的实例
        # 截断函数，去除填充的字符
        self.unpad = lambda date: date[0:-ord(date[-1])]

    def pad(self, text):
        """
        #填充函数，使被加密数据的字节码长度是block_size的整数倍
        """
        count = len(text.encode('utf-8'))
        add = self.length - (count % self.length)
        entext = text + (chr(add) * add)
        return entext

    def encrypt(self, encrData):  # 加密函数
        res = self.aes.encrypt(self.pad(encrData).encode("utf8"))
        msg = str(base64.b64encode(res), encoding="utf8")
        return msg

    def decrypt(self, decrData):  # 解密函数
        res = base64.decodebytes(decrData.encode("utf8"))
        msg = self.aes.decrypt(res).decode("utf8")
        return self.unpad(msg)


class Quantity(object):
    def __init__(self):
        self.app_id = "ak_nEfE94OSogf3x"
        app_secret = "g2BcerjK4fWmhGZoetCJHeVqJmHEmfLt3gWFjDrBLB1yxiapgUKH6kOVs2N9JH7SFuBKuOF8K/CrNNSeFO1KKtsL05z24j" \
                     "+AdWTW+V4op5QxDkmlTllvlprT8FfjctDdNDGrwHvBvE6s9h0pO0dNgopBAYiA7oosPzQhDF1A6XC1X/cZZmgBy3XRHyEv" \
                     "xTT40xzwVGish53R8dZt3YIxNtKSgrBloo/CRQsV01yU40nyQR9L9oML32VT0C16jBrxcoWthlGDwfBn+CtVUvws4imyZi" \
                     "+sG/CqZQeaVLkBCqLCgqw1VK4/a4jZws6HO3FMeBgvuf0aS5euNmfhkudQmg=="
        querystring = {"appId": f"{self.app_id}", "appSecret": f"{app_secret}"}
        url = "https://openapi.lingxing.com/api/auth-server/oauth/access-token"
        payload = ""
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
        response = requests.post(url, data=payload, headers=headers, params=querystring)
        result = json.loads(response.text)
        self.access_token = result['data']['access_token']
        self.refresh_token = result['data']['refresh_token']
        self.time = datetime.now().strftime("%Y-%m-%d")
        self.time = datetime.strptime(self.time, "%Y-%m-%d")
        # self.time = "2021-12-06"
        self.start_time = self.time
        self.time = self.time.strftime("%Y-%m-%d")
        self.start_time = self.start_time.strftime("%Y-%m-%d")
        # self.start_time = '2022-03-07'

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

    def get_sign(self, body):
        apikey = "ak_nEfE94OSogf3x"

        # 目标md5串
        str_parm = ''
        # 将字典中的key排序
        for p in sorted (body):
            # 每次排完序的加到串中
            # if body[p]:
            # str类型需要转化为url编码格式
            if isinstance(body[p], str):
                str_parm = str_parm + str(p) + "=" + str(urllib.parse.quote (body[p])) + "&"
                continue
            str_value = str (body[p])
            str_value = str_value.replace(" ", "")
            # str_value = str_value.replace("?", " ")
            str_value = str_value.replace("'", "\"")
            str_parm = str_parm + str(p) + "=" + str_value + "&"
        # 加上对应的key
        str_parm = str_parm.rstrip('&')
        str_parm = str_parm.replace("?", " ")
        if isinstance (str_parm, str):
            # 如果是unicode先转utf-8
            parmStr = str_parm.encode ("utf-8")
            # parmStr = str_parm
            m = hashlib.md5 ()
            m.update (parmStr)
            md5_sign = m.hexdigest ()
            # print(m.hexdigest())
            md5_sign = md5_sign.upper ()
            # print("MD5加密:", md5_sign)
        eg = EncryptDate (apikey)  # 这里密钥的长度必须是16的倍数
        res = eg.encrypt (md5_sign)
        # print("AES加密:", res)
        # print(eg.decrypt(res))
        return res

    def get_list_male(self, parent=None):
        self.sql()
        if parent:
            sql = f"select * from `amazon_form`.`list_parent` where `本地父体` like '%{parent}%'"
        else:
            sql = "select * from `amazon_form`.`list_parent`"
        self.cursor.execute(sql)
        result = self.cursor.fetchall()
        if result:
            list_msg = []
            for i in result:
                list_msg.append(i['本地父体'])
            return list_msg
        else:
            return False

    def download_asin(self):
        self.sql()
        sql = "select * from `flag`.`amazon_form_flag` where `flag_name` = 'downloads'"
        self.cursor.execute(sql)
        result = self.cursor.fetchall()
        self.sql_close()
        if result[0]['flag_num'] == 0:
            try:
                self.open_downloads()
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
                auth_token = self.s.cookies.get('auth-token')
                auth_token = auth_token.replace('%25', '%')
                auth_token = auth_token.replace('%23', '#')
                auth_token = auth_token.replace('%26', '&')
                auth_token = auth_token.replace('%2B', '+')
                auth_token = auth_token.replace('%28', '(')
                auth_token = auth_token.replace('%29', ')')
                auth_token = auth_token.replace('%2F', '/')
                auth_token = auth_token.replace('%3D', '=')
                auth_token = auth_token.replace('%3F', '?')
                msg1, report = self.download1(auth_token)
                if msg1:
                    msg2 = self.download2(auth_token)
                    if msg2:
                        self.write_asin(report)
                        self.write_order()
                        self.close_downloads()
                    else:
                        self.close_downloads()
                else:
                    self.close_downloads()
            except Exception as e:
                self.close_downloads()
                print(e)
        else:
            self.close_downloads()
            return False

    def open_downloads(self):
        self.sql()
        sql = "update `flag`.`amazon_form_flag` set `flag_num` = 1 where `flag_name` = 'downloads'"
        self.cursor.execute(sql)
        self.connection.commit()
        self.sql_close()

    def close_downloads(self):
        self.sql()
        sql = "update `flag`.`amazon_form_flag` set `flag_num` = 0 where `flag_name` = 'downloads'"
        self.cursor.execute(sql)
        self.connection.commit()
        self.sql_close()

    def download1(self, auth_token):
        try:
            url = "https://gw.lingxingerp.com/listing-api/api/product/exportOnline"
            headers = {'Host': 'gw.lingxingerp.com',
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:95.0) Gecko/20100101 Firefox/95.0'
                        , 'Referer': 'https://erp.lingxing.com',
                       'auth-token': auth_token,
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
                        'Content-Length': '909',
                        'Origin': 'https://erp.lingxing.com',
                        'Connection': 'keep-alive'}
            data = {"offset": 0, "length": 50, "search_field": "local_sku", "exact_search": 1, "sids": "", "status": "",
                    "is_pair": "", "fulfillment_channel_type": "", "global_tag_ids": "",
                    "req_time_sequence": "/listing-api/api/product/exportOnline$$2"}
            data = json.dumps(data)
            post_msg = self.s.post(url, headers=headers, data=data)
            post_msg = json.loads(post_msg.text)
            print(post_msg)
            if post_msg['code'] == 1 and post_msg['msg'] == "成功":
                report_id = post_msg['data']['data']['report_id']
                time.sleep(300)
                if report_id:
                    file_download_url = f"https://erp.lingxing.com/api/download/downloadCenterReport/downloadResource?report_id={report_id}"
                    # print(file_download_url)
                    get_headers = {'user-agent': 'Mozilla/5.0', 'Referer': 'https://erp.lingxing.com/erp/muser/downloadCenter'}
                    download_file = self.s.get(file_download_url, headers=get_headers, stream=False)
                    with open('D:/listing/listing.zip', 'wb') as q:
                        q.write(download_file.content)
                    return True, report_id
                else:
                    return False, False
            else:
                return False, False
        except Exception as e:
            print(e)
            return False, False

    def download2(self, auth_token):
        try:
            url = "https://erp.lingxing.com/api/storage/export"
            headers = {'Host': 'erp.lingxing.com',
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:95.0) Gecko/20100101 Firefox/95.0'
                        , 'Referer': 'https://erp.lingxing.com/erp/muser/downloadCenter',
                       'auth-token': auth_token,
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
                        'Content-Length': '909',
                        'Origin': 'https://erp.lingxing.com',
                        'Connection': 'keep-alive'}
            data = {"wid_list": "", "mid_list": "", "sid_list": "", "cid_list": "", "bid_list": "",
                    "principal_list": "", "product_type_list": "", "product_attribute": "", "product_status": "",
                    "search_field": "sku", "search_value": "", "is_sku_merge_show": 0, "is_hide_zero_stock": 0,
                    "offset": 0, "length": 200, "sort_field": "", "sort_type": "", "gtag_ids": "",
                    "senior_search_list": "[]", "req_time_sequence": "/api/storage/export$$3"}
            data = json.dumps(data)
            post_msg = self.s.post(url, headers=headers, data=data)
            post_msg = json.loads(post_msg.text)
            print(post_msg)
            if post_msg['code'] == 1 and post_msg['msg'] == "操作成功":
                get_url = "https://erp.lingxing.com/api/download/downloadCenterReport/getReportData?offset=0&length=100" \
                          "&report_time_type=0&req_time_sequence=/api/download/downloadCenterReport/getReportData$$"
                get_headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:95.0) Gecko/20100101 Firefox/95.0'
                               , 'Referer': 'https://erp.lingxing.com/erp/msupply/warehouseDetail',}
                time.sleep(100)
                report_id = ''
                get_msg = self.s.get(get_url, headers=get_headers)
                get_msg = json.loads(get_msg.text)
                print(get_msg['data']['list'][0])
                if get_msg['data']['list'][0]['report_name'].find('库存明细_仓库库存') >= 0:
                    report_id = get_msg['data']['list'][0]['report_id']
                if report_id:
                    file_download_url = f"https://erp.lingxing.com/api/download/downloadCenterReport/downloadResource?report_id={report_id}"
                    # print(file_download_url)
                    get_headers = {'user-agent': 'Mozilla/5.0', 'Referer': 'https://erp.lingxing.com/erp/muser/downloadCenter'}
                    download_file = self.s.get(file_download_url, headers=get_headers, stream=False)
                    with open('D:/listing/库存明细_仓库库存.xlsx', 'wb') as q:
                        q.write(download_file.content)
                    return True
                else:
                    return False
            else:
                return False
        except Exception as e:
            print(e)
            return False

    def write_asin(self, report):
        file = zipfile.ZipFile('D:/listing/listing.zip')
        file.extractall('D:/listing/')
        file.close()
        time_data = datetime.now().strftime("%Y%m%d")
        filename = f"D:/listing/listing{time_data}-{report}.xlsx"
        dict_asin = {}
        dict_sku = {}
        dict_asin_son = {}
        wb = openpyxl.load_workbook(filename)
        wb_sheet = wb.active
        max_row = wb_sheet.max_row
        for i in range(2, max_row+1):
            asin = wb_sheet.cell(row=i, column=6).value
            sku = wb_sheet.cell(row=i, column=10).value
            if asin and sku:
                asin_son = wb_sheet.cell(row=i, column=5).value
                country = wb_sheet.cell(row=i, column=2).value
                fnsku = wb_sheet.cell(row=i, column=8).value
                fba_order1 = int(wb_sheet.cell(row=i, column=19).value)
                fba_order2 = int(wb_sheet.cell(row=i, column=20).value)
                fba_order3 = int(wb_sheet.cell(row=i, column=21).value)
                fba_order4 = int(wb_sheet.cell(row=i, column=23).value)
                fba_order = fba_order3 + fba_order2 + fba_order1
                sale_num = int(wb_sheet.cell(row=i, column=31).value)
                if asin in dict_asin:
                    if sku in dict_asin[asin]:
                        dict_asin[asin][sku].append([fnsku, fba_order, fba_order4, sale_num, country])
                    else:
                        dict_asin[asin][sku] = [[fnsku, fba_order, fba_order4, sale_num, country]]
                else:
                    dict_asin[asin] = {sku: [[fnsku, fba_order, fba_order4, sale_num, country]]}
                if sku in dict_sku:
                    dict_sku[sku].append([fnsku, fba_order, fba_order4, sale_num, country])
                else:
                    dict_sku[sku] = [[fnsku, fba_order, fba_order4, sale_num, country]]
                if asin in dict_asin_son:
                    if asin_son not in dict_asin_son[asin]:
                        dict_asin_son[asin].append(asin_son)
                else:
                    dict_asin_son[asin] = [asin_son]
        str_json = json.dumps(dict_asin)
        sku_json = json.dumps(dict_sku)
        asin_son_json = json.dumps(dict_asin_son)
        f1 = open('asin_info.json', 'w')
        f1.write(str_json)
        f2 = open('sku_info.json', 'w')
        f2.write(sku_json)
        f3 = open('asin_son_info.json', 'w')
        f3.write(asin_son_json)
        self.read_json(asin_son_json)

    def write_order(self):
        filename = f"D:/listing/库存明细_仓库库存.xlsx"
        dict_order = {}
        dict_fnsku = {}
        wb = openpyxl.load_workbook(filename)
        wb_sheet = wb.active
        max_row = wb_sheet.max_row
        for i in range(2, max_row+1):
            sku = wb_sheet.cell(row=i, column=2).value
            if sku:
                fnsku = wb_sheet.cell(row=i, column=5).value
                num = int(wb_sheet.cell(row=i, column=35).value)
                predict_num = int(wb_sheet.cell(row=i, column=36).value)
                country = wb_sheet.cell(row=i, column=7).value
                if fnsku:
                    if sku in dict_order:
                        if country in dict_order[sku]:
                            dict_order[sku][country][0] += num
                            dict_order[sku][country][1] += predict_num
                        else:
                            dict_order[sku][country] = [num, predict_num]
                    else:
                        dict_order[sku] = {country: [num, predict_num]}
                    if sku in dict_fnsku:
                        if fnsku in dict_fnsku[sku]:
                            flag = 1
                            for j in range(0, len(dict_fnsku[sku][fnsku])):
                                if dict_fnsku[sku][fnsku][j][2] == country:
                                    dict_fnsku[sku][fnsku][j][0] += num
                                    dict_fnsku[sku][fnsku][j][1] += predict_num
                                    flag = 0
                            if flag:
                                dict_fnsku[sku][fnsku].append([num, predict_num, country])
                        else:
                            dict_fnsku[sku][fnsku] = [[num, predict_num, country]]
                    else:
                        dict_fnsku[sku] = {fnsku: [[num, predict_num, country]]}
        fnsku_json = json.dumps(dict_fnsku)
        str_json = json.dumps(dict_order)
        f1 = open('order_info.json', 'w')
        f1.write(str_json)
        f2 = open('fnsku_info.json', 'w')
        f2.write(fnsku_json)

    def read_json(self, asin_son_json):
        time_now = datetime.now().strftime('%Y%m%d%H%M%S')
        f = open(f"./static/父ASIN详情/asin_son_info-{time_now}.json", 'w')
        f.write(asin_son_json)
        filename = "./static/父ASIN详情"
        list_file = os.listdir(filename)
        filelist = []
        for i in range(0, len(list_file)):
            path = os.path.join(filename, list_file[i])
            if os.path.isfile(path):
                filelist.append(list_file[i])
        time_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        time_now = datetime.strptime(time_now, "%Y-%m-%d %H:%M:%S")
        for i in range(0, len(filelist)):
            path = os.path.join(filename, filelist[i])
            print(path)
            if os.path.isdir(path):
                continue
            timestamp = os.path.getmtime(path)
            date = datetime.fromtimestamp(timestamp)
            flie_time = date.strftime('%Y-%m-%d %H:%M:%S')
            flie_time = datetime.strptime(flie_time, "%Y-%m-%d %H:%M:%S")
            file_day = (time_now - flie_time).days
            if file_day >= 30:
                os.remove(path)

    def read_excl(self, asin_parent=None):
        # file = zipfile.ZipFile('D:/listing/listing.zip')
        # file.extractall('D:/listing/')
        # file.close()
        # filename = f"D:/listing/listing.xlsx"
        # mtime = os.path.getmtime(filename)  # 修改时间
        # mtime_string = time.localtime(mtime)
        # time_create = time.strftime("%Y-%m-%d %H:%M:%S", mtime_string)
        # time_create = datetime.strptime(time_create, "%Y-%m-%d %H:%M:%S")
        # time_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # time_now = datetime.strptime(time_now, "%Y-%m-%d %H:%M:%S")
        # seconds = (time_now - time_create).total_seconds()
        seconds = 100
        if int(seconds) <= 3600:
            f = open('asin_info.json', 'r')
            info_data = json.load(f)
            # print(info_data[asin_parent])
            if asin_parent:
                if asin_parent in info_data:
                    return info_data[asin_parent]
                else:
                    return False
            else:
                list_asin = list(info_data.keys())
                return list_asin
        return False

    def get_order(self, dict_asin, country):
        dict_asin_new = {}
        for i in dict_asin:
            dict_asin_new[i] = [0, 0, 0]
            if type(dict_asin[i][0]) is list:
                country = dict_asin[i][0][4]
                for j in dict_asin[i]:
                    dict_asin_new[i][0] += j[1]
                    dict_asin_new[i][1] += j[2]
                    dict_asin_new[i][2] += j[3]
                dict_asin_new[i].append(0)
                dict_asin_new[i].append(0)
                f = open('fnsku_info.json', 'r')
                info_data = json.load(f)
                if i in info_data:
                    for j in info_data[i]:
                        for k in range(0, len(info_data[i][j])):
                            if info_data[i][j][k][2] == country:
                                dict_asin_new[i][3] +=info_data[i][j][k][0]
                                dict_asin_new[i][4] += info_data[i][j][k][1]
            else:
                dict_asin_new[i][0] += dict_asin[i][0]
                dict_asin_new[i][1] += dict_asin[i][1]
                dict_asin_new[i][2] += dict_asin[i][2]
                f = open('order_info.json', 'r')
                info_data = json.load(f)
                if i in info_data and country in info_data[i]:
                    dict_asin_new[i].append(info_data[i][country][0])
                    dict_asin_new[i].append(info_data[i][country][1])
                else:
                    dict_asin_new[i].append(0)
                    dict_asin_new[i].append(0)
        return dict_asin_new

    def read_sku_info(self):
        f = open('sku_info.json', 'r')
        info_data = json.load(f)
        return info_data

    def find_excl(self, asin):
        # asin = "B07KYYSQN6"
        list_asin = []
        dict_asin = self.read_excl(asin)
        if dict_asin:
            # print(dict_asin)
            dict_asin = self.get_order(dict_asin, None)
            # print(dict_asin)
            dict_sku = self.select_male_name(dict_asin)
            # print(dict_sku)
            for i in dict_sku:
                list_asin.append([asin, i, dict_sku[i][0], dict_sku[i][1], dict_sku[i][2], dict_sku[i][3], dict_sku[i][4]])
            # print(list_asin)
            str_json = json.dumps({asin: list_asin})
            f = open(f'./static/列表详情/{asin}_info.json', 'w')
            f.write(str_json)
            return list_asin
        else:
            return False

    def select_male_name(self, dict_sku):
        self.sql()
        dict_sku_new = {}
        for i in dict_sku:
            sql = f"select * from `amazon_form`.`male_sku` where `SKU` = '{i}'"
            self.cursor.execute(sql)
            result = self.cursor.fetchall()
            if result:
                if result[0]['本地品名'] in dict_sku_new:
                    dict_sku_new[result[0]['本地品名']][0] += dict_sku[i][0]
                    dict_sku_new[result[0]['本地品名']][1] += dict_sku[i][1]
                    dict_sku_new[result[0]['本地品名']][2] += dict_sku[i][2]
                    dict_sku_new[result[0]['本地品名']][3] += dict_sku[i][3]
                    dict_sku_new[result[0]['本地品名']][4] += dict_sku[i][4]
                else:
                    dict_sku_new[result[0]['本地品名']] = dict_sku[i]
            else:
                dict_sku_new[i] = dict_sku[i]
        self.sql_close()
        return dict_sku_new

    def find_list_male(self, asin, country):
        self.sql()
        sql = f"select * from `amazon_form`.`male_parent` where `本地父体` like '%{asin}%'"
        # print(sql)
        self.cursor.execute(sql)
        result = self.cursor.fetchall()
        # print(result)
        if result:
            list_sku = []
            dict_data = {}
            dict_sku = self.read_sku_info()
            # print(dict_sku)
            for i in result:
                sku = i['SKU']
                list_num = [0, 0, 0]
                if sku in dict_sku:
                    for j in dict_sku[sku]:
                        if country == j[4]:
                            list_num[0] += j[1]
                            list_num[1] += j[2]
                            list_num[2] += j[3]
                dict_data[sku] = list_num
            dict_data = self.get_order(dict_data, country)
            dict_data = self.select_male_name(dict_data)
            # print(dict_data)
            for i in dict_data:
                list_sku.append([asin, i, dict_data[i][0], dict_data[i][1], dict_data[i][2], dict_data[i][3], dict_data[i][4]])
            # print(list_sku)
            str_json = json.dumps({asin: list_sku})
            f = open(f'./static/列表详情/{asin}_info.json', 'w')
            f.write(str_json)
            return list_sku
        else:
            return False

    def contrast_parent(self, list1, list2):
        dict1 = {}
        dict2 = {}
        list_male = []
        list_asin = []
        for i in list1:
            if i[1]:
                if i[1] == 'SKU':
                    continue
                if i[1] == '0':
                    continue
                dict1[i[1]] = i
        for i in list2:
            if i[1]:
                if i[1] == 'SKU':
                    continue
                if i[1] == '0':
                    continue
                dict2[i[1]] = i
        list_sku = []
        for i in dict1:
            if i in dict2:
                list_male.append([dict2[i][0], dict1[i][1], dict1[i][2], dict1[i][3], dict1[i][4], dict1[i][5], dict1[i][6]])
                list_sku.append(i)
                list_asin.append([dict1[i][0], dict2[i][1], dict2[i][2], dict2[i][3], dict2[i][4], dict2[i][5], dict2[i][6]])
        # print(list_sku)
        # print(list_male)
        for i in dict1:
            if i in list_sku:
                continue
            else:
                list_male.append(dict1[i])
        for i in dict2:
            if i in list_sku:
                continue
            else:
                list_asin.append(dict2[i])
        list_male_new = []
        for i in list_male:
            list_male_new.append([i[0], i[1], i[2], i[3], i[6], i[4], i[5]])
        list_asin_new = []
        for i in list_asin:
            list_asin_new.append([i[0], i[1], i[2], i[3], i[6], i[4], i[5]])
        # print(list_asin_new)
        return list_male_new, list_asin_new

    def windows_msg(self, sku, asin, country):
        if asin.find('B0') >= 0:
            list_sku = self.get_male_sku(sku)
            f1 = open('asin_info.json', 'r')
            str_asin = json.load(f1)
            dict_sku = str_asin[asin]
            f2 = open('fnsku_info.json', 'r')
            dict_order = json.load(f2)
            list_fnsku = []
            for i in list_sku:
                if i in dict_sku and i in dict_order:
                    for j in dict_sku[i]:
                        if j[0] in dict_order[i]:
                            list_warehouse = []
                            for k in dict_order[i][j[0]]:
                                if j[4] == k[2]:
                                    list_warehouse = [i, j[0], j[1], j[2], j[3], k[0], k[1], k[2]]
                            if list_warehouse:
                                list_fnsku.append(list_warehouse)
                            else:
                                list_fnsku.append([i, j[0], j[1], j[2], j[3], 0, 0, j[4]])
                        else:
                            list_fnsku.append([i, j[0], j[1], j[2], j[3], 0, 0, j[4]])
                else:
                    continue
            return list_fnsku
        else:
            list_sku = self.get_male_sku(sku)
            f1 = open('sku_info.json', 'r')
            dict_sku = json.load(f1)
            f2 = open('fnsku_info.json', 'r')
            dict_order = json.load(f2)
            list_fnsku = []
            for i in list_sku:
                if i in dict_sku and i in dict_order:
                    for j in dict_sku[i]:
                        if country == j[4]:
                            if j[0] in dict_order[i]:
                                list_warehouse = []
                                for k in dict_order[i][j[0]]:
                                    if j[4] == k[2]:
                                        list_warehouse = [i, j[0], j[1], j[2], j[3], k[0], k[1], k[2]]
                                if list_warehouse:
                                    list_fnsku.append(list_warehouse)
                                else:
                                    list_fnsku.append([i, j[0], j[1], j[2], j[3], 0, 0, j[4]])
                            else:
                                list_fnsku.append([i, j[0], j[1], j[2], j[3], 0, 0, j[4]])
                else:
                    continue
            return list_fnsku

    def get_male_sku(self, sku):
        list_sku = []
        self.sql()
        sql = f"select * from `amazon_form`.`male_sku` where `本地品名` = '{sku}'"
        self.cursor.execute(sql)
        result = self.cursor.fetchall()
        self.sql_close()
        if result:
            for i in result:
                list_sku.append(i['SKU'])
        else:
            list_sku = [sku]
        return list_sku

    def ascending_sort(self, list1, list2, index, sort_asin):
        list1_pop = []
        if list1:
            list1.pop(0)
            for i in list1:
                if i[0]:
                    if i[1] == '0':
                        continue
                    list1_pop.append(i)
        list2_pop = []
        if list2:
            list2.pop(0)
            for i in list2:
                if i[0]:
                    if i[1] == '0':
                        continue
                    list2_pop.append(i)
        list1_new = []
        list2_new = []
        if sort_asin.find('B0') >= 0:
            if index == 'FBA库存':
                list2_new = sorted(list2_pop, key=lambda d: int(d[2]), reverse=False)
            if index == 'FBA在途':
                list2_new = sorted(list2_pop, key=lambda d: int(d[3]), reverse=False)
            if index == '本地库存':
                list2_new = sorted(list2_pop, key=lambda d: int(d[4]), reverse=False)
            if index == '预计库存':
                list2_new = sorted(list2_pop, key=lambda d: int(d[5]), reverse=False)
            if index == '30天销量':
                list2_new = sorted(list2_pop, key=lambda d: int(d[6]), reverse=False)
            for i in list2_new:
                i[4], i[5], i[6] = i[6], i[4], i[5]
            if list1_pop:
                for i in list2_new:
                    flag = 1
                    for j in list1_pop:
                        if j[1] == i[1]:
                            flag = 0
                            list1_new.append(j)
                    if flag:
                        list1_new.append([0, 0, 0, 0, 0, 0, 0])
                for i in list1_pop:
                    flag = 1
                    for j in list1_new:
                        if j[1] == i[1]:
                            flag = 0
                    if flag:
                        list1_new.append(i)
                for i in list1_new:
                    i[4], i[5], i[6] = i[6], i[4], i[5]
        else:
            if index == 'FBA库存':
                list1_new = sorted(list1_pop, key=lambda d: int(d[2]), reverse=False)
            if index == 'FBA在途':
                list1_new = sorted(list1_pop, key=lambda d: int(d[3]), reverse=False)
            if index == '本地库存':
                list1_new = sorted(list1_pop, key=lambda d: int(d[4]), reverse=False)
            if index == '预计库存':
                list1_new = sorted(list1_pop, key=lambda d: int(d[5]), reverse=False)
            if index == '30天销量':
                list1_new = sorted(list1_pop, key=lambda d: int(d[6]), reverse=False)
            for i in list1_new:
                i[4], i[5], i[6] = i[6], i[4], i[5]
            if list2_pop:
                for i in list1_new:
                    flag = 1
                    for j in list2_pop:
                        if j[1] == i[1]:
                            flag = 0
                            list2_new.append(j)
                    if flag:
                        list2_new.append([0, 0, 0, 0, 0, 0, 0])
                for i in list2_pop:
                    flag = 1
                    for j in list2_new:
                        if j[1] == i[1]:
                            flag = 0
                    if flag:
                        list2_new.append(i)
                for i in list2_new:
                    i[4], i[5], i[6] = i[6], i[4], i[5]
        return list1_new, list2_new

    def descending_sort(self, list1, list2, index, sort_asin):
        list1_pop = []
        if list1:
            list1.pop(0)
            for i in list1:
                if i[0]:
                    if i[1] == '0':
                        continue
                    list1_pop.append(i)
        list2_pop = []
        if list2:
            list2.pop(0)
            for i in list2:
                if i[0]:
                    if i[1] == '0':
                        continue
                    list2_pop.append(i)
        list1_new = []
        list2_new = []
        if sort_asin.find('B0') >= 0:
            if index == 'FBA库存':
                list2_new = sorted(list2_pop, key=lambda d: int(d[2]), reverse=True)
            if index == 'FBA在途':
                list2_new = sorted(list2_pop, key=lambda d: int(d[3]), reverse=True)
            if index == '本地库存':
                list2_new = sorted(list2_pop, key=lambda d: int(d[4]), reverse=True)
            if index == '预计库存':
                list2_new = sorted(list2_pop, key=lambda d: int(d[5]), reverse=True)
            if index == '30天销量':
                list2_new = sorted(list2_pop, key=lambda d: int(d[6]), reverse=True)
            for i in list2_new:
                i[4], i[5], i[6] = i[6], i[4], i[5]
            if list1_pop:
                for i in list2_new:
                    flag = 1
                    for j in list1_pop:
                        if j[1] == i[1]:
                            flag = 0
                            list1_new.append(j)
                    if flag:
                        list1_new.append([0, 0, 0, 0, 0, 0, 0])
                for i in list1_pop:
                    flag = 1
                    for j in list1_new:
                        if j[1] == i[1]:
                            flag = 0
                    if flag:
                        list1_new.append(i)
                for i in list1_new:
                    i[4], i[5], i[6] = i[6], i[4], i[5]
        else:
            if index == 'FBA库存':
                list1_new = sorted(list1_pop, key=lambda d: int(d[2]), reverse=True)
            if index == 'FBA在途':
                list1_new = sorted(list1_pop, key=lambda d: int(d[3]), reverse=True)
            if index == '本地库存':
                list1_new = sorted(list1_pop, key=lambda d: int(d[4]), reverse=True)
            if index == '预计库存':
                list1_new = sorted(list1_pop, key=lambda d: int(d[5]), reverse=True)
            if index == '30天销量':
                list1_new = sorted(list1_pop, key=lambda d: int(d[6]), reverse=True)
            for i in list1_new:
                i[4], i[5], i[6] = i[6], i[4], i[5]
            if list2_pop:
                for i in list1_new:
                    flag = 1
                    for j in list2_pop:
                        if j[1] == i[1]:
                            flag = 0
                            list2_new.append(j)
                    if flag:
                        list2_new.append([0, 0, 0, 0, 0, 0, 0])
                for i in list2_pop:
                    flag = 1
                    for j in list2_new:
                        if j[1] == i[1]:
                            flag = 0
                    if flag:
                        list2_new.append(i)
                for i in list2_new:
                    i[4], i[5], i[6] = i[6], i[4], i[5]
        return list1_new, list2_new

    def sql_parent_test(self):
        list_parent = []
        dict_parent = {}
        self.sql()
        dict_sku = {}
        sql = "select * from `amazon_form`.`male_sku`"
        self.cursor.execute(sql)
        result = self.cursor.fetchall()
        for i in result:
            if i['本地品名'] in dict_sku:
                dict_sku[i['本地品名']].append(i['SKU'])
            else:
                dict_sku[i['本地品名']] = []
                dict_sku[i['本地品名']].append(i['SKU'])
        for i in dict_sku:
            if i in dict_parent:
                continue
            else:
                dict_parent[i] = []
            for j in dict_sku[i]:
                sql1 = "select * from `amazon_form`.`male_parent` where `SKU` = '%s'" % j
                self.cursor.execute(sql1)
                result1 = self.cursor.fetchall()
                for k in result1:
                    if k['本地父体'] in dict_parent[i]:
                        continue
                    else:
                        dict_parent[i].append(k['本地父体'])
        for i in dict_parent:
            for j in dict_parent[i]:
                sql2 = "select * from `amazon_form`.`male_parent` where `本地父体` = '%s'" % j
                self.cursor.execute(sql2)
                result2 = self.cursor.fetchall()
                list_sku = []
                for k in result2:
                    list_sku.append(k['SKU'])
                list_male = []
                for k in dict_sku[i]:
                    list_male.append(k)
                for k in list_male:
                    if k in list_sku:
                        continue
                    else:
                        list_parent.append([j, i, k])
        self.sql_close()
        print(list_parent)

    def write_sql(self, list_sku):
        self.sql()
        for i in list_sku:
            sql = "insert into `amazon_form`.`male_parent`(`本地父体`, `SKU`)values('%s', '%s')" % (i[0], i[2])
            self.cursor.execute(sql)
            self.connection.commit()
        self.sql_close()

    def download_parent(self, asin):
        f1 = open('asin_son_info.json', 'r')
        dict_asin = json.load(f1)
        if asin in dict_asin:
            wb = openpyxl.Workbook()
            wb_sheet = wb.active
            wb_sheet.append(['ASIN'])
            for i in dict_asin[asin]:
                wb_sheet.append([i])
            time_now = datetime.now().strftime("%Y%m%d%H%M%S")
            path = f"D:/html_windows/static/父ASIN详情/{asin}详情-{time_now}.xlsx"
            wb.save(path)
            return True, [f"../父ASIN详情/{asin}详情-{time_now}.xlsx", f"{asin}详情-{time_now}"]
        else:
            return False, f"没有找到{asin}父ASIN的详情，请检查"

    def find_parent_sku(self, list_male, list_sku, local_sku):
        if list_sku:
            list_sku_new = []
            if list_sku:
                asin = list_sku[1][0]
                f1 = open(f'./static/列表详情/{asin}_info.json', 'r')
                dict_asin = json.load(f1)
                if asin in dict_asin:
                    for i in dict_asin[asin]:
                        if i[1] and i[1].find(local_sku) >= 0:
                            list_sku_new.append(i)
                else:
                    list_sku_new = list_sku
            list_male_new = []
            if list_male:
                asin = list_male[1][0]
                f1 = open(f'./static/列表详情/{asin}_info.json', 'r')
                dict_asin = json.load(f1)
                if asin in dict_asin:
                    for i in dict_asin[asin]:
                        if i[1] and i[1].find(local_sku) >= 0:
                            list_male_new.append(i)
                else:
                    list_male_new = list_male
            return list_male_new, list_sku_new
        else:
            return list_male, list_sku


if __name__ == '__main__':
    quantity = Quantity()
    quantity.download_asin()
    # quantity.find_parent_sku([['0'], ['Fire10父体']], [['0'], ['B0BRRTKF11']], 'Fire8')
    # quantity.read_json()
    # quantity.write_asin('510418804344160256')
    # quantity.write_order()
    # quantity.find_excl('B0C3J7MCNW')
    # quantity.windows_msg('K22-壳子款-玻纤板-十字纹-黑色', 'B0C3J7MCNW')
    # quantity.sql_parent_test()
    # list_sku = [['KPW5壳子支架款父体', 'K10-壳子款 深蓝[十字纹]', 'K10-Dark Blue-20190624-C'], ['KPW5壳子支架款父体', 'K10-壳子款 深蓝[十字纹]', 'CB-K10-KZK-SL（SZW）-JT'],
    #             ['K10颜色父体', 'K10-壳子款 深蓝[十字纹]', 'K10-Dark Blue-20190624-C'], ['K10颜色父体', 'K10-壳子款 深蓝[十字纹]', 'CB-K10-KZK-SL（SZW）-JT'],
    #             ['K10颜色父体', 'K10-壳子款 黑色[十字纹]', 'K10-Black-20190624-C'], ['KPW5壳子支架款父体', 'K10-壳子款 橙色[十字纹]', 'K10-Orange-20190624-C'],
    #             ['KPW5-基础壳子款-薄荷绿父体', 'K10-壳子款 紫色巴黎之星', 'CB-K10-KZK-ZSBLZX-HX'], ['KPW5壳子支架款父体', 'K10-壳子款 幸运树', 'K10-Lucky Tree-20190624-C'],
    #             ['K10颜色父体', 'K10-壳子款 幸运树', 'K10-Lucky Tree-20190624-C'], ['KPW5壳子支架款父体', 'K10-壳子款 巴黎之星', 'K10-Pink Glitter-20190707'],
    #             ['kPW5橙色茉莉父体', 'K10-壳子款 巴黎之星', 'K10-Pink Glitter-20190707'], ['K10颜色父体', 'K10-壳子款 红日仙鹤', 'K10-Crane-20200110'],
    #             ['KPW5-基础壳子款-薄荷绿父体', 'K10-壳子款 粉色闪闪心', 'CB-K10-KZK-FSSSX-HWF23-HX'], ['K10颜色父体', 'K10-壳子款 粉色闪闪心', 'K10-Pink Sparking Heart-20191227'],
    #             ['KPW5支架机框父体', 'K10-支架款 东方花纹', 'CB-K10S-DFHW-HX-Combo'], ['KPW5支架机框父体', 'K10-支架款 东方花纹', 'CB-K10S-DFHW-GGL-Combo'],
    #             ['KPW5壳子支架款父体', 'K10-壳子款 棕色[小牛皮]', 'K10-Brown-20190807'], ['KPW5壳子支架款父体', 'K10-壳子款 棕色[小牛皮]', 'CB-K10-KZK-ZS（XNP）-JT'],
    #             ['K10颜色父体', 'K10-壳子款 棕色[小牛皮]', 'K10-Brown-20190807'], ['K10颜色父体', 'K10-壳子款 棕色[小牛皮]', 'CB-K10-KZK-ZS（XNP）-JT'],
    #             ['KPW5壳子支架款父体', 'K10-壳子款 东方花纹', 'K10-Floral-20190829'], ['K10颜色父体', 'K10-壳子款 蝴蝶', 'K10-Butterfly-20190917'],
    #             ['KPW5-基础壳子款-薄荷绿父体', 'K10-壳子款 蝴蝶', 'K10-Butterfly-20190917'], ['kPW5橙色茉莉父体', 'K10-壳子款 杏花', 'CB-K10-KZK-XH-HX'],
    #             ['K10颜色父体', 'K10-壳子款 杏花', 'K10-Wintersweet-20190917'], ['kPW5橙色茉莉父体', 'K10-壳子款 树叶', 'K10-Foliage-20200325'],
    #             ['KPW5-基础壳子款-薄荷绿父体', 'K10-壳子款 树叶', 'K10-Foliage-20200325'], ['K10颜色父体', 'k10-变形金刚款 薄荷绿', 'CB-K10-BXJG-BHL（R64）-HX'],
    #             ['K10颜色父体', 'K10-变形金刚款 磨砂薰衣草浅紫', 'CB-K10-BXJG-MSXYCZ#23-HX'], ['K11-K22父体', 'K10-壳子款 磨砂薰衣草深紫', 'K10磨砂薰衣草'],
    #             ['KPW5壳子支架款父体', 'K10-壳子款 磨砂薰衣草深紫', 'K10磨砂薰衣草'], ['K10颜色父体', 'K10-壳子款 磨砂薰衣草深紫', 'K10磨砂薰衣草'],
    #             ['KPW5壳子支架款父体', 'K10-壳子款 磨砂薰衣草浅紫', 'K10磨砂薰衣草浅紫#23'], ['KPW5-基础壳子款-薄荷绿父体', 'K10-壳子款 磨砂薰衣草浅紫', 'K10磨砂薰衣草浅紫#23'],
    #             ['KPW5壳子支架款父体', 'K10-壳子款 灰色', 'K10灰色#369 20200622'], ['KPW5壳子支架款父体', 'K10-壳子款 灰色', 'CB-K10-KZK-HS#369-JT'],
    #             ['K10颜色父体', 'K10-壳子款 灰色', 'K10灰色#369 20200622'], ['K10颜色父体', 'K10-壳子款 灰色', 'CB-K10-KZK-HS#369-JT'],
    #             ['K10颜色父体', 'K10-壳子款 苹果树', 'CB-K10-KZK-PGS-HX'], ['K10颜色父体', 'K10-壳子款 渐变蓝色复古纹', 'K10渐变蓝色复古纹20200622'],
    #             ['KPW5-基础壳子款-薄荷绿父体', 'K10-壳子款 雪花', 'K10壳子款 雪花'], ['K10颜色父体', 'K10-壳子款 浪花', 'K10壳子款 浪花'],
    #             ['kPW5橙色茉莉父体', 'K10-壳子款 浪花', 'K10壳子款 浪花'], ['K10颜色父体', 'K10-壳子款 布纹黑', 'K10壳子款 布纹黑（经典330-01）'],
    #             ['KPW5-基础壳子款-薄荷绿父体', 'K10-壳子款 布纹黑', 'K10壳子款 布纹黑（经典330-01）'], ['kPW5橙色茉莉父体', 'K10-变形金刚款-十字纹玫瑰金', 'CB-K10-BXJG-SZWMGJ-HX'],
    #             ['K10颜色父体', 'k10-变形金刚款 紫色巴黎之星', 'CB-K10-BXJG-ZSBLZX-HX'], ['K10颜色父体', 'K10-壳子款 灰色热压纹', 'CB-K10-KZK-HSRYW-GGL'],
    #             ['K10颜色父体', 'K10-壳子款 灰色热压纹', 'CB-K10-KZK-HSRYHW二017-3-HX'], ['kPW5橙色茉莉父体', 'K10-壳子款 灰色热压纹', 'CB-K10-KZK-HSRYW-HX'],
    #             ['kPW5橙色茉莉父体', 'K10-壳子款 灰色热压纹', 'CB-K10-KZK-HSRYW-GGL'], ['K10颜色父体', 'K10-支架款-V2.2-杏花', 'CB-K10-ZJK-V2.2-XH-PVC-ZKBZ-GGL'],
    #             ['K10颜色父体', 'K10-支架款-V2.2-银河', 'CB-K10-ZJK-V2.2-YH-PVC-ZKBZ-GGL'], ['K10颜色父体', 'K10-支架款-V2.2-灰色', 'CB-K10-ZJK-V2.2-HS#369-PVC-ZKBZ-GGL'],
    #             ['KPW5支架机框父体', 'K10-支架款-V2.2-幸运树', 'CB-K10-ZJK-V2.2-XYS-PVC-ZKBZ-GGL'], ['K10颜色父体', 'K10-支架款-V2.2-幸运树', 'CB-K10-ZJK-V2.2-XYS-PVC-ZKBZ-GGL'],
    #             ['K10颜色父体', 'K10-支架款-V2.2-薄荷绿', 'CB-K10-ZJK-V2.2-BHL（R64）-PVC-ZKBZ-GGL'], ['K10颜色父体', 'K10-支架款-V2.2-接皮蓝', 'CB-K10-ZJK-V2.2-JPL-PVC-ZKBZ-GGL'],
    #             ['K10颜色父体', 'K10-支架款-V2.2-接皮蓝', '[CB]161'], ['K10颜色父体', 'K10-支架款-V2.2-接皮黄', 'CB-K10-ZJK-V2.2-JPH-PVC-ZKBZ-GGL'],
    #             ['K10颜色父体', 'K10-支架款-V2.2-接皮黄', '[CB]160'], ['K10颜色父体', 'K10-支架款-V2.2-东方花纹', 'CB-K10-ZJK-V2.2-DFHW-PVC-ZKBZ-GGL'],
    #             ['K10颜色父体', 'K10-支架款-V2.2-金色蝴蝶', 'CB-K10-ZJK-V2.2-JSHD-PVC-ZKBZ-GGL'], ['K10颜色父体', 'K10-支架款-V2.2-紫色巴黎之星', 'CB-K10-ZJK-V2.2-ZSBLZX-PVC-ZKBZ-GGL'],
    #             ['K10颜色父体', 'K10-支架款-V2.2-十字纹深蓝', 'CB-K10-ZJK-V2.2-SZWSL-PVC-ZKBZ-GGL'], ['K10颜色父体', 'K10-支架款-V2.2-十字纹深蓝', '[CB]169'],
    #             ['K10颜色父体', 'K10-支架款-V2.2-十字纹黑色', 'CB-K10-ZJK-V2.2-SZWHS-PVC-ZKBZ-GGL'], ['K10颜色父体', 'K10-支架款-V2.2-十字纹黑色', '[CB]168'],
    #             ['KPW5橙色茉莉父体', 'K10-支架款-V2.2-星空', 'CB-K10-ZJK-V2.2-XK-PVC-ZKBZ-GGL'], ['K10颜色父体', 'K10-支架款-V2.2-星空', 'CB-K10-ZJK-V2.2-XK-PVC-ZKBZ-GGL'],
    #             ['K10颜色父体', 'K10-支架款-V2.2-磨砂粉', 'CB-K10-ZJK-V2.2-MSF-PVC-ZKBZ-GGL'], ['K10颜色父体', 'K10-支架款-V2.2-磨砂粉', '[CB]167'],
    #             ['K10颜色父体', 'K10-支架款-雪花', 'CB-K10-ZJK-V2.2-XUEHUA-PVC-ZKBZ-GGL'], ['K10颜色父体', 'K10-支架款-V2.2-布纹粉色', 'CB-K10-ZJK-V2.2-V2.2ZYCF-PVC-ZKBZ-HX'],
    #             ['K10颜色父体', 'K10-支架款-V2.2-布纹粉色', '[CB]155'], ['KPW5橙色茉莉父体', 'K10-支架款-V2.2-十字纹玫瑰金', 'CB-K10-ZJK-V2.2-SZWMGJ-PVC-ZKBZ-GGL'],
    #             ['K10颜色父体', 'K10-支架款-V2.2-十字纹玫瑰金', 'CB-K10-ZJK-V2.2-SZWMGJ-PVC-ZKBZ-GGL'], ['KPW5支架机框父体', 'KPW5-基础机框款-R64薄荷绿', '[CB]215'],
    #             ['KPW5支架机框父体', 'KPW5-基础机框款-R64薄荷绿', '[CB]289'], ['KPW5支架机框父体', 'KPW5-基础机框款-R64薄荷绿', '[CB]323-COMBO'],
    #             ['KPW5壳子支架款父体', 'KPW5-基础机框款-R64薄荷绿', '[CB]215'], ['KPW5壳子支架款父体', 'KPW5-基础机框款-R64薄荷绿', '[CB]289'],
    #             ['KPW5壳子支架款父体', 'KPW5-基础机框款-R64薄荷绿', '[CB]323-COMBO'], ['kPW5橙色茉莉父体', 'KPW5-基础机框款-R64粉色', '[CB]216'],
    #             ['kPW5橙色茉莉父体', 'KPW5-基础机框款-R64粉色', '[CB]305-COMBO'], ['kPW5橙色茉莉父体', 'KPW5-基础机框款-R64粉色', '[CB]324-COMBO'],
    #             ['KPW5壳子支架款父体', 'KPW5-基础机框款-R64粉色', '[CB]216'], ['KPW5壳子支架款父体', 'KPW5-基础机框款-R64粉色', '[CB]290'],
    #             ['KPW5壳子支架款父体', 'KPW5-基础机框款-R64粉色', '[CB]305-COMBO'], ['KPW5壳子支架款父体', 'KPW5-基础机框款-荔枝纹棕色', '[CB]218'],
    #             ['KPW5壳子支架款父体', 'KPW5-基础机框款-荔枝纹棕色', '[CB]292'], ['KPW5壳子支架款父体', 'KPW5-基础机框款-荔枝纹棕色', '[CB]307-COMBO'],
    #             ['KPW5-支架机框款-黑色父体', 'KPW5-基础机框款-木纹', '[CB]293'], ['KPW5-支架机框款-黑色父体', 'KPW5-基础机框款-木纹', '[CB]308-COMBO'],
    #             ['KPW5壳子支架款父体', 'KPW5-基础机框款-木纹', '[CB]219'], ['KPW5壳子支架款父体', 'KPW5-基础机框款-木纹', '[CB]293'], ['KPW5壳子支架款父体', 'KPW5-基础机框款-木纹', '[CB]308-COMBO'],
    #             ['KPW5壳子支架款父体', 'KPW5-基础机框款-深蓝', '[CB]224'], ['KPW5壳子支架款父体', 'KPW5-基础机框款-深蓝', '[CB]298'], ['KPW5壳子支架款父体', 'KPW5-基础机框款-深蓝', '[CB]313-COMBO'],
    #             ['KPW5壳子支架款父体', 'KPW5-基础机框款-深蓝', 'CB.COMBO.647'], ['KPW5壳子支架款父体', 'KPW5-基础机框款-梵高星空', '[CB]229'],
    #             ['KPW5壳子支架款父体', 'KPW5-基础机框款-梵高星空', '[CB]318-COMBO'], ['KPW5壳子支架款父体', 'KPW5-基础机框款-梵高星空', '[CB]337-COMBO'],
    #             ['KPW5壳子支架款父体', 'KPW5-基础机框款-梵高柏树', '[CB]230'], ['KPW5壳子支架款父体', 'KPW5-基础机框款-梵高柏树', '[CB]304'],
    #             ['KPW5壳子支架款父体', 'KPW5-基础机框款-梵高柏树', '[CB]338-COMBO'], ['KPW5壳子支架款父体', 'KPW5-基础机框款-蓝色东方', '[CB]233'],
    #             ['KPW5壳子支架款父体', 'KPW5-基础机框款-蓝色东方', '[CB]322-COMBO'], ['KPW5壳子支架款父体', 'KPW5-基础机框款-蓝色东方', '[CB]341-COMBO'],
    #             ['KPW5支架机框父体', 'KPW5-支架机框款-R64薄荷绿', '[CB]308'], ['KPW5支架机框父体', 'KPW5-支架机框款-R64薄荷绿', '[CB]267-COMBO'],
    #             ['KPW5支架机框父体', 'KPW5-支架机框款-R64薄荷绿', '[CB]300-COMBO'], ['KPW5壳子支架款父体', 'KPW5-支架机框款-R64薄荷绿', '[CB]234'],
    #             ['KPW5壳子支架款父体', 'KPW5-支架机框款-R64薄荷绿', '[CB]308'], ['KPW5壳子支架款父体', 'KPW5-支架机框款-R64薄荷绿', '[CB]267-COMBO'],
    #             ['KPW5支架机框父体', 'KPW5-支架机框款-R64粉色', '[CB]235'], ['KPW5支架机框父体', 'KPW5-支架机框款-R64粉色', '[CB]309'],
    #             ['KPW5支架机框父体', 'KPW5-支架机框款-R64粉色', '[CB]268-COMBO'], ['KPW5壳子支架款父体', 'KPW5-支架机框款-R64粉色', '[CB]235'],
    #             ['KPW5壳子支架款父体', 'KPW5-支架机框款-R64粉色', '[CB]309'], ['KPW5壳子支架款父体', 'KPW5-支架机框款-R64粉色', '[CB]268-COMBO'],
    #             ['KPW5支架机框父体', 'KPW5-支架机框款-荔枝纹黑色', '[CB]236'], ['KPW5支架机框父体', 'KPW5-支架机框款-荔枝纹黑色', '[CB]310'],
    #             ['KPW5支架机框父体', 'KPW5-支架机框款-荔枝纹黑色', '[CB]385'], ['KPW5支架机框父体', 'KPW5-支架机框款-荔枝纹黑色', '[CB]269-COMBO'],
    #             ['KPW5支架机框父体', 'KPW5-支架机框款-荔枝纹黑色', '[CB]302-COMBO'], ['KPW5壳子支架款父体', 'KPW5-支架机框款-荔枝纹黑色', '[CB]236'],
    #             ['KPW5壳子支架款父体', 'KPW5-支架机框款-荔枝纹黑色', '[CB]310'], ['KPW5壳子支架款父体', 'KPW5-支架机框款-荔枝纹黑色', '[CB]385'],
    #             ['KPW5壳子支架款父体', 'KPW5-支架机框款-荔枝纹黑色', '[CB]263-COMBO'], ['KPW5壳子支架款父体', 'KPW5-支架机框款-荔枝纹黑色', '[CB]302-COMBO'],
    #             ['KPW5壳子支架款父体', 'KPW5-支架机框款-荔枝纹棕色', '[CB]237'], ['KPW5壳子支架款父体', 'KPW5-支架机框款-荔枝纹棕色', '[CB]311'],
    #             ['KPW5壳子支架款父体', 'KPW5-支架机框款-荔枝纹棕色', '[CB]270-COMBO'], ['KPW5壳子支架款父体', 'KPW5-支架机框款-荔枝纹棕色', 'CB.COMBO.658'],
    #             ['KPW5-支架机框款-黑色父体', 'KPW5-支架机框款-木纹', '[CB]312'], ['KPW5-支架机框款-黑色父体', 'KPW5-支架机框款-木纹', '[CB]271-COMBO'],
    #             ['KPW5支架机框父体', 'KPW5-支架机框款-木纹', '[CB]312'], ['KPW5支架机框父体', 'KPW5-支架机框款-木纹', '[CB]234-COMBO'],
    #             ['KPW5支架机框父体', 'KPW5-支架机框款-木纹', '[CB]271-COMBO'], ['KPW5壳子支架款父体', 'KPW5-支架机框款-布纹蓝色', '[CB]239'],
    #             ['KPW5壳子支架款父体', 'KPW5-支架机框款-布纹蓝色', '[CB]313'], ['KPW5壳子支架款父体', 'KPW5-支架机框款-布纹蓝色', '[CB]235-COMBO'],
    #             ['KPW5壳子支架款父体', 'KPW5-支架机框款-紫色巴黎之星', '[CB]241'], ['KPW5壳子支架款父体', 'KPW5-支架机框款-紫色巴黎之星', '[CB]315'],
    #             ['KPW5壳子支架款父体', 'KPW5-支架机框款-紫色巴黎之星', '[CB]237-COMBO'], ['KPW5壳子支架款父体', 'KPW5-支架机框款-黑色巴黎之星', '[CB]242'],
    #             ['KPW5壳子支架款父体', 'KPW5-支架机框款-黑色巴黎之星', '[CB]316'], ['KPW5壳子支架款父体', 'KPW5-支架机框款-黑色巴黎之星', '[CB]238-COMBO'],
    #             ['kPW5橙色茉莉父体', 'KPW5-支架机框款-深蓝', '[CB]276-COMBO'], ['kPW5橙色茉莉父体', 'KPW5-支架机框款-深蓝', 'CB.COMBO.643'],
    #             ['kPW5橙色茉莉父体', 'KPW5-支架机框款-深蓝', 'CB.COMBO.644'], ['KPW5支架机框父体', 'KPW5-支架机框款-深蓝', '[CB]243'], ['KPW5支架机框父体', 'KPW5-支架机框款-深蓝', '[CB]317'],
    #             ['KPW5支架机框父体', 'KPW5-支架机框款-深蓝', '[CB]276-COMBO'], ['KPW5支架机框父体', 'KPW5-支架机框款-深蓝', 'CB.COMBO.643'],
    #             ['KPW5支架机框父体', 'KPW5-支架机框款-深蓝', 'CB.COMBO.644'], ['KPW5壳子支架款父体', 'KPW5-支架机框款-深蓝', '[CB]243'], ['KPW5壳子支架款父体', 'KPW5-支架机框款-深蓝', '[CB]317'],
    #             ['KPW5壳子支架款父体', 'KPW5-支架机框款-深蓝', '[CB]276-COMBO'], ['KPW5壳子支架款父体', 'KPW5-支架机框款-深蓝', 'CB.COMBO.643'],
    #             ['KPW5壳子支架款父体', 'KPW5-支架机框款-深蓝', 'CB.COMBO.644'], ['K11-K22父体', 'KPW5-支架机框款-深灰', '[CB]244'], ['K11-K22父体', 'KPW5-支架机框款-深灰', '[CB]240-COMBO'],
    #             ['K11-K22父体', 'KPW5-支架机框款-深灰', 'CB.COMBO.663'], ['KPW5壳子支架款父体', 'KPW5-支架机框款-深灰', '[CB]244'], ['KPW5壳子支架款父体', 'KPW5-支架机框款-深灰', '[CB]318'],
    #             ['KPW5壳子支架款父体', 'KPW5-支架机框款-深灰', '[CB]277-COMBO'], ['KPW5壳子支架款父体', 'KPW5-支架机框款-深灰', 'CB.COMBO.663'], ['KPW5支架机框父体', 'KPW5-支架机框款-深棕', '[CB]245'],
    #             ['KPW5支架机框父体', 'KPW5-支架机框款-深棕', '[CB]319'], ['KPW5支架机框父体', 'KPW5-支架机框款-深棕', '[CB]278-COMBO'], ['KPW5支架机框父体', 'KPW5-支架机框款-灰白大理石', '[CB]246'],
    #             ['KPW5支架机框父体', 'KPW5-支架机框款-灰白大理石', '[CB]320'], ['KPW5支架机框父体', 'KPW5-支架机框款-灰白大理石', '[CB]279-COMBO'],
    #             ['KPW5支架机框父体', 'KPW5-支架机框款-杏花', '[CB]247'], ['KPW5支架机框父体', 'KPW5-支架机框款-杏花', '[CB]321'], ['KPW5支架机框父体', 'KPW5-支架机框款-杏花', '[CB]280-COMBO'],
    #             ['KPW5支架机框父体', 'KPW5-支架机框款-梵高星空', '[CB]248'], ['KPW5支架机框父体', 'KPW5-支架机框款-梵高星空', '[CB]244-COMBO'],
    #             ['KPW5支架机框父体', 'KPW5-支架机框款-梵高星空', '[CB]281-COMBO'], ['KPW5支架机框父体', 'KPW5-支架机框款-梵高柏树', '[CB]249'],
    #             ['KPW5支架机框父体', 'KPW5-支架机框款-梵高柏树', '[CB]245-COMBO'], ['KPW5支架机框父体', 'KPW5-支架机框款-梵高柏树', '[CB]282-COMBO'],
    #             ['KPW5支架机框父体', 'KPW5-支架机框款-银河', '[CB]250'], ['KPW5支架机框父体', 'KPW5-支架机框款-银河', '[CB]324'], ['KPW5支架机框父体', 'KPW5-支架机框款-银河', '[CB]246-COMBO'],
    #             ['KPW5支架机框父体', 'KPW5-支架机框款-金色东方', '[CB]251'], ['KPW5支架机框父体', 'KPW5-支架机框款-金色东方', '[CB]247-COMBO'],
    #             ['KPW5支架机框父体', 'KPW5-支架机框款-金色东方', '[CB]284-COMBO'], ['KPW5支架机框父体', 'KPW5-支架机框款-蓝色东方', '[CB]252'],
    #             ['KPW5支架机框父体', 'KPW5-支架机框款-蓝色东方', '[CB]248-COMBO'], ['KPW5支架机框父体', 'KPW5-支架机框款-蓝色东方', '[CB]285-COMBO'],
    #             ['KPW5-基础壳子款-薄荷绿父体', 'KPW5-基础壳子款-玻纤板-十字纹深蓝', '[PDD]62'], ['KPW5-支架机框款-黑色父体', 'KPW5-基础壳子款-玻纤板-十字纹深蓝', '[PDD]62'],
    #             ['KPW5壳子支架款父体', 'KPW5-基础壳子款-玻纤板-十字纹深蓝', '[CB]327'], ['KPW5壳子支架款父体', 'KPW5-基础壳子款-玻纤板-十字纹深蓝', 'CB.812'],
    #             ['KPW5壳子支架款父体', 'KPW5-基础壳子款-玻纤板-十字纹深蓝', 'CB.1071'], ['KPW5壳子支架款父体', 'KPW5-基础壳子款-玻纤板-十字纹深蓝', '[PDD]62'],
    #             ['kPW5橙色茉莉父体', 'KPW5-基础壳子款-玻纤板-十字纹深蓝', '[CB]327'], ['kPW5橙色茉莉父体', 'KPW5-基础壳子款-玻纤板-十字纹深蓝', 'CB.812'],
    #             ['kPW5橙色茉莉父体', 'KPW5-基础壳子款-玻纤板-十字纹深蓝', 'CB.1071'], ['kPW5橙色茉莉父体', 'KPW5-基础壳子款-玻纤板-十字纹深蓝', '[PDD]62'],
    #             ['KPW5壳子支架款父体', 'KPW5-基础壳子款-玻纤板-十字纹黑色', '[CB]328'], ['KPW5壳子支架款父体', 'KPW5-基础壳子款-玻纤板-十字纹黑色', 'CB.813'],
    #             ['KPW5壳子支架款父体', 'KPW5-基础壳子款-玻纤板-十字纹黑色', 'CB.1070'], ['KPW5壳子支架款父体', 'KPW5-基础壳子款-玻纤板-十字纹黑色', 'CB.1072'],
    #             ['KPW5壳子支架款父体', 'KPW5-基础壳子款-玻纤板-十字纹玫瑰金', '[CB]329'], ['KPW5壳子支架款父体', 'KPW5-基础壳子款-玻纤板-十字纹玫瑰金', 'CB.814'],
    #             ['KPW5壳子支架款父体', 'KPW5-基础壳子款-玻纤板-十字纹玫瑰金', 'CB.1073'], ['kPW5橙色茉莉父体', 'KPW5-基础壳子款-玻纤板-十字纹玫瑰金', '[CB]255'],
    #             ['kPW5橙色茉莉父体', 'KPW5-基础壳子款-玻纤板-十字纹玫瑰金', 'CB.814'], ['kPW5橙色茉莉父体', 'KPW5-基础壳子款-玻纤板-十字纹玫瑰金', 'CB.1073'],
    #             ['KPW5壳子支架款父体', 'KPW5-基础壳子款-玻纤板-布纹绿色', '[CB]330'], ['KPW5壳子支架款父体', 'KPW5-基础壳子款-玻纤板-布纹绿色', 'CB.815'], ['KPW5壳子支架款父体', 'KPW5-基础壳子款-玻纤板-布纹绿色', 'CB.1074'],
    #             ['KPW5-基础壳子款-薄荷绿父体', 'KPW5-基础壳子款-玻纤板-布纹黄色', '[CB]331'], ['KPW5-基础壳子款-薄荷绿父体', 'KPW5-基础壳子款-玻纤板-布纹黄色', 'CB.816'],
    #             ['KPW5-基础壳子款-薄荷绿父体', 'KPW5-基础壳子款-玻纤板-布纹黄色', 'CB.1075'], ['KPW5壳子支架款父体', 'KPW5-基础壳子款-玻纤板-布纹黄色', '[CB]331'], ['KPW5壳子支架款父体', 'KPW5-基础壳子款-玻纤板-布纹黄色', 'CB.816'],
    #             ['KPW5壳子支架款父体', 'KPW5-基础壳子款-玻纤板-布纹黄色', 'CB.1075'], ['K11-K22父体', 'KPW5-基础壳子款-玻纤板-布纹黄色', '[CB]257'], ['K11-K22父体', 'KPW5-基础壳子款-玻纤板-布纹黄色', 'CB.816'],
    #             ['K11-K22父体', 'KPW5-基础壳子款-玻纤板-布纹黄色', 'CB.1075'], ['kPW5橙色茉莉父体', 'KPW5-基础壳子款-玻纤板-布纹紫色', '[CB]332'], ['kPW5橙色茉莉父体', 'KPW5-基础壳子款-玻纤板-布纹紫色', 'CB.817'],
    #             ['kPW5橙色茉莉父体', 'KPW5-基础壳子款-玻纤板-布纹紫色', 'CB.1076'], ['KPW5壳子支架款父体', 'KPW5-基础壳子款-玻纤板-布纹紫色', '[CB]258'], ['KPW5壳子支架款父体', 'KPW5-基础壳子款-玻纤板-布纹紫色', '[CB]332'],
    #             ['KPW5壳子支架款父体', 'KPW5-基础壳子款-玻纤板-布纹紫色', 'CB.817'], ['KPW5壳子支架款父体', 'KPW5-基础壳子款-玻纤板-布纹灰色', '[CB]333'], ['KPW5壳子支架款父体', 'KPW5-基础壳子款-玻纤板-布纹灰色', 'CB.818'],
    #             ['KPW5壳子支架款父体', 'KPW5-基础壳子款-玻纤板-布纹灰色', 'CB.1077'], ['kPW5橙色茉莉父体', 'KPW5-基础壳子款-玻纤板-布纹灰色', '[CB]333'], ['kPW5橙色茉莉父体', 'KPW5-基础壳子款-玻纤板-布纹灰色', 'CB.818'],
    #             ['kPW5橙色茉莉父体', 'KPW5-基础壳子款-玻纤板-布纹灰色', 'CB.1077'], ['KPW5壳子支架款父体', 'KPW5-基础壳子款-玻纤板-东方花纹', 'CB.819'], ['KPW5壳子支架款父体', 'KPW5-基础壳子款-玻纤板-东方花纹', 'CB.1078'],
    #             ['KPW5-基础壳子款-薄荷绿父体', 'KPW5-基础壳子款-玻纤板-星座', '[CB]335'], ['KPW5-基础壳子款-薄荷绿父体', 'KPW5-基础壳子款-玻纤板-星座', 'CB.820'],
    #             ['KPW5-基础壳子款-薄荷绿父体', 'KPW5-基础壳子款-玻纤板-星座', 'CB.987'], ['KPW5-基础壳子款-薄荷绿父体', 'KPW5-基础壳子款-玻纤板-星座', 'CB.1156'], ['KPW5壳子支架款父体', 'KPW5-基础壳子款-玻纤板-星座', '[CB]261'],
    #             ['KPW5壳子支架款父体', 'KPW5-基础壳子款-玻纤板-星座', '[CB]335'], ['KPW5壳子支架款父体', 'KPW5-基础壳子款-玻纤板-星座', 'CB.987'], ['KPW5壳子支架款父体', 'KPW5-基础壳子款-玻纤板-星座', 'CB.1156'],
    #             ['KPW5壳子支架款父体', 'KPW5-基础壳子款-玻纤板-银河', '[CB]263'], ['KPW5壳子支架款父体', 'KPW5-基础壳子款-玻纤板-银河', 'CB.822'], ['KPW5壳子支架款父体', 'KPW5-基础壳子款-玻纤板-银河', 'CB.1080'],
    #             ['KPW5壳子支架款父体', 'KPW5-基础壳子款-玻纤板-黑色东方', '[CB]264'], ['KPW5壳子支架款父体', 'KPW5-基础壳子款-玻纤板-黑色东方', 'CB.823'], ['KPW5壳子支架款父体', 'KPW5-基础壳子款-玻纤板-黑色东方', 'CB.1081'],
    #             ['KPW5支架机框父体', 'KPW5-基础机框款-V2.0-荔枝纹黑色', '[CB]384'], ['KPW5支架机框父体', 'KPW5-支架机框款-流金岁月-黄棕色-骷髅', '[CB]387'],
    #             ['KPW5支架机框父体', 'KPW5-支架机框款-流金岁月-黄棕色-骷髅', '[CB]265-COMBO'], ['KPW5支架机框父体', 'KPW5-支架机框款-流金岁月-深蓝', '[CB]388'], ['KPW5支架机框父体', 'KPW5-支架机框款-流金岁月-深蓝', '[CB]266-COMBO'],
    #             ['KPW5支架机框父体', 'KPW5-支架机框款-流金岁月-深蓝', 'CB.COMBO.661'], ['KPW5壳子支架款父体', 'KPW5-支架机框款-流金岁月-深蓝', '[CB]388'], ['KPW5壳子支架款父体', 'KPW5-支架机框款-流金岁月-深蓝', '[CB]266-COMBO'],
    #             ['KPW5壳子支架款父体', 'KPW5-支架机框款-流金岁月-深蓝', 'CB.COMBO.661'], ['kPW5橙色茉莉父体', 'KPW5-基础机框款-V2.0-流金岁月-黄棕色', '[CB]344-COMBO'],
    #             ['kPW5橙色茉莉父体', 'KPW5-基础机框款-V2.0-流金岁月-深蓝', '[CB]345-COMBO'], ['KPW5-基础壳子款-薄荷绿父体', 'KPW5-基础壳子款-玻纤板-流金岁月-深棕', '[CB]395'],
    #             ['KPW5-基础壳子款-薄荷绿父体', 'KPW5-基础壳子款-玻纤板-流金岁月-深棕', 'CB.826'], ['KPW5-基础壳子款-薄荷绿父体', 'KPW5-基础壳子款-玻纤板-流金岁月-深棕', 'CB.1084'],
    #             ['KPW5壳子支架款父体', 'KPW5-基础壳子款-玻纤板-流金岁月-深棕', '[CB]392'], ['KPW5壳子支架款父体', 'KPW5-基础壳子款-玻纤板-流金岁月-深棕', 'CB.826'],
    #             ['KPW5壳子支架款父体', 'KPW5-基础壳子款-玻纤板-流金岁月-深棕', 'CB.1084'], ['KPW5-基础壳子款-薄荷绿父体', 'KPW5-基础壳子款-玻纤板-曼陀罗蓝', '[CB]400'],
    #             ['KPW5-基础壳子款-薄荷绿父体', 'KPW5-基础壳子款-玻纤板-曼陀罗蓝', 'CB.829'], ['KPW5-基础壳子款-薄荷绿父体', 'KPW5-基础壳子款-玻纤板-曼陀罗蓝', 'CB.1087'],
    #             ['kPW5橙色茉莉父体', 'K11-壳子款-波纤板-梵高星空', '[CB]457'], ['kPW5橙色茉莉父体', 'K11-壳子款-波纤板-浪花', '[CB]471'], ['kPW5橙色茉莉父体', 'K11-壳子款-波纤板-布纹灰色', '[CB]472'],
    #             ['KPW5壳子支架款父体', 'KPW5-基础壳子款-玻纤板-R64-橙色茉莉', 'CB.831'], ['KPW5壳子支架款父体', 'KPW5-基础壳子款-玻纤板-R64-橙色茉莉', 'CB.985'],
    #             ['KPW5壳子支架款父体', 'KPW5-基础壳子款-玻纤板-R64-橙色茉莉', 'CB.1154'], ['kPW5橙色茉莉父体', 'KPW5-基础壳子款-玻纤板-R64-橙色茉莉', 'CB.831'], ['kPW5橙色茉莉父体', 'KPW5-基础壳子款-玻纤板-R64-橙色茉莉', 'CB.1154'],
    #             ['kPW5橙色茉莉父体', 'KPW5-基础壳子款-玻纤板-R64-粉霞', 'CB.833'], ['kPW5橙色茉莉父体', 'KPW5-基础壳子款-玻纤板-R64-粉霞', 'CB.1090'], ['kPW5橙色茉莉父体', 'KPW5-基础壳子款-玻纤板-R64-枫树林', 'CB.834'],
    #             ['kPW5橙色茉莉父体', 'KPW5-基础壳子款-玻纤板-R64-枫树林', 'CB.1091'], ['kPW5橙色茉莉父体', 'KPW5-基础壳子款-玻纤板-R64-鹤望兰', 'CB.835'], ['kPW5橙色茉莉父体', 'KPW5-基础壳子款-玻纤板-R64-鹤望兰', 'CB.1092'],
    #             ['KPW5壳子支架款父体', 'KPW5-基础壳子款-玻纤板-R64-鹤望兰', 'CB.835'], ['KPW5壳子支架款父体', 'KPW5-基础壳子款-玻纤板-R64-鹤望兰', 'CB.1092'], ['kPW5橙色茉莉父体', 'KPW5-基础壳子款-玻纤板-R64-湖泊', 'CB.836'],
    #             ['kPW5橙色茉莉父体', 'KPW5-基础壳子款-玻纤板-R64-湖泊', 'CB.1093'], ['KPW5壳子支架款父体', 'KPW5-基础壳子款-玻纤板-R64-湖泊', 'CB.836'], ['KPW5壳子支架款父体', 'KPW5-基础壳子款-玻纤板-R64-湖泊', 'CB.1093'],
    #             ['KPW5壳子支架款父体', 'KPW5-基础壳子款-玻纤板-R64-极光', 'CB.837'], ['KPW5壳子支架款父体', 'KPW5-基础壳子款-玻纤板-R64-极光', 'CB.1094'], ['kPW5橙色茉莉父体', 'KPW5-基础壳子款-玻纤板-R64-极光', 'CB.837'],
    #             ['kPW5橙色茉莉父体', 'KPW5-基础壳子款-玻纤板-R64-极光', 'CB.1094'], ['K11-K22父体', 'KPW5-基础壳子款-玻纤板-R64-菊花', 'CB.838'], ['K11-K22父体', 'KPW5-基础壳子款-玻纤板-R64-菊花', 'CB.992'],
    #             ['K11-K22父体', 'KPW5-基础壳子款-玻纤板-R64-菊花', 'CB.1161'], ['KPW5壳子支架款父体', 'KPW5-基础壳子款-玻纤板-R64-菊花', 'CB.838'], ['KPW5壳子支架款父体', 'KPW5-基础壳子款-玻纤板-R64-菊花', 'CB.992'],
    #             ['KPW5壳子支架款父体', 'KPW5-基础壳子款-玻纤板-R64-菊花', 'CB.1161'], ['kPW5橙色茉莉父体', 'KPW5-基础壳子款-玻纤板-R64-菊花', 'CB.838'], ['kPW5橙色茉莉父体', 'KPW5-基础壳子款-玻纤板-R64-菊花', 'CB.992'],
    #             ['kPW5橙色茉莉父体', 'KPW5-基础壳子款-玻纤板-R64-菊花', 'CB.1161'], ['KPW5壳子支架款父体', 'KPW5-基础壳子款-玻纤板-R64-兰花', 'CB.839'], ['KPW5壳子支架款父体', 'KPW5-基础壳子款-玻纤板-R64-兰花', 'CB.993'],
    #             ['KPW5壳子支架款父体', 'KPW5-基础壳子款-玻纤板-R64-兰花', 'CB.1162'], ['kPW5橙色茉莉父体', 'KPW5-基础壳子款-玻纤板-R64-兰花', 'CB.839'], ['kPW5橙色茉莉父体', 'KPW5-基础壳子款-玻纤板-R64-兰花', 'CB.993'],
    #             ['kPW5橙色茉莉父体', 'KPW5-基础壳子款-玻纤板-R64-兰花', 'CB.1162'], ['kPW5橙色茉莉父体', 'KPW5-基础壳子款-玻纤板-R64-落日余晖', 'CB.840'], ['kPW5橙色茉莉父体', 'KPW5-基础壳子款-玻纤板-R64-落日余晖', 'CB.1095'],
    #             ['kPW5橙色茉莉父体', 'KPW5-基础壳子款-玻纤板-R64-欧洲小镇', 'CB.841'], ['kPW5橙色茉莉父体', 'KPW5-基础壳子款-玻纤板-R64-欧洲小镇', 'CB.1096'], ['kPW5橙色茉莉父体', 'KPW5-基础壳子款-玻纤板-R64-蒲公英', 'CB.842'],
    #             ['kPW5橙色茉莉父体', 'KPW5-基础壳子款-玻纤板-R64-蒲公英', 'CB.1097'], ['kPW5橙色茉莉父体', 'KPW5-基础壳子款-玻纤板-R64-山雾', 'CB.844'], ['kPW5橙色茉莉父体', 'KPW5-基础壳子款-玻纤板-R64-山雾', 'CB.1099'],
    #             ['kPW5橙色茉莉父体', 'KPW5-基础壳子款-玻纤板-R64-夕阳船舶', 'CB.845'], ['kPW5橙色茉莉父体', 'KPW5-基础壳子款-玻纤板-R64-夕阳船舶', 'CB.1100'], ['kPW5橙色茉莉父体', 'KPW5-基础壳子款-玻纤板-R64-霞峰', 'CB.846'],
    #             ['kPW5橙色茉莉父体', 'KPW5-基础壳子款-玻纤板-R64-霞峰', 'CB.1101'], ['kPW5橙色茉莉父体', 'KPW5-基础壳子款-玻纤板-R64-雪中街', 'CB.847'], ['kPW5橙色茉莉父体', 'KPW5-基础壳子款-玻纤板-R64-雪中街', 'CB.1102'],
    #             ['kPW5橙色茉莉父体', 'KPW5-基础壳子款-玻纤板-R64-栀子花', 'CB.848'], ['kPW5橙色茉莉父体', 'KPW5-基础壳子款-玻纤板-R64-栀子花', 'CB.990'], ['kPW5橙色茉莉父体', 'KPW5-基础壳子款-玻纤板-R64-栀子花', 'CB.1159'],
    #             ['KPW5-基础壳子款-薄荷绿父体', 'KPW5-基础壳子款-玻纤板-R64-栀子花', 'CB.848'], ['KPW5-基础壳子款-薄荷绿父体', 'KPW5-基础壳子款-玻纤板-R64-栀子花', 'CB.990'],
    #             ['KPW5-基础壳子款-薄荷绿父体', 'KPW5-基础壳子款-玻纤板-R64-栀子花', 'CB.1159'], ['KPW5壳子支架款父体', 'KPW5-基础壳子款-玻纤板-R64-栀子花', 'CB.848'],
    #             ['KPW5壳子支架款父体', 'KPW5-基础壳子款-玻纤板-R64-栀子花', 'CB.990'], ['KPW5壳子支架款父体', 'KPW5-基础壳子款-玻纤板-R64-栀子花', 'CB.1159'], ['kPW5橙色茉莉父体', 'KPW5-基础壳子款-玻纤板-R64-紫丁香', 'CB.849'],
    #             ['kPW5橙色茉莉父体', 'KPW5-基础壳子款-玻纤板-R64-紫丁香', 'CB.988'], ['kPW5橙色茉莉父体', 'KPW5-基础壳子款-玻纤板-R64-紫丁香', 'CB.1157'], ['KPW5壳子支架款父体', 'KPW5-基础壳子款-玻纤板-布纹黑', 'CB.850'],
    #             ['KPW5壳子支架款父体', 'KPW5-基础壳子款-玻纤板-布纹黑', 'CB.1103'], ['KPW5壳子支架款父体', 'KPW5-基础壳子款-玻纤板-布纹黑', '[ZX]287'], ['KPW5-基础壳子款-薄荷绿父体', 'KPW5-基础壳子款-玻纤板-布纹黑', 'CB.850'],
    #             ['KPW5-基础壳子款-薄荷绿父体', 'KPW5-基础壳子款-玻纤板-布纹黑', 'CB.1103'], ['KPW5-基础壳子款-薄荷绿父体', 'KPW5-基础壳子款-玻纤板-布纹黑', '[ZX]287'],
    #             ['账单夹父体', '账单夹-灰白大理石-富发#HY2317-3-两件装', 'CB.434-COMBO'], ['账单夹父体', '账单夹-灰白大理石-富发#HY2317-3-十件装', 'CB.435-COMBO'],
    #             ['账单夹父体', '账单夹-灰白大理石-富发#HY2317-3-二十件装', 'CB.436-COMBO'], ['账单夹父体', '账单夹-黑色大理石-富发#HY2317-18-两件装', 'CB.437-COMBO'],
    #             ['账单夹父体', '账单夹-黑色大理石-富发#HY2317-18-十件装', 'CB.438-COMBO'], ['账单夹父体', '账单夹-黑色大理石-富发#HY2317-18-二十件装', 'CB.439-COMBO'],
    #             ['KPW5壳子支架款父体', 'KPW5-基础壳子款-玻纤板-R64-浅绿繁花', 'CB.610'], ['KPW5壳子支架款父体', 'KPW5-基础壳子款-玻纤板-R64-浅绿繁花', 'CB.852'], ['KPW5壳子支架款父体', 'KPW5-基础壳子款-玻纤板-R64-浅绿繁花', 'CB.991'],
    #             ['KPW5壳子支架款父体', 'KPW5-基础壳子款-玻纤板-R64-浅绿繁花', 'CB.1160'], ['kPW5橙色茉莉父体', 'KPW5-基础壳子款-玻纤板-R64-浅绿繁花', 'CB.610'], ['kPW5橙色茉莉父体', 'KPW5-基础壳子款-玻纤板-R64-浅绿繁花', 'CB.852'],
    #             ['kPW5橙色茉莉父体', 'KPW5-基础壳子款-玻纤板-R64-浅绿繁花', 'CB.991'], ['kPW5橙色茉莉父体', 'KPW5-基础壳子款-玻纤板-R64-浅绿繁花', 'CB.1160'],
    #             ['KPW5-基础壳子款-薄荷绿父体', 'KPW5-基础壳子款-玻纤板-R64-浅绿繁花', 'CB.610'], ['KPW5-基础壳子款-薄荷绿父体', 'KPW5-基础壳子款-玻纤板-R64-浅绿繁花', 'CB.852'],
    #             ['KPW5-基础壳子款-薄荷绿父体', 'KPW5-基础壳子款-玻纤板-R64-浅绿繁花', 'CB.991'], ['KPW5-基础壳子款-薄荷绿父体', 'KPW5-基础壳子款-玻纤板-R64-浅绿繁花', 'CB.1160'],
    #             ['KPW5壳子支架款父体', 'KPW5-支架机框款-R64-橙色茉莉', 'CB.COMBO.524'], ['KPW5壳子支架款父体', 'KPW5-支架机框款-R64-橙色茉莉', 'CB.COMBO.645'], ['KPW5壳子支架款父体', 'KPW5-支架机框款-R64-橙色茉莉', 'CB.COMBO.646'],
    #             ['KPW5壳子支架款父体', 'KPW5-基础壳子款-玻纤板-荔枝纹棕色', 'CB.614'], ['KPW5壳子支架款父体', 'KPW5-基础壳子款-玻纤板-荔枝纹棕色', 'CB.1105'], ['KPW5-基础壳子款-薄荷绿父体', 'KPW5-基础壳子款-玻纤板-荔枝纹棕色', 'CB.614'],
    #             ['KPW5-基础壳子款-薄荷绿父体', 'KPW5-基础壳子款-玻纤板-荔枝纹棕色', 'CB.1105'], ['KPW5壳子支架款父体', 'KPW5-基础壳子款-玻纤板-豹纹', 'CB.858'], ['KPW5壳子支架款父体', 'KPW5-基础壳子款-玻纤板-豹纹', 'CB.1110'],
    #             ['KPW5-基础壳子款-薄荷绿父体', 'KPW5-基础壳子款-玻纤板-孔雀', 'CB.859'], ['KPW5-基础壳子款-薄荷绿父体', 'KPW5-基础壳子款-玻纤板-孔雀', 'CB.1111'],
    #             ['KPW5-基础壳子款-薄荷绿父体', 'KPW5-基础壳子款-玻纤板-复古红色花卉', 'CB.860'], ['KPW5-基础壳子款-薄荷绿父体', 'KPW5-基础壳子款-玻纤板-复古红色花卉', 'CB.1112'],
    #             ['KPW5-基础壳子款-薄荷绿父体', 'KPW5-基础壳子款-玻纤板-碎花', 'CB.861'], ['KPW5-基础壳子款-薄荷绿父体', 'KPW5-基础壳子款-玻纤板-碎花', 'CB.1113'],
    #             ['KPW5-基础壳子款-薄荷绿父体', 'KPW5-基础壳子款-玻纤板-小雏菊', 'CB.862'], ['KPW5-基础壳子款-薄荷绿父体', 'KPW5-基础壳子款-玻纤板-小雏菊', 'CB.984'],
    #             ['KPW5-基础壳子款-薄荷绿父体', 'KPW5-基础壳子款-玻纤板-小雏菊', 'CB.1153'], ['KPW5壳子支架款父体', 'KPW5-基础壳子款-玻纤板-小雏菊', 'CB.631'], ['KPW5壳子支架款父体', 'KPW5-基础壳子款-玻纤板-小雏菊', 'CB.984'],
    #             ['KPW5壳子支架款父体', 'KPW5-基础壳子款-玻纤板-小雏菊', 'CB.1153'], ['KPW5支架机框父体', 'KPW5-支架机框款-布纹紫色', 'CB.COMBO.662'], ['KPW5壳子支架款父体', 'KPW5-基础壳子款-玻纤板-R64粉色', 'CB.643'],
    #             ['KPW5壳子支架款父体', 'KPW5-基础壳子款-玻纤板-R64粉色', 'CB.1114'], ['kPW5橙色茉莉父体', 'KPW5-基础壳子款-玻纤板-R64-紫方格', 'CB.864'], ['kPW5橙色茉莉父体', 'KPW5-基础壳子款-玻纤板-R64-紫方格', 'CB.1115'],
    #             ['kPW5橙色茉莉父体', 'KPW5-基础壳子款-玻纤板-R64-日式樱花', 'CB.865'], ['kPW5橙色茉莉父体', 'KPW5-基础壳子款-玻纤板-R64-日式樱花', 'CB.1116'], ['kPW5橙色茉莉父体', 'KPW5-基础壳子款-玻纤板-R64-红腰果', 'CB.866'],
    #             ['kPW5橙色茉莉父体', 'KPW5-基础壳子款-玻纤板-R64-红腰果', 'CB.1117'], ['kPW5橙色茉莉父体', 'KPW5-基础壳子款-玻纤板-R64-天蓝雏菊', 'CB.867'], ['kPW5橙色茉莉父体', 'KPW5-基础壳子款-玻纤板-R64-天蓝雏菊', 'CB.989'],
    #             ['kPW5橙色茉莉父体', 'KPW5-基础壳子款-玻纤板-R64-天蓝雏菊', 'CB.1158'], ['KPW5壳子支架款父体', 'KPW5-基础壳子款-玻纤板-玫瑰金巴黎之星', 'CB.649'],
    #             ['KPW5壳子支架款父体', 'KPW5-基础壳子款-玻纤板-玫瑰金巴黎之星', 'CB.1118'], ['KPW5-基础壳子款-薄荷绿父体', 'KPW5-基础壳子款-玻纤板-玫瑰金巴黎之星', 'CB.649'],
    #             ['KPW5-基础壳子款-薄荷绿父体', 'KPW5-基础壳子款-玻纤板-玫瑰金巴黎之星', 'CB.1118'], ['KPW5壳子支架款父体', 'KPW5-基础壳子款-玻纤板-黑色巴黎之星', 'CB.869'],
    #             ['KPW5壳子支架款父体', 'KPW5-基础壳子款-玻纤板-黑色巴黎之星', 'CB.1119'], ['KPW5-基础壳子款-薄荷绿父体', 'KPW5-基础壳子款-玻纤板-黑色巴黎之星', 'CB.869'],
    #             ['KPW5-基础壳子款-薄荷绿父体', 'KPW5-基础壳子款-玻纤板-黑色巴黎之星', 'CB.1119'], ['kPW5橙色茉莉父体', 'KPW5-基础壳子款-玻纤板-R64-复古花卉', 'CB.873'],
    #             ['kPW5橙色茉莉父体', 'KPW5-基础壳子款-玻纤板-R64-复古花卉', 'CB.1123'], ['KPW5-基础壳子款-薄荷绿父体', 'KPW5-基础壳子款-玻纤板-R64-黑夜绽放', 'CB.874'],
    #             ['KPW5-基础壳子款-薄荷绿父体', 'KPW5-基础壳子款-玻纤板-R64-黑夜绽放', 'CB.1124'], ['kPW5橙色茉莉父体', 'KPW5-基础壳子款-玻纤板-R64-热气球', 'CB.875'],
    #             ['kPW5橙色茉莉父体', 'KPW5-基础壳子款-玻纤板-R64-热气球', 'CB.1125'], ['kPW5橙色茉莉父体', 'KPW5-基础壳子款-玻纤板-R64-沉默的羔羊', 'CB.876'],
    #             ['kPW5橙色茉莉父体', 'KPW5-基础壳子款-玻纤板-R64-沉默的羔羊', 'CB.1126'], ['kPW5橙色茉莉父体', 'KPW5-基础壳子款-玻纤板-R64-读书小孩', 'CB.877'], ['kPW5橙色茉莉父体', 'KPW5-基础壳子款-玻纤板-R64-读书小孩', 'CB.1127'],
    #             ['kPW5橙色茉莉父体', 'KPW5-基础壳子款-玻纤板-R64-粉猫杂志', 'CB.878'], ['kPW5橙色茉莉父体', 'KPW5-基础壳子款-玻纤板-R64-粉猫杂志', 'CB.1128'], ['kPW5橙色茉莉父体', 'KPW5-基础壳子款-玻纤板-R64-工作与梦想', 'CB.879'],
    #             ['kPW5橙色茉莉父体', 'KPW5-基础壳子款-玻纤板-R64-工作与梦想', 'CB.1129'], ['kPW5橙色茉莉父体', 'KPW5-基础壳子款-玻纤板-R64-黑白电视', 'CB.880'], ['kPW5橙色茉莉父体', 'KPW5-基础壳子款-玻纤板-R64-黑白电视', 'CB.1130'],
    #             ['kPW5橙色茉莉父体', 'KPW5-基础壳子款-玻纤板-R64-黑底彩虹', 'CB.881'], ['kPW5橙色茉莉父体', 'KPW5-基础壳子款-玻纤板-R64-黑底彩虹', 'CB.1131'], ['kPW5橙色茉莉父体', 'KPW5-基础壳子款-玻纤板-R64-黄色迷幻', 'CB.882'],
    #             ['kPW5橙色茉莉父体', 'KPW5-基础壳子款-玻纤板-R64-黄色迷幻', 'CB.1132'], ['KPW5壳子支架款父体', 'KPW5-基础壳子款-玻纤板-R64-火箭遨游', 'CB.883'], ['KPW5壳子支架款父体', 'KPW5-基础壳子款-玻纤板-R64-火箭遨游', 'CB.1133'],
    #             ['kPW5橙色茉莉父体', 'KPW5-基础壳子款-玻纤板-R64-火箭遨游', 'CB.883'], ['kPW5橙色茉莉父体', 'KPW5-基础壳子款-玻纤板-R64-火箭遨游', 'CB.1133'], ['kPW5橙色茉莉父体', 'KPW5-基础壳子款-玻纤板-R64-咖啡', 'CB.884'],
    #             ['kPW5橙色茉莉父体', 'KPW5-基础壳子款-玻纤板-R64-咖啡', 'CB.1134'], ['kPW5橙色茉莉父体', 'KPW5-基础壳子款-玻纤板-R64-乐观', 'CB.885'], ['kPW5橙色茉莉父体', 'KPW5-基础壳子款-玻纤板-R64-乐观', 'CB.1135'],
    #             ['kPW5橙色茉莉父体', 'KPW5-基础壳子款-玻纤板-R64-深蓝波浪', 'CB.886'], ['kPW5橙色茉莉父体', 'KPW5-基础壳子款-玻纤板-R64-深蓝波浪', 'CB.1136'], ['kPW5橙色茉莉父体', 'KPW5-基础壳子款-玻纤板-R64-太空少女', 'CB.887'],
    #             ['kPW5橙色茉莉父体', 'KPW5-基础壳子款-玻纤板-R64-太空少女', 'CB.1137'], ['kPW5橙色茉莉父体', 'KPW5-基础壳子款-玻纤板-R64-紫色笑脸', 'CB.888'], ['kPW5橙色茉莉父体', 'KPW5-基础壳子款-玻纤板-R64-紫色笑脸', 'CB.1138'],
    #             ['KPW5支架机框父体', 'KPW5-支架机框款-十字纹深蓝', 'CB.COMBO.650'], ['KPW5壳子支架款父体', 'KPW5-支架机框款-十字纹深蓝', 'CB.COMBO.650'], ['KPW5壳子支架款父体', 'KPW5-基础壳子款-玻纤板-墨绿色', 'CB.736'],
    #             ['KPW5壳子支架款父体', 'KPW5-基础壳子款-玻纤板-墨绿色', 'CB.1139'], ['KPW5-基础壳子款-薄荷绿父体', 'KPW5-基础壳子款-玻纤板-墨绿色', 'CB.736'], ['KPW5-基础壳子款-薄荷绿父体', 'KPW5-基础壳子款-玻纤板-墨绿色', 'CB.1139'],
    #             ['KPW5-基础壳子款-薄荷绿父体', 'KPW5-基础壳子款-玻纤板-天蓝色', 'CB.890'], ['KPW5-基础壳子款-薄荷绿父体', 'KPW5-基础壳子款-玻纤板-天蓝色', 'CB.1140'],
    #             ['KPW5-基础壳子款-薄荷绿父体', 'KPW5-基础壳子款-玻纤板-夏天', 'CB.855'], ['KPW5-基础壳子款-薄荷绿父体', 'KPW5-基础壳子款-玻纤板-夏天', 'CB.1107'], ['KPW5壳子支架款父体', 'KPW5-基础壳子款-玻纤板-夏天', 'CB.855'],
    #             ['KPW5壳子支架款父体', 'KPW5-基础壳子款-玻纤板-夏天', 'CB.1107'], ['KPW5壳子支架款父体', 'KPW5-基础壳子款-玻纤板-月亮', 'CB.941'], ['KPW5壳子支架款父体', 'KPW5-基础壳子款-玻纤板-爱', 'CB.1143'],
    #             ['KPW5壳子支架款父体', 'KPW5-基础壳子款-玻纤板-可爱', 'CB.1144'], ['KPW5-基础壳子款-薄荷绿父体', 'KPW5-基础壳子款-玻纤板-棕色豹纹改版', 'CB.1155'],
    #             ['KPW5壳子支架款父体', 'KPW5-基础壳子款-玻纤板-棕色豹纹改版', 'CB.1155']]
    # quantity.write_sql(list_sku)
    # quantity.find_list_male("", "美国")
