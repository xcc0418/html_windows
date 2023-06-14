import requests
import pymysql
import re
import openpyxl
import datetime
import json
import hashlib
import urllib
import base64
from Crypto.Cipher import AES
import time


class Upload_Image():
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
        login_msg = self.s.post(login_url, headers=headers, data=data)
        # print(json.loads(login_msg.text))
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

    def get_list_name(self):
        self.sql()
        sql = "select * from `data_read`.`product_read` where `状态` = '无图片链接'"
        self.cursor.execute(sql)
        result = self.cursor.fetchall()
        list_name = []
        self.sql_close()
        for i in result:
            if i['本地品名'] in list_name:
                continue
            list_name.append(i['本地品名'])
        print(len(list_name))
        return list_name

    def get_sql_sku(self):
        self.sql()
        sql1 = "select * from `data_read`.`product_image` where `状态` = '无图片链接'"
        self.cursor.execute(sql1)
        result1 = self.cursor.fetchall()
        list_msg = []
        for i in result1:
            list_msg.append([i['本地品名'], i['SKU'], i['品名'], i['状态']])
        # self.write_excl(list_msg)
        list_msg.sort(key=lambda d: (d[0], d[3]))
        print(len(list_msg))
        return list_msg

    def write_excl(self, list_msg):
        wb = openpyxl.Workbook()
        wb_sheet = wb.active
        wb_sheet.append(['本地品名', 'SKU', '品名'])
        for i in list_msg:
            wb_sheet.append(i)
        wb.save('SKU无图片连接信息.xlsx')

    def get_class_sku(self, index, index_data):
        # list_msg = self.find_msg(index, index_data)
        print(index, index_data)
        list_msg = []
        self.sql()
        if index == 'SKU':
            sql = f"select * from `data_read`.`product_image` where `状态` = '无图片链接' and `SKU` like '%{index_data}%'"
        else:
            sql = f"select * from `data_read`.`product_image` where `状态` = '无图片链接' and `本地品名` like '%{index_data}%'"
        self.cursor.execute(sql)
        result = self.cursor.fetchall()
        if result:
            for i in result:
                list_msg.append([i['本地品名'], i['SKU'], i['品名'], i['状态']])
        print(len(list_msg))
        self.sql_close()
        list_msg.sort(key=lambda d: (d[0], d[3]))
        return list_msg

    def get_image_msg(self, male_name):
        self.sql()
        sql1 = "select * from `data_read`.`product_image` where `状态` = '有图片链接' and `本地品名` = '%s'" % male_name
        self.cursor.execute(sql1)
        result1 = self.cursor.fetchall()
        list_msg = []
        for i in result1:
            list_msg.append([i['本地品名'], i['SKU'], i['品名'], i['状态']])
        return list_msg

    def find_msg(self, index, index_data):
        self.sql()
        if index == 'SKU':
            sql = "select * from `data_read`.`product_image` where `SKU` like '%s'" % index_data
        else:
            sql = "select * from `data_read`.`product_image` where `本地品名` like '%s'" % index_data
        self.cursor.execute(sql)
        result = self.cursor.fetchall()
        self.sql_close()
        print(len(result))
        list_msg = []
        for i in result:
            list_msg.append([i['本地品名'], i['SKU'], i['品名'], i['状态']])
        # self.write_excl(list_msg)
        list_msg.sort(key=lambda d: d[0])
        print(len(list_msg))
        return list_msg

    def change_sql(self, list_sku):
        self.sql()
        flag = 0
        for i in list_sku:
            sql = "update `data_read`.`product_id` set `图片状态` = '已上传图片连接' where `SKU` = '%s'" % i
            self.cursor.execute(sql)
            flag += 1
            if flag % 100 == 0:
                self.connection.commit()
        self.connection.commit()
        self.sql_close()

    def get_image_link(self, index, index_data):
        if index == 'SKU':
            sql = "select * from `amazon_form`.`male_sku` where `SKU` = '%s'" % index_data
            self.cursor.execute(sql)
            result = self.cursor.fetchall()
            index_data = result[0]['本地品名']
        self.sql()
        sql1 = "select * from `data_read`.`product_image` where `状态` = '无图片连接'"
        self.cursor.execute(sql1)
        result1 = self.cursor.fetchall()
        sql2 = "select * from `amazon_form`.`male_sku` where `本地品名` like '%s'" % index_data
        self.cursor.execute(sql2)
        result2 = self.cursor.fetchall()
        self.sql_close()
        dict_image = {}
        dict_sku = {}
        list_msg = []
        if result1:
            for i in result1:
                dict_image[i['SKU']] = i['品名']
        if result2:
            for i in result2:
                dict_sku[i['SKU']] = i['本地品名']
        for i in dict_sku:
            if i in dict_image:
                list_msg.append([dict_sku[i], i, dict_image[i], 0])
            else:
                list_msg.append([dict_sku[i], i, dict_image[i], 1])
        return list_msg

    def upload_image(self, list_sku):
        list_error = []
        list_success = []
        for i in range(0, len(list_sku)):
            sku = list_sku[i]
            list_msku = self.get_msku(sku)
            for j in list_msku:
                msg = self.upload(j)
                if msg:
                    list_success.append(sku)
                else:
                    list_error.append(sku)
        self.update_sql(list_success)
        if list_error:
            str_msg = ''
            for i in list_error:
                str_msg = f"{str_msg}{i}同步失败, "
            msg = f"{str_msg}其余关联成功。"
            return False, msg
        else:
            return True, True

    def upload(self, list_msg):
        try:
            msku = list_msg[0]
            store_id = list_msg[1]
            product_id = list_msg[2]
            language_tag = self.get_language_tag(store_id, msku)
            main_url, list_url = self.get_picture_url(product_id)
            if store_id and language_tag and main_url:
                data = {"store_id": store_id, "msku": f"{msku}", "is_item_name_required": 0,
                        "is_product_description_required": 0, "is_bullet_point_required": 0,
                        "is_generic_keyword_required": 0, "is_image_required": 1,
                        "main_product_image_locator": main_url,
                        "init_other_product_image_count": 0, "other_product_image_locator": list_url,
                        "init_switch_product_image_locator": "", "swatch_product_image_locator": "",
                        "item_name": {"language_tag": language_tag, "value": ""},
                        "generic_keyword": {"language_tag": language_tag, "value": ""},
                        "bullet_point": [{"language_tag": language_tag, "value": ""}],
                        "product_description": {"language_tag": language_tag, "value": ""},
                        "req_time_sequence": "/listing-publish-api/api/AmazonPublishProduct/listingUpdate$$2"}
                post_data = json.dumps(data)
                post_url = "https://gw.lingxingerp.com/listing-publish-api/api/AmazonPublishProduct/listingUpdate"
                post_headers = {'Host': 'gw.lingxingerp.com',
                                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:95.0) Gecko/20100101 Firefox/95.0'
                                , 'Referer': 'https://erp.lingxing.com',
                                'auth-token': self.auth_token,
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
                post_msg = self.s.post(url=post_url, headers=post_headers, data=post_data)
                post_msg = json.loads(post_msg.text)
                if post_msg['code'] == 1 and post_msg['msg'] == '成功':
                    print(post_msg)
                    return True
                else:
                    print(post_msg)
                    return False
            else:
                print(store_id, product_id, main_url, list_url, language_tag)
                return False
        except Exception as e:
            print(e)
            return False

    def get_product_id(self, sku):
        self.sql()
        sql = "select * from `data_read`.`product_id` where `SKU` = '%s'" % sku
        # print(sql)
        self.cursor.execute(sql)
        result = self.cursor.fetchall()
        if result:
            self.sql_close()
            return result[0]['ID']
        else:
            self.sql_close()
            return False

    def find_store(self, msku):
        post_url = "https://gw.lingxingerp.com/listing-api/api/product/showOnline"
        post_headers = {'Host': 'gw.lingxingerp.com',
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:95.0) Gecko/20100101 Firefox/95.0'
                        , 'Referer': 'https://erp.lingxing.com',
                        'auth-token': self.auth_token,
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
        data = {}
        data['fulfillment_channel_type'] = ''
        data['is_pair'] = ''
        data['length'] = 200
        data['offset'] = 0
        data['req_time_sequence'] = '/listing-api/api/product/showOnline$$'
        data['search_field'] = 'msku'
        data['search_value'] = []
        data['search_value'].append(msku)
        data['sids'] = ''
        data['status'] = ''
        # print(data)
        data = json.dumps(data)
        post_msg = self.s.post(post_url, headers=post_headers, data=data)
        post_msg = json.loads(post_msg.text)
        # print(post_msg)
        # print(msku)
        if post_msg['code'] == 1 and post_msg['msg'] == '成功' and post_msg['data']['list']:
            for i in post_msg['data']['list']:
                # msku_ = i['msku'].strip()
                if i['msku'] == msku:
                    # print(i['fnsku'])
                    return i['store_id']
                else:
                    print(i['msku'])
            return False
        return False

    def get_picture_url(self, product_id):
        if product_id:
            get_url = f"https://erp.lingxing.com/api/module/product/product.picture/getProductPictures?" \
                      f"product_id={product_id}&req_time_sequence=/api/module/product/product.picture/getProductPictures$$3"
            get_headers = {'Host': 'erp.lingxing.com',
                           'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/112.0'
                           , 'Referer': 'https://erp.lingxing.com/erp/listing',
                           'Accept': 'application/json, text/plain, */*',
                           'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
                           'Accept-Encoding': 'gzip, deflate, br', 'Content-Type': 'application/json;charset=utf-8',
                           'X-AK-Request-Id': 'e7f7b81a-fafd-4031-8964-00376ae24d07',
                           'X-AK-Company-Id': '90136229927150080', 'X-AK-Request-Source': 'erp',
                           'X-AK-ENV-KEY': 'SAAS-10', 'X-AK-Version': '1.0.0.0.0.023', 'X-AK-Zid': '109810',
                           'Sec-Fetch-Site': 'cross-site', 'Sec-Fetch-Dest': 'empty',
                           'Sec-Fetch-Mode': 'cors', 'Connection': 'keep-alive'}
            get_msg = self.s.get(get_url, headers=get_headers)
            get_msg = json.loads(get_msg.text)
            if get_msg['code'] == 1 and get_msg['msg'] == '操作成功':
                main_url = ''
                list_url = []
                for i in get_msg['list']:
                    if i['pic_name'] == '1.jpg':
                        main_url = i['pic_url']
                    else:
                        list_url.append(i['pic_url'])
                return main_url, list_url
            else:
                return False, False
        else:
            return False, False

    def get_language_tag(self, store_id, msku):
        marketplace_id = self.get_marketplace_id(store_id)
        if marketplace_id:
            get_url = f"https://gw.lingxingerp.com/listing-publish-api/api/AmazonListingInfo/getListingInfo?" \
                      f"store_id={store_id}&msku={msku}&marketplace_id={marketplace_id}" \
                      f"&req_time_sequence=/listing-publish-api/api/AmazonListingInfo/getListingInfo$$"
            get_headers = {'Host': 'gw.lingxingerp.com',
                           'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/112.0'
                           , 'Referer': 'https://erp.lingxing.com',
                           'auth-token': self.auth_token,
                           'Accept': 'application/json, text/plain, */*',
                           'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
                           'Accept-Encoding': 'gzip, deflate, br',
                           'Content-Type': 'application/json;charset=utf-8',
                           'X-AK-Request-Id': 'e7f7b81a-fafd-4031-8964-00376ae24d07',
                           'X-AK-Company-Id': '90136229927150080',
                           'X-AK-Request-Source': 'erp',
                           'X-AK-ENV-KEY': 'SAAS-10',
                           'X-AK-Version': '3.1.6.3.0.008',
                           'X-AK-Zid': '109810',
                           'Origin': 'https://erp.lingxing.com',
                           'Connection': 'keep-alive', 'Sec-Fetch-Site': 'cross-site', 'TE': 'trailers',
                           'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors'
                           }
            # print(store_id, self.auth_token)
            get_msg = self.s.get(get_url, headers=get_headers)
            get_msg = json.loads(get_msg.text)
            # print(get_msg)
            if get_msg['code'] == 1 and get_msg['msg'] == '成功':
                return get_msg['data']['default_language_tag']
            else:
                return False
        else:
            return False

    def get_marketplace_id(self, store_id):
        self.sql()
        sql = "select * from `data_read`.`seller` where `店铺ID` = '%s'" % store_id
        self.cursor.execute(sql)
        result = self.cursor.fetchall()
        self.sql_close()
        if result:
            return result[0]['市场ID']
        else:
            return False

    def get_msku(self, sku):
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
        self.auth_token = auth_token
        post_url = 'https://gw.lingxingerp.com/listing-api/api/product/showOnline'
        post_headers = {'Host': 'gw.lingxingerp.com',
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:95.0) Gecko/20100101 Firefox/95.0'
                        , 'Referer': 'https://erp.lingxing.com',
                        'auth-token': self.auth_token,
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
                        'Content-Length': '241',
                        'Origin': 'https://erp.lingxing.com',
                        'Connection': 'keep-alive'}
        data = {"offset": 0, "length": 400, "search_field": "local_sku", "search_value": [f"{sku}"], "exact_search": 0,
                "sids": "", "status": "", "is_pair": "", "fulfillment_channel_type": "", "global_tag_ids": "",
                "req_time_sequence": "/listing-api/api/product/showOnline$$"}
        post_data = json.dumps(data)
        post_msg = self.s.post(url=post_url, headers=post_headers, data=post_data)
        post_msg = json.loads(post_msg.text)
        if post_msg['code'] == 1 and post_msg['msg'] == '成功':
            list_msku = []
            for i in post_msg['data']['list']:
                if i['small_image_url']:
                    continue
                else:
                    list_msku.append([i['msku'], i['store_id'], i['product_id']])
            return list_msku
        else:
            return False

    def update_sql(self, list_sku):
        self.sql()
        flag = 0
        for i in list_sku:
            flag += 1
            sql = "update `data_read`.`product_image` where `SKU` = '%s'" % i
            self.cursor.execute(sql)
            if flag % 100 == 0:
                self.connection.commit()
        self.connection.commit()
        self.sql_close()


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
        print(self.time, self.start_time)

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
        for p in sorted(body):
            # 每次排完序的加到串中
            # if body[p]:
            # str类型需要转化为url编码格式
            if isinstance(body[p], str):
                str_parm = str_parm + str(p) + "=" + str(urllib.parse.quote(body[p])) + "&"
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
            str_value = str(body[p])
            str_value = str_value.replace(" ", "")
            str_value = str_value.replace("'", "\"")
            str_parm = str_parm + str(p) + "=" + str_value + "&"
        # 加上对应的key
        str_parm = str_parm.rstrip('&')
        # print("字符串拼接1:", str_parm)
        if isinstance(str_parm, str):
            # 如果是unicode先转utf-8
            parmStr = str_parm.encode("utf-8")
            # parmStr = str_parm
            m = hashlib.md5()
            m.update(parmStr)
            md5_sign = m.hexdigest()
            # print(m.hexdigest())
            md5_sign = md5_sign.upper()
            # print("MD5加密:", md5_sign)
        eg = EncryptDate(apikey)  # 这里密钥的长度必须是16的倍数
        res = eg.encrypt(md5_sign)
        # print("AES加密:", res)
        # print(eg.decrypt(res))
        return res

    def get_product_id(self):
        time_stamp = int(time.time())
        url = "https://openapi.lingxing.com/erp/sc/routing/data/local_inventory/productList"
        body = {"access_token": self.access_token,
                "timestamp": time_stamp,
                "app_key": "ak_nEfE94OSogf3x", "offset": 0, "length": 1000, "create_time_start": 1514736000,
                "create_time_end": time_stamp
                }
        # "wid": "2156,1489,2382,1490,1461,1488,1476,1477,1399,1478,414", "offset": 0, "length": 400
        res = self.get_sign(body)
        # res = ''
        querystring = {"access_token": self.access_token,
                       "timestamp": time_stamp,
                       "app_key": self.app_id,
                       "sign": res
                       }
        payload = {"offset": 0, "length": 1000, "create_time_start": 1514736000, "create_time_end": time_stamp}
        payload = json.dumps(payload)
        headers = {
            "Content-Type": "application/json",
            "Authorization": "bearer {{access_token}}"
        }
        response = requests.request("POST", url, data=payload, headers=headers, params=querystring)
        result1 = json.loads(response.text)
        print(result1['total'])
        dict_id = {}
        for i in result1['data']:
            pic_index = '无图片连接'
            if i['pic_url']:
                pic_index = '有图片连接'
            supplier_name = ''
            for k in i['supplier_quote']:
                if k['is_primary'] == 1:
                    supplier_name = k['supplier_name']
            dict_id[i['id']] = [i['sku'], i['product_name'], supplier_name, pic_index]
        flag = int(result1['total'] / 1000)
        print(flag)
        for i in range(1, flag+1):
            body['offset'] = i*1000
            res = self.get_sign(body)
            querystring['sign'] = res
            payload = {"offset": i*1000, "length": 1000, "create_time_start": 1514736000, "create_time_end": time_stamp}
            payload = json.dumps(payload)
            response = requests.request("POST", url, data=payload, headers=headers, params=querystring)
            result1 = json.loads(response.text)
            for j in result1['data']:
                pic_index = '无图片连接'
                if j['pic_url']:
                    pic_index = '有图片连接'
                if j['id'] in dict_id:
                    continue
                else:
                    supplier_name = ''
                    for k in j['supplier_quote']:
                        if k['is_primary'] == 1:
                            supplier_name = k['supplier_name']
                    dict_id[j['id']] = [j['sku'], j['product_name'], supplier_name, pic_index]
        print(len(dict_id))
        self.write_sql(dict_id)

    def write_sql(self, dict_id):
        self.sql()
        sql1 = "TRUNCATE TABLE `data_read`.`product_id`"
        sql3 = "TRUNCATE TABLE `data_read`.`product_image`"
        self.cursor.execute(sql1)
        self.cursor.execute(sql3)
        self.connection.commit()
        self.sql_close()
        time.sleep(5)
        self.sql()
        flag = 0
        for i in dict_id:
            # print(dict_id[i])
            sql2 = "insert into `data_read`.`product_id`(`SKU`,`品名`,`供应商`, `ID`, `图片状态`) VALUES ('%s','%s','%s',%d, '%s')" % (dict_id[i][0], dict_id[i][1], dict_id[i][2], i, dict_id[i][3])
            self.cursor.execute(sql2)
            flag += 1
            if flag % 100 == 0:
                self.connection.commit()
        self.connection.commit()
        self.sql_close()
        self.get_sql_sku()

    def get_sql_sku(self):
        self.sql()
        sql1 = "select * from `data_read`.`product_id`"
        self.cursor.execute(sql1)
        result1 = self.cursor.fetchall()
        sql2 = "select * from `amazon_form`.`male_sku`"
        self.cursor.execute(sql2)
        result2 = self.cursor.fetchall()
        # self.sql_close()
        dict_msg = {}
        dict_image = {}
        dict_sku = {}
        list_msg = []
        list_link = []
        if result1:
            for i in result1:
                dict_image[i['SKU']] = [i['品名'], i['图片状态']]
        if result2:
            for i in result2:
                dict_sku[i['SKU']] = i['本地品名']
        print(len(dict_image), len(dict_sku))
        for i in dict_sku:
            if i in dict_image:
                if dict_image[i][1] == "无图片连接":
                    if dict_sku[i] in dict_msg:
                        dict_msg[dict_sku[i]]['无图片连接'].append([dict_sku[i], i, dict_image[i][0], '无图片连接'])
                    else:
                        dict_msg[dict_sku[i]] = {'无图片连接': [], '有图片连接': []}
                        dict_msg[dict_sku[i]]['无图片连接'] = [[dict_sku[i], i, dict_image[i][0], '无图片连接']]
                else:
                    if dict_sku[i] in dict_msg:
                        dict_msg[dict_sku[i]]['有图片连接'].append([dict_sku[i], i, dict_image[i][0], '有图片连接'])
                    else:
                        dict_msg[dict_sku[i]] = {'无图片连接': [], '有图片连接': []}
                        dict_msg[dict_sku[i]]['有图片连接'] = [[dict_sku[i], i, dict_image[i][0], '有图片连接']]
            else:
                print(i)
        # print(len(dict_msg), len(list_link))
        for i in dict_msg:
            list_value = list(dict_msg[i].values())
            for j in list_value:
                for k in j:
                    list_msg.append(k)
        flag = 0
        for i in list_msg:
            sql3 = "insert into `data_read`.`product_image`(`本地品名`, `SKU`,`品名`, `状态`) VALUES ('%s','%s','%s','%s')" % (
            i[0], i[1], i[2], i[3])
            if i[0] == '菜单套-折边对贴-拉链口袋-玫瑰金巴黎之星':
                print(sql3)
            self.cursor.execute(sql3)
            flag += 1
            if flag % 100 == 0:
                self.connection.commit()
        self.connection.commit()
        self.sql_close()
        return list_msg

    def get_flag(self):
        self.sql()
        sql = "select * from `flag`.`amazon_form_flag` where `flag_name` = 'update_image'"
        self.cursor.execute(sql)
        result = self.cursor.fetchall()
        self.sql_close()
        if result[0]['flag_num'] == 0:
            update_time = result[0]['time']
            time_now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            time_now = datetime.datetime.strptime(time_now, '%Y-%m-%d %H:%M:%S')
            time_difference = (time_now - update_time).seconds
            print(time_difference)
            if time_difference > 1800:
                return True
            else:
                return False
        else:
            return False

    def update_flag(self, index):
        self.sql()
        sql = f"update `flag`.`amazon_form_flag` set `flag_num` = {index} where `flag_name` = 'update_image'"
        self.cursor.execute(sql)
        self.cursor.fetchall()
        self.sql_close()

    def update_image_msg(self):
        try:
            self.update_flag(1)
            self.get_product_id()
            self.update_flag(0)
        except Exception as e:
            print('图片信息更新失败：', str(e))
            self.update_flag(0)


if __name__ == '__main__':
    upload = Upload_Image()
    upload.get_class_sku('本地品名', 'Fire10(2021)')
    # upload.upload(['KPW5CS_Brown-11-2301051635-T', '272', 'en_US'])
    # upload.get_sql_sku()
    # quantity = Quantity()
    # quantity.update_msg()
    # quantity.get_sql_sku()
