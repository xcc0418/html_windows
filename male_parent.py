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

    def open_downloads(self):
        self.sql()
        sql = "update `flag`.`amazon_form_flag` set `flag_num` = 1 where `flag_name` = 'parent'"
        self.cursor.execute(sql)
        self.connection.commit()
        self.sql_close()

    def close_downloads(self):
        self.sql()
        sql = "update `flag`.`amazon_form_flag` set `flag_num` = 0 where `flag_name` = 'parent'"
        self.cursor.execute(sql)
        self.connection.commit()
        self.sql_close()

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
                return False, str(e)

    def upload_male(self, filename):
        self.sql()
        sql = "select * from `flag`.`amazon_form_flag` where `flag_name` = 'parent'"
        self.cursor.execute(sql)
        result = self.cursor.fetchall()
        self.sql_close()
        if result[0]['flag_num'] == 0:
            try:
                list_error = []
                self.open_downloads()
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
                        if msg or message == "已经有这个本地父体了，请检查":
                            continue
                        else:
                            list_error.append(male_parent)
                        wb_sheet.cell(row=i, column=2).value = message
                wb.save(filename)
                self.close_downloads()
                if list_error:
                    msg = ''
                    for i in list_error:
                        msg = f"{msg}{i}添加失败, "
                    msg = f"{msg}其余添加成功。"
                    return False, msg
                return True, True
            except Exception as e:
                print(e)
                self.close_downloads()
                return False, str(e)
        else:
            return False, "当前正在进行添加操作，请稍后再试"

    def upload_sku(self, filename):
        self.sql()
        sql = "select * from `flag`.`amazon_form_flag` where `flag_name` = 'parent'"
        self.cursor.execute(sql)
        result = self.cursor.fetchall()
        self.sql_close()
        if result[0]['flag_num'] == 0:
            try:
                list_error = []
                self.open_downloads()
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
                        # print(message)
                        if msg or message == "已经有这个本地品名了，请检查":
                            continue
                        else:
                            list_error.append(male_sku)
                        wb_sheet.cell(row=i, column=2).value = message
                wb.save(filename)
                self.close_downloads()
                if list_error:
                    msg = ''
                    for i in list_error:
                        msg = f"{msg}{i}添加失败, "
                    msg = f"{msg}其余添加成功。"
                    return False, msg
                return True, True
            except Exception as e:
                print(e)
                self.close_downloads()
                return False, str(e)
        else:
            return False, "当前正在进行添加操作，请稍后再试"

    def upload_parent(self, filename):
        self.sql()
        sql = "select * from `flag`.`amazon_form_flag` where `flag_name` = 'parent'"
        self.cursor.execute(sql)
        result = self.cursor.fetchall()
        self.sql_close()
        if result[0]['flag_num'] == 0:
            try:
                list_error = []
                self.open_downloads()
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
                        sku = wb_sheet.cell(row=i, column=2).value
                        if sku:
                            msg, message = self.relevance_male(male_parent, sku)
                            if not msg:
                                list_error.append([male_parent, sku])
                        else:
                            male_sku = wb_sheet.cell(row=i, column=3).value
                            list_sku, message = self.get_male_sku("本地品名", male_sku)
                            if list_sku:
                                flag = 1
                                for j in list_sku:
                                    sku = j[1]
                                    msg, message = self.relevance_male(male_parent, sku)
                                    if msg:
                                        continue
                                    else:
                                        flag = 0
                                if flag:
                                    message = "关联成功"
                                else:
                                    list_error.append([male_parent, sku])
                                    message = "关联失败"
                            else:
                                message = "没有找到这个本地品名"
                        wb_sheet.cell(row=i, column=3).value = message
                time_now = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
                wb.save(f'./static/本地父体/关联本地父体_{time_now}.xlsx')
                self.close_downloads()
                if list_error:
                    msg = ''
                    for i in list_error:
                        msg = f"{msg}{i[0]}与{i[1]}关联失败, "
                    msg = f"{msg}其余关联成功。"
                    return False, msg
                return True, True
            except Exception as e:
                self.close_downloads()
                return False, str(e)
        else:
            return False, "当前正在进行关联操作，请稍后再试"

    def upload_name(self, filename):
        self.sql()
        sql = "select * from `flag`.`amazon_form_flag` where `flag_name` = 'parent'"
        self.cursor.execute(sql)
        result = self.cursor.fetchall()
        self.sql_close()
        if result[0]['flag_num'] == 0:
            try:
                list_error = []
                list_success = []
                self.open_downloads()
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
                    if msg:
                        list_success.append([sku, male_parent])
                    else:
                        list_error.append([male_parent, sku])
                    wb_sheet.cell(row=i, column=3).value = message
                if list_success:
                    self.add_image_msg(list_success)
                time_now = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
                wb.save(f'./static/本地品名/关联本地品名_{time_now}.xlsx')
                self.close_downloads()
                if list_error:
                    msg = ''
                    for i in list_error:
                        msg = f"{msg}{i[0]}与{i[1]}关联失败, "
                    msg = f"{msg}其余关联成功。"
                    return False, msg
                return True, True
            except Exception as e:
                print(e)
                self.close_downloads()
                return False, str(e)
        else:
            return False, "当前正在进行关联操作，请稍后再试"

    def add_image_msg(self, list_sku):
        self.sql()
        for i in list_sku:
            sql1 = "select * from `data_read`.`product_id` where `SKU` = '%s'" % i[0]
            self.cursor.execute(sql1)
            result = self.cursor.fetchall()
            name = '暂无品名'
            values = '无图片链接'
            if result:
                name = result[0]['品名']
                values = result[0]['图片状态']
            sql2 = "insert into `data_read`.`product_image`(`本地品名`, `SKU`,`品名`, `状态`) VALUES ('%s','%s','%s','%s')" % (
                i[1], i[0], name, values)
            self.cursor.execute(sql2)
        self.connection.commit()
        self.sql_close()

    def delete_image_msg(self, list_sku):
        self.sql()
        for i in list_sku:
            sql1 = "DELETE FROM `data_read`.`product_image` where `SKU` = '%s'" % i[0]
            self.cursor.execute(sql1)
        self.connection.commit()
        self.sql_close()

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
                return False, str(e)

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
                print(f"{male_parent}与{sku}已关联")
                return False, f"{male_parent}与{sku}已关联"
            else:
                sql2 = "select * from `amazon_form`.`male_sku` where `SKU` = '%s'" % sku
                self.cursor.execute(sql2)
                result1 = self.cursor.fetchall()
                if result1:
                    sql3 = "select * from `amazon_form`.`male_sku` where `本地品名` = '%s'" % result1[0]['本地品名']
                    self.cursor.execute(sql3)
                    result2 = self.cursor.fetchall()
                    for i in result2:
                        sql5 = "select * from `amazon_form`.`male_parent` where `本地父体` = '%s' and `SKU` = '%s'" % (male_parent, i['SKU'])
                        self.cursor.execute(sql5)
                        result = self.cursor.fetchall()
                        if result:
                            continue
                        else:
                            sql4 = "insert into `amazon_form`.`male_parent`(`本地父体`, `SKU`)values('%s', '%s')" % (male_parent, i['SKU'])
                            self.cursor.execute(sql4)
                else:
                    sql3 = "select * from `amazon_form`.`male_sku` where `本地品名` = '%s'" % sku
                    self.cursor.execute(sql3)
                    result2 = self.cursor.fetchall()
                    if result2:
                        for i in result2:
                            sql4 = "insert into `amazon_form`.`male_parent`(`本地父体`, `SKU`)values('%s', '%s')" % (male_parent, i['SKU'])
                            self.cursor.execute(sql4)
                    else:
                        sql1 = "insert into `amazon_form`.`male_parent`(`本地父体`, `SKU`)values('%s', '%s')" % (male_parent, sku)
                        self.cursor.execute(sql1)
                try:
                    self.connection.commit()
                    return True, '成功'
                except Exception as e:
                    # print(e)
                    self.connection.rollback()
                    return False, str(e)
        else:
            self.sql_close()
            # print(f"没有{male_parent}这个本地父体，请检查")
            return False, f"没有{male_parent}这个本地父体，请检查"

    def relieve_male(self, male_parent, sku):
        self.sql()
        sql = "select * from `amazon_form`.`male_parent` where `本地父体` = '%s' and `SKU` = '%s'" % (male_parent, sku)
        self.cursor.execute(sql)
        result = self.cursor.fetchall()
        sql = "select * from `amazon_form`.`male_sku` where `本地品名` = '%s'" % sku
        self.cursor.execute(sql)
        result3 = self.cursor.fetchall()
        if result or result3:
            if result:
                sql2 = "select * from `amazon_form`.`male_sku` where `SKU` = '%s'" % sku
            else:
                sql2 = "select * from `amazon_form`.`male_sku` where `本地品名` = '%s'" % sku
            self.cursor.execute(sql2)
            result1 = self.cursor.fetchall()
            if result1:
                sql3 = "select * from `amazon_form`.`male_sku` where `本地品名` = '%s'" % result1[0]['本地品名']
                self.cursor.execute(sql3)
                result2 = self.cursor.fetchall()
                for i in result2:
                    sql4 = "DELETE FROM `amazon_form`.`male_parent` WHERE `本地父体` = '%s' and `SKU` = '%s'" % (male_parent, i['SKU'])
                    self.cursor.execute(sql4)
            else:
                sql1 = "DELETE FROM `amazon_form`.`male_parent` WHERE `本地父体` = '%s' and `SKU` = '%s'" % (male_parent, sku)
                self.cursor.execute(sql1)
            try:
                self.connection.commit()
                self.sql_close()
                return True, '成功'
            except Exception as e:
                self.connection.rollback()
                self.sql_close()
                return False, str(e)
        else:
            self.sql_close()
            return False, "这个父体与sku没有相关信息"

    def relevance_sku(self, local_sku, sku):
        self.sql()
        sql = "select * from `amazon_form`.`list_local_sku` where `本地品名` = '%s'" % local_sku
        self.cursor.execute(sql)
        result = self.cursor.fetchall()
        if result:
            sql = "select * from `amazon_form`.`male_sku` where `SKU` = '%s'" % sku
            self.cursor.execute(sql)
            result = self.cursor.fetchall()
            if result:
                self.sql_close()
                return False, f"{result[0]['本地品名']}与{sku}已关联"
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
                    return False, str(e)
        else:
            self.sql_close()
            return False, f"没有{local_sku}这个本地品名，请检查"

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
                return False, str(e)
        else:
            self.sql_close()
            return False, "这个父体与sku没有相关信息"

    def relevance_amazon(self, male_parent, amazon_parent):
        self.sql()
        sql1 = "select * from `amazon_form`.`list_parent` where `本地父体` = '%s'" % male_parent
        self.cursor.execute(sql1)
        result1 = self.cursor.fetchall()
        # print(sql1)
        if result1:
            sql2 = "select * from `amazon_form`.`male_amazon` where `本地父体` = '%s' and `亚马逊父体` = '%s'" % (male_parent, amazon_parent)
            self.cursor.execute(sql2)
            result2 = self.cursor.fetchall()
            if result2:
                self.sql_close()
                return False, f'{male_parent}与{amazon_parent}已关联'
            else:
                try:
                    sql3 = "insert into `amazon_form`.`male_amazon`(`本地父体`, `亚马逊父体`)values('%s', '%s')" % (male_parent, amazon_parent)
                    self.cursor.execute(sql3)
                    self.connection.commit()
                    self.sql_close()
                    return True, True
                except Exception as e:
                    self.connection.rollback()
                    self.sql_close()
                    return False, str(e)
        else:
            return False, f'没有{male_parent}，请检查'

    def relieve_amazon(self, male_parent, amazon_parent):
        self.sql()
        sql1 = "select * from `amazon_form`.`male_amazon` where `本地父体` = '%s' and `亚马逊父体` = '%s'" % (male_parent, amazon_parent)
        self.cursor.execute(sql1)
        result1 = self.cursor.fetchall()
        if result1:
            try:
                sql2 = "DELETE FROM `amazon_form`.`male_amazon` WHERE `本地父体` = '%s' and `亚马逊父体` = '%s'" % (male_parent, amazon_parent)
                self.cursor.execute(sql2)
                self.connection.commit()
                self.sql_close()
                return True, True
            except Exception as e:
                self.connection.rollback()
                self.sql_close()
                return False, str(e)
        else:
            return False, f"{male_parent}与{amazon_parent}没有关联信息，请检查"

    def upload_relieve_male(self, filename):
        self.sql()
        sql = "select * from `flag`.`amazon_form_flag` where `flag_name` = 'parent'"
        self.cursor.execute(sql)
        result = self.cursor.fetchall()
        self.sql_close()
        if result[0]['flag_num'] == 0:
            try:
                list_error = []
                self.open_downloads()
                wb = openpyxl.load_workbook(filename)
                wb_sheet = wb.active
                row1 = wb_sheet.max_row
                for i in range(row1, 0, -1):
                    cell_value1 = wb_sheet.cell(row=i, column=1).value
                    if cell_value1:
                        row1 = i
                        break
                for i in range(2, row1 + 1):
                    male_parent = wb_sheet.cell(row=i, column=1).value
                    sku = wb_sheet.cell(row=i, column=2).value
                    if sku:
                        msg, message = self.relieve_male(male_parent, sku)
                    else:
                        male_sku = wb_sheet.cell(row=i, column=3).value
                        list_sku, message = self.get_male_sku("本地品名", male_sku)
                        if list_sku:
                            flag = 1
                            for j in list_sku:
                                sku = j[1]
                                msg, message = self.relieve_male(male_parent, sku)
                                if msg:
                                    continue
                                else:
                                    flag = 0
                            if flag:
                                message = "解除成功"
                            else:
                                list_error.append([male_parent, sku])
                                message = "解除失败"
                        else:
                            message = "没有找到这个本地品名"
                    wb_sheet.cell(row=i, column=3).value = message
                time_now = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
                wb.save(f'./static/本地父体/解除本地父体关联_{time_now}.xlsx')
                self.close_downloads()
                if list_error:
                    msg = ''
                    for i in list_error:
                        msg = f"{msg}{i[0]}与{i[1]}解除关联失败, "
                    msg = f"{msg}其余解除关联成功。"
                    return False, msg
                return True, True
            except Exception as e:
                print(e)
                self.close_downloads()
                return False, str(e)
        else:
            return False, "当前正在进行关联操作，请稍后再试"

    def upload_relieve_sku(self, filename):
        self.sql()
        sql = "select * from `flag`.`amazon_form_flag` where `flag_name` = 'parent'"
        self.cursor.execute(sql)
        result = self.cursor.fetchall()
        self.sql_close()
        if result[0]['flag_num'] == 0:
            try:
                list_error = []
                list_succes = []
                self.open_downloads()
                wb = openpyxl.load_workbook(filename)
                wb_sheet = wb.active
                row1 = wb_sheet.max_row
                for i in range(row1, 0, -1):
                    cell_value1 = wb_sheet.cell(row=i, column=1).value
                    if cell_value1:
                        row1 = i
                        break
                for i in range(2, row1 + 1):
                    male_parent = wb_sheet.cell(row=i, column=1).value
                    sku = wb_sheet.cell(row=i, column=2).value
                    msg, message = self.relieve_sku(male_parent, sku)
                    if msg:
                        list_succes.append([sku, male_parent])
                    else:
                        list_error.append([male_parent, sku])
                    wb_sheet.cell(row=i, column=3).value = message
                if list_succes:
                    self.delete_image_msg(list_succes)
                time_now = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
                wb.save(f'./static/本地品名/解除本地品名关联_{time_now}.xlsx')
                self.close_downloads()
                if list_error:
                    msg = ''
                    for i in list_error:
                        msg = f"{msg}{i[0]}与{i[1]}解除关联失败, "
                    msg = f"{msg}其余解除关联成功。"
                    return False, msg
                return True, True
            except Exception as e:
                print(e)
                self.close_downloads()
                return False, str(e)
        else:
            return False, "当前正在进行关联操作，请稍后再试"

    def delete_male(self, male_parent):
        self.sql()
        sql = "select * from `amazon_form`.`list_parent` where `本地父体` = '%s'" % male_parent
        self.cursor.execute(sql)
        result = self.cursor.fetchall()
        if result:
            sql1 = "DELETE FROM `amazon_form`.`male_parent` WHERE `本地父体` = '%s'" % male_parent
            sql2 = "DELETE FROM `amazon_form`.`list_parent` WHERE `本地父体` = '%s'" % male_parent
            try:
                self.cursor.execute(sql1)
                self.cursor.execute(sql2)
                self.connection.commit()
                self.sql_close()
                return True, True
            except Exception as e:
                self.connection.rollback()
                self.sql_close()
                return False, str(e)
        else:
            self.sql_close()
            return False, f"没有{male_parent}这个父体"

    def delete_sku(self, male_parent):
        self.sql()
        sql = "select * from `amazon_form`.`list_local_sku` where `本地品名` = '%s'" % male_parent
        self.cursor.execute(sql)
        result = self.cursor.fetchall()
        if result:
            sql1 = "DELETE FROM `amazon_form`.`male_sku` WHERE `本地品名` = '%s'" % male_parent
            sql2 = "DELETE FROM `amazon_form`.`list_local_sku` WHERE `本地品名` = '%s'" % male_parent
            try:
                self.cursor.execute(sql1)
                self.cursor.execute(sql2)
                self.connection.commit()
                self.sql_close()
                return True, True
            except Exception as e:
                self.connection.rollback()
                self.sql_close()
                return False, str(e)
        else:
            self.sql_close()
            return False, f"没有{male_parent}这个父体"

    def upload_delete_male(self, filename):
        self.sql()
        sql = "select * from `flag`.`amazon_form_flag` where `flag_name` = 'parent'"
        self.cursor.execute(sql)
        result = self.cursor.fetchall()
        self.sql_close()
        if result[0]['flag_num'] == 0:
            try:
                list_error = []
                self.open_downloads()
                wb = openpyxl.load_workbook(filename)
                wb_sheet = wb.active
                row1 = wb_sheet.max_row
                for i in range(row1, 0, -1):
                    cell_value1 = wb_sheet.cell(row=i, column=1).value
                    if cell_value1:
                        row1 = i
                        break
                for i in range(2, row1 + 1):
                    male_parent = wb_sheet.cell(row=i, column=1).value
                    msg, message = self.delete_male(male_parent)
                    if msg:
                        continue
                    else:
                        list_error.append(i)
                    wb_sheet.cell(row=i, column=3).value = message
                time_now = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
                wb.save(f'./static/本地父体/删除本地父体_{time_now}.xlsx')
                self.close_downloads()
                if list_error:
                    msg = ''
                    for i in list_error:
                        msg = f"{msg}{i}删除本失败, "
                    msg = f"{msg}其余删除本成功。"
                    return False, msg
                return True, True
            except Exception as e:
                print(e)
                self.close_downloads()
                return False, str(e)
        else:
            return False, "当前正在进行关联操作，请稍后再试"

    def upload_delete_sku(self, filename):
        self.sql()
        sql = "select * from `flag`.`amazon_form_flag` where `flag_name` = 'parent'"
        self.cursor.execute(sql)
        result = self.cursor.fetchall()
        self.sql_close()
        if result[0]['flag_num'] == 0:
            try:
                list_error = []
                self.open_downloads()
                wb = openpyxl.load_workbook(filename)
                wb_sheet = wb.active
                row1 = wb_sheet.max_row
                for i in range(row1, 0, -1):
                    cell_value1 = wb_sheet.cell(row=i, column=1).value
                    if cell_value1:
                        row1 = i
                        break
                for i in range(2, row1 + 1):
                    male_parent = wb_sheet.cell(row=i, column=1).value
                    msg, message = self.delete_sku(male_parent)
                    if msg:
                        continue
                    else:
                        list_error.append(i)
                    wb_sheet.cell(row=i, column=3).value = message
                time_now = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
                wb.save (f'./static/本地品名/删除本地品名_{time_now}.xlsx')
                self.close_downloads()
                if list_error:
                    msg = ''
                    for i in list_error:
                        msg = f"{msg}{i}删除本失败, "
                    msg = f"{msg}其余删除本成功。"
                    return False, msg
                return True, True
            except Exception as e:
                print(e)
                self.close_downloads()
                return False, str(e)
        else:
            return False, "当前正在进行关联操作，请稍后再试"

    def change_parent(self, parent, change_parent):
        self.sql()
        sql1 = "select * from `amazon_form`.`list_parent` where `本地父体` = '%s'" % parent
        self.cursor.execute(sql1)
        result = self.cursor.fetchall()
        if result:
            sql2 = "UPDATE `amazon_form`.`list_parent` SET `本地父体` = '%s' WHERE `本地父体` = '%s'" % (change_parent, parent)
            sql3 = "UPDATE `amazon_form`.`male_parent` SET `本地父体` = '%s' WHERE `本地父体` = '%s'" % (change_parent, parent)
            try:
                self.cursor.execute(sql2)
                self.cursor.execute(sql3)
                self.connection.commit()
                self.sql_close()
                return True, True
            except Exception as e:
                self.connection.rollback()
                self.sql_close()
                print(e)
                return False, str(e)
        else:
            self.sql_close()
            return False, f'没有找到{parent}, 请检查'

    def change_sku(self, sku, change_sku):
        self.sql()
        sql1 = "select * from `amazon_form`.`list_local_sku` where `本地品名` = '%s'" % sku
        self.cursor.execute(sql1)
        result = self.cursor.fetchall()
        if result:
            sql2 = "UPDATE `amazon_form`.`list_local_sku` SET `本地品名` = '%s' WHERE `本地品名` = '%s'" % (change_sku, sku)
            sql3 = "UPDATE `amazon_form`.`male_sku` SET `本地品名` = '%s' WHERE `本地品名` = '%s'" % (change_sku, sku)
            try:
                self.cursor.execute(sql2)
                self.cursor.execute(sql3)
                self.connection.commit()
                self.sql_close()
                return True, True
            except Exception as e:
                self.connection.rollback()
                self.sql_close()
                print(e)
                return False, str(e)
        else:
            self.sql_close()
            return False, f'没有找到{sku}, 请检查'

    def write_xlsx(self, list_data, list_header):
        wb = openpyxl.Workbook()
        wb_sheet = wb.active
        if list_header:
            list_header.insert(0, '本地品名')
            list_header.insert(0, '父体')
            wb_sheet.append(list_header)
        for i in list_data:
            if i[1] and i[1] != '...':
                wb_sheet.append(i)
        time_now = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        if list_data[0][0] == "本地父体":
            path = f'./static/本地父体/本地父体详情_{time_now}.xlsx'
            file = f'../本地父体/本地父体详情_{time_now}.xlsx'
            filename = f'本地父体详情_{time_now}'
            download_name = "本地父体详情"
        elif list_data[0][0] == "本地品名":
            path = f'./static/本地品名/本地品名详情_{time_now}.xlsx'
            file = f'../本地品名/本地品名详情_{time_now}.xlsx'
            filename = f'本地品名详情_{time_now}'
            download_name = "本地品名详情"
        else:
            if list_data[0][0].find('B0') >= 0:
                path = f'./static/本地父体/亚马逊父体详情_{time_now}.xlsx'
                file = f'../本地父体/亚马逊父体详情_{time_now}.xlsx'
                filename = f'亚马逊父体详情_{time_now}'
                download_name = "亚马逊父体详情"
            else:
                path = f'./static/本地父体/本地父体详情_{time_now}.xlsx'
                file = f'../本地父体/本地父体详情_{time_now}.xlsx'
                filename = f'本地父体详情_{time_now}'
                download_name = "本地父体详情"
        wb.save(path)
        return file, filename, download_name

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
        if result:
            dict_sku = self.get_dict_sku ()
            list_data = []
            for i in result:
                if i['SKU'] in dict_sku:
                    list_data.append([i['本地父体'], i['SKU'], dict_sku[i['SKU']]])
                else:
                    list_data.append([i['本地父体'], i['SKU'], '当前没有本地品名'])
            self.sql_close()
            return list_data, 0
        else:
            self.sql_close()
            return False, 0

    def get_dict_sku(self):
        dict_sku = {}
        sql = "select * from `amazon_form`.`male_sku`"
        self.cursor.execute(sql)
        result = self.cursor.fetchall()
        for i in result:
            dict_sku[i['SKU']] = i['本地品名']
        return dict_sku

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

    def read_xlsx(self, filename):
        wb = openpyxl.load_workbook(filename)
        wb_sheet = wb.active
        list_sku = []
        for i in range(2, 400):
            male_parent = wb_sheet.cell(row=i, column=1).value
            if male_parent:
                name = wb_sheet.cell(row=i, column=2).value
                sku = self.get_sku(name)
                if sku:
                    continue
                else:
                    list_sku.append(name)
                    print(name)
        print(list_sku)

    def test_sql(self):
        self.sql()
        sql = "SELECT `SKU` FROM `amazon_form`.`male_parent` WHERE `本地父体` = 'K11-K22父体'"
        self.cursor.execute(sql)
        result = self.cursor.fetchall()
        print(result)
        self.sql_close()

    def get_sku(self, name):
        self.sql()
        sql = "select * from `data_read`.`product_id` where `品名` = '%s'" % name
        # print(sql)
        self.cursor.execute(sql)
        result = self.cursor.fetchall()
        self.sql_close()
        if result:
            return result[0]['SKU']
        else:
            return False


if __name__ == '__main__':
    quantity = Quantity()
    # quantity.read_xlsx("F:/html_windows/static/本地父体/关联本地父体_20230428172405.xlsx")
    quantity.test_sql()
