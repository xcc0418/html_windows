import openpyxl
import requests
import pymysql
import json
import datetime
import hashlib
import urllib
import base64
from Crypto.Cipher import AES


######## AES-128-ECS 加密
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
        # print(response.text)
        self.access_token = result['data']['access_token']
        self.refresh_token = result['data']['refresh_token']
        self.time = datetime.datetime.now().strftime("%Y-%m-%d")
        self.time = datetime.datetime.strptime(self.time, "%Y-%m-%d")
        # self.time = "2021-12-06"
        self.start_time = self.time - datetime.timedelta(days=1)
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
        # body = {"access_token": self.access_token,
        #         "timestamp": int(time.time()),
        #         "start_date": f"{self.start_time}",
        #         "end_date": f"{self.time}",
        #         "app_key": apikey}
        # print(body)
        # bb = sign().get_sign(apikey, body)
        # print(bb)

        # 目标md5串
        str_parm = ''
        # 将字典中的key排序
        for p in sorted (body):
            # 每次排完序的加到串中
            # if body[p]:
            # str类型需要转化为url编码格式
            if isinstance (body[p], str):
                str_parm = str_parm + str (p) + "=" + str (urllib.parse.quote (body[p])) + "&"
                continue
            # if isinstance(body[p], dict):
            #     for i in body[p]:
            #         body[p][i] = str(body[p][i])
            # if isinstance(body[p], list) and isinstance(body[p][0], dict):
            #     for i in range(0, len(body[p])):
            #         for j in body[p][i]:
            #             body[p][i][j] = str(urllib.parse.quote(str(body[p][i][j])))
            # if p == "product_list":
            #     str_parm = str_parm + str(p) + "=" + '[{"sku":"GCWL.897","good_num":1,"bad_num":0,"seller_id":0,"fnsku":""}]' + "&"
            #     continue
            #     body[p][0] = str(urllib.parse.quote(body[p][0]))
            #     print(str(urllib.parse.quote(body[p][0])))
            str_value = str (body[p])
            str_value = str_value.replace (" ", "")
            # str_value = str_value.replace("?", " ")
            str_value = str_value.replace ("'", "\"")
            str_parm = str_parm + str (p) + "=" + str_value + "&"
        # 加上对应的key
        str_parm = str_parm.rstrip ('&')
        # print("字符串拼接1:", str_parm)
        str_parm = str_parm.replace ("?", " ")
        # print("字符串拼接2:", str_parm)
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

    def add_male(self, male_parent):
        self.sql()
        sql = "select * from `amazon_form`.`list_parent` where `本地父体` = '%s'" % male_parent
        self.cursor.execute(sql)
        result = self.cursor.fetchall()
        if result:
            return False, "已经有这个本地父体了，请检查"
        else:
            try:
                sql1 = "insert into `amazon_form`.`list_parent`(`本地父体`)values('%s')" % male_parent
                self.cursor.execute(sql1)
                self.connection.commit()
                self.sql_close()
                return True, True
            except Exception as e:
                self.connection.rollback()
                self.sql_close()
                return False, e

    def upload_male(self, filename):
        try:
            wb = openpyxl.load_workbook(filename)
            wb_sheet = wb.active
            row1 = wb_sheet.max_row
            for i in range(row1, 0, -1):
                cell_value1 = wb_sheet.cell(row=i, column=1).value
                if cell_value1:
                    row1 = i
                    break
            for i in range(2, row1+1):
                male_parent = wb_sheet.cell(row=i, column=1).value
                if male_parent:
                    msg, message = self.add_male(male_parent)
                    if msg:
                        continue
                    else:
                        wb_sheet.cell(row=i, column=2).value = message
            wb.save(filename)
            return True
        except Exception as e:
            print(e)
            return False

    def upload_sku(self, filename):
        try:
            wb = openpyxl.load_workbook(filename)
            wb_sheet = wb.active
            row1 = wb_sheet.max_row
            for i in range(row1, 0, -1):
                cell_value1 = wb_sheet.cell(row=i, column=1).value
                if cell_value1:
                    row1 = i
                    break
            for i in range(2, row1+1):
                male_sku = wb_sheet.cell(row=i, column=1).value
                if male_sku:
                    msg, message = self.add_sku(male_sku)
                    if msg:
                        continue
                    else:
                        wb_sheet.cell(row=i, column=2).value = message
            wb.save(filename)
            return True
        except Exception as e:
            print(e)
            return False

    def upload_parent(self, filename):
        try:
            wb = openpyxl.load_workbook(filename)
            wb_sheet = wb.active
            row1 = wb_sheet.max_row
            for i in range(row1, 0, -1):
                cell_value1 = wb_sheet.cell(row=i, column=1).value
                if cell_value1:
                    row1 = i
                    break
            for i in range(2, row1+1):
                male_parent = wb_sheet.cell(row=i, column=1).value
                sku = wb_sheet.cell(row=i, column=2).value
                msg, message = self.relevance_male(male_parent, sku)
                wb_sheet.cell(row=i, column=3).value = message
            time_now = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            wb.save(f'./static/本地父体/关联本地父体_{time_now}.xlsx')
            return True, [f'../本地父体/关联本地父体_{time_now}.xlsx', f"关联本地父体_{time_now}.xlsx"]
        except Exception as e:
            return False, e

    def upload_name(self, filename):
        try:
            wb = openpyxl.load_workbook(filename)
            wb_sheet = wb.active
            row1 = wb_sheet.max_row
            for i in range(row1, 0, -1):
                cell_value1 = wb_sheet.cell(row=i, column=1).value
                if cell_value1:
                    row1 = i
                    break
            for i in range(2, row1+1):
                male_parent = wb_sheet.cell(row=i, column=1).value
                sku = wb_sheet.cell(row=i, column=2).value
                msg, message = self.relevance_sku(male_parent, sku)
                wb_sheet.cell(row=i, column=3).value = message
            time_now = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            wb.save(f'./static/本地品名/关联本地品名_{time_now}.xlsx')
            return True, [f'../本地品名/关联本地品名_{time_now}.xlsx', f"关联本地品名_{time_now}.xlsx"]
        except Exception as e:
            print(e)
            return False, e

    def add_sku(self, local_sku):
        self.sql()
        sql = "select * from `amazon_form`.`list_local_sku` where `本地品名` = '%s'" % local_sku
        self.cursor.execute(sql)
        result = self.cursor.fetchall()
        if result:
            return False, "已经有这个本地品名了，请检查"
        else:
            try:
                sql1 = "insert into `amazon_form`.`list_local_sku`(`本地品名`)values('%s')" % local_sku
                self.cursor.execute(sql1)
                self.connection.commit()
                self.sql_close()
                return True, True
            except Exception as e:
                self.connection.rollback()
                self.sql_close()
                return False, e

    def relevance_male(self, male_parent, sku):
        self.sql()
        sql = "select * from `amazon_form`.`list_parent` where `本地父体` = '%s'" % male_parent
        self.cursor.execute(sql)
        result = self.cursor.fetchall()
        if result:
            sql = "select * from `amazon_form`.`male_parent` where `本地父体` = '%s' and `SKU` = '%s'" % (male_parent, sku)
            self.cursor.execute(sql)
            result = self.cursor.fetchall()
            if result:
                return False, f"{male_parent}与{sku}已关联"
            else:
                sql1 = "insert into `amazon_form`.`male_parent`(`本地父体`, `SKU`)values('%s', '%s')" % (male_parent, sku)
                try:
                    self.cursor.execute(sql1)
                    self.connection.commit()
                    return True, '成功'
                except Exception as e:
                    self.connection.rollback()
                    return False, e
        else:
            self.sql_close()
            return False, f"没有{male_parent}这个本地父体，请检查"

    def relieve_male(self, male_parent, sku):
        self.sql()
        sql = "select * from `amazon_form`.`male_parent` where `本地父体` = '%s' and `SKU` = '%s'" % (male_parent, sku)
        self.cursor.execute(sql)
        result = self.cursor.fetchall()
        if result:
            sql1 = "DELETE FROM `amazon_form`.`male_parent` WHERE `本地父体` = '%s' and `SKU` = '%s'" % (male_parent, sku)
            try:
                self.cursor.execute(sql1)
                self.connection.commit()
                self.sql_close()
                return True, True
            except Exception as e:
                self.connection.rollback()
                self.sql_close()
                return False, e
        else:
            self.sql_close()
            return False, "这个父体与sku没有相关信息"

    def relevance_sku(self, local_sku, sku):
        self.sql()
        sql = "select * from `amazon_form`.`list_parent` where `本地父体` = '%s'" % local_sku
        self.cursor.execute(sql)
        result = self.cursor.fetchall()
        if result:
            sql = "select * from `amazon_form`.`male_sku` where `本地品名` = '%s' and `SKU` = '%s'" % (local_sku, sku)
            self.cursor.execute(sql)
            result = self.cursor.fetchall()
            if result:
                self.sql_close()
                return False, f"{local_sku}与{sku}已关联"
            else:
                sql1 = "insert into `amazon_form`.`male_sku`(`本地品名`, `SKU`)values('%s', '%s')" % (local_sku, sku)
                try:
                    self.cursor.execute(sql1)
                    self.connection.commit()
                    self.sql_close()
                    return True, '成功'
                except Exception as e:
                    self.connection.rollback()
                    self.sql_close()
                    return False, e
        else:
            self.sql_close()
            return False, f"没有{local_sku}这个本地父体，请检查"

    def relieve_sku(self, local_sku, sku):
        self.sql()
        sql = "select * from `amazon_form`.`male_sku` where `本地品名` = '%s' and `SKU` = '%s'" % (local_sku, sku)
        self.cursor.execute(sql)
        result = self.cursor.fetchall()
        if result:
            sql1 = "DELETE FROM `amazon_form`.`male_sku` WHERE `本地品名` = '%s' and `SKU` = '%s'" % (local_sku, sku)
            try:
                self.cursor.execute(sql1)
                self.connection.commit()
                self.sql_close()
                return True, True
            except Exception as e:
                self.connection.rollback()
                self.sql_close()
                return False, e
        else:
            self.sql_close()
            return False, "这个父体与sku没有相关信息"

    def get_male_parent(self, index, index_data):
        self.sql()
        if index == "本地父体":
            if index_data:
                sql = f"select * from `amazon_form`.`male_parent` where `本地父体` like '%{index_data}%'"
            else:
                sql = "select * from `amazon_form`.`list_parent`"
                self.cursor.execute(sql)
                result = self.cursor.fetchall()
                self.sql_close()
                if result:
                    list_data = []
                    for i in result:
                        list_data.append([i['本地父体']])
                    return list_data, 1
                else:
                    return False, 0
        else:
            if index_data:
                sql = f"select * from `amazon_form`.`male_parent` where `SKU` like '%{index_data}%'"
            else:
                sql = "select * from `amazon_form`.`male_parent`"
        self.cursor.execute(sql)
        result = self.cursor.fetchall()
        self.sql_close()
        if result:
            list_data = []
            for i in result:
                list_data.append([i['本地父体'], i['SKU']])
            return list_data, 0
        else:
            return False, 0

    def get_male_sku(self, index, index_data):
        self.sql()
        if index == "本地品名":
            if index_data:
                sql = f"select * from `amazon_form`.`male_sku` where `本地品名` like '%{index_data}%'"
            else:
                sql = "select * from `amazon_form`.`list_local_sku`"
                self.cursor.execute(sql)
                result = self.cursor.fetchall()
                self.sql_close()
                if result:
                    list_data = []
                    for i in result:
                        list_data.append([i['本地品名']])
                    return list_data, 1
                else:
                    return False, 0
        else:
            if index_data:
                sql = f"select * from `amazon_form`.`male_sku` where `SKU` like '%{index_data}%'"
            else:
                sql = "select * from `amazon_form`.`male_sku`"
        self.cursor.execute(sql)
        result = self.cursor.fetchall()
        self.sql_close()
        if result:
            list_data = []
            for i in result:
                list_data.append([i['本地品名'], i['SKU']])
            return list_data, 0
        else:
            return False, 0
