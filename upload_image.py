import requests
import pymysql
import os
import openpyxl
import datetime
import json


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

    def upload(self, list_msg):
        msku = list_msg[0]
        store_id = list_msg[1]
        product_id = list_msg[2]
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
                list_msku.append([i['msku'], i['store_id'], i['product_id']])
            return list_msku
        else:
            return False


if __name__ == '__main__':
    upload = Upload_Image()
    upload.upload(['KPW5CS_Brown-11-2301051635-T', '272', 'en_US'])
