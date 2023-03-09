import pymysql
import json
import global_var
import datetime
import time
import hashlib
import urllib
import requests
import base64
from Crypto.Cipher import AES
import openpyxl


def get_msg(index, index_data):
    data_msg = []
    if index == '箱号':
        sql = "select * from `storage`.`warehouse` where `箱号` = '%s' and 状态 = '已打包'" % index_data
        result = func(sql)
        for i in result:
            name = func("SELECT `品名` FROM `data_read`.`listing` where `FNSKU`='%s'" % i[1])
            if i[12]:
                msg = {'箱号': i[0], 'fnsku': i[1], '品名': name[0][0], '装箱数量': i[2], '装箱状态': i[11], '装箱位置': i[12]}
            else:
                msg = {'箱号': i[0], 'fnsku': i[1], '品名': name[0][0], '装箱数量': i[2], '装箱状态': i[11], '装箱位置': '这箱还没有匹配位置'}
            data_msg.append(msg)
        return {'data_list': data_msg}
    if index == 'FNSKU':
        sql = "select * from `storage`.`warehouse` where `FNSKU1` = '%s' and 状态 = '已打包'" % index_data
        result = func(sql)
        num_location = 0
        for i in result:
            num_location += int(i[2])
            name = func("SELECT `品名` FROM `data_read`.`listing` where `FNSKU`='%s'" % i[1])
            if i[12]:
                msg = {'箱号': i[0], 'fnsku': i[1], '品名': name[0][0], '装箱数量': i[2], '装箱状态': i[11], '装箱位置': i[12]}
            else:
                msg = {'箱号': i[0], 'fnsku': i[1], '品名': name[0][0], '装箱数量': i[2], '装箱状态': i[11], '装箱位置': '这箱还没有匹配位置'}
            data_msg.append(msg)
        # num_all = find_storage(index_data)
        quantity_msg = Quantity()
        num_all = quantity_msg.get_warehouse_num(index_data)
        return {'库存数量': num_all, '装箱总数量': num_location, 'data_list': data_msg}
    if index == '位置':
        sql = "select * from `storage`.`warehouse` where `存放位置` = '%s' and 状态 = '已打包'" % index_data
        result = func(sql)
        for i in result:
            name = func("SELECT `品名` FROM `data_read`.`listing` where `FNSKU`='%s'" % i[1])
            msg = {'箱号': i[0], 'fnsku': i[1], '品名': name[0][0], '装箱数量': i[2], '装箱状态': i[11], '装箱位置': i[12]}
            data_msg.append(msg)
            # print(msg)
        return {'data_list': data_msg}


def find_storage(fnsku):
    get_url = "https://erp.lingxing.com/api/storage/lists"
    get_headers = {'Host': 'erp.lingxing.com',
                   'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:95.0) Gecko/20100101 Firefox/95.0'
                   , 'Referer': 'https://erp.lingxing.com/erp/msupply/warehouseDetail',
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
    data = {"wid_list": "", "mid_list": "", "sid_list": "", "cid_list": "", "bid_list": "", "principal_list": "",
            "product_type_list": "", "product_attribute": "", "product_status": "", "search_field": "fnsku",
            "search_value": f"{fnsku}", "is_sku_merge_show": 0, "is_hide_zero_stock": 0, "offset": 0,
            "length": 200, "sort_field": "pre_total", "sort_type": "desc", "gtag_ids": "",
            "senior_search_list": "[]", "req_time_sequence": "/api/storage/lists$$"}
    data = json.dumps(data)
    get_msg = global_var.s.post(get_url, headers=get_headers, data=data)
    get_msg = json.loads(get_msg.text)
    num_prepare = 0
    # if sku == '[GCWL]635':
    # print(get_msg)
    # for i in get_msg['list']:
    if get_msg['code'] == 1 and get_msg['msg'] == '操作成功':
        num_prepare = get_msg['data']['total_info']['total']
    # print(num_prepare)
    return num_prepare


def get_warehouse(filename):
    ws = openpyxl.load_workbook(filename)
    ws_sheet = ws.active
    row1 = ws_sheet.max_row
    for i in range(row1, 0, -1):
        cell_value1 = ws_sheet.cell(row=i, column=1).value
        if cell_value1:
            row1 = i
            break
    list_fnsku = []
    for i in range(1, row1+1):
        fnsku = ws_sheet.cell(row=i, column=2).value
        if fnsku:
            if fnsku in list_fnsku:
                continue
            else:
                list_fnsku.append(fnsku)
    list_warehouse = []
    for i in list_fnsku:
        msg = get_po(i)
        list_warehouse.append(msg)
    if list_warehouse:
        wb = openpyxl.Workbook()
        wb_sheet = wb.active
        wb_sheet.append(['品名', 'FNSKU', '箱号信息', '装箱总数量'])
        for i in list_warehouse:
            wb_sheet.append(i)
        starrow1 = 2
        last_cell_value = wb_sheet.cell(row=starrow1, column=2).value
        count = 0
        for q in range(0, row1):
            cell_value = wb_sheet.cell(row=starrow1 + count, column=2).value
            # if q+2 != starrow1 + count:
            #     print("第%s个q，第%d行"%(q,starrow1+count))
            if cell_value == last_cell_value:
                count = count + 1
            else:
                wb_sheet.merge_cells('B%d:B%d' % (starrow1, starrow1 - 1 + count))
                wb_sheet.merge_cells('A%d:A%d' % (starrow1, starrow1 - 1 + count))
                wb_sheet.merge_cells('D%d:D%d' % (starrow1, starrow1 - 1 + count))
                starrow1 = starrow1 + count
                count = 1
                last_cell_value = cell_value
        time_now = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        file = f'F:/html_windows/static/FNSKU装箱信息/{time_now}-箱号.xlsx'
        wb.save(file)
        return file


def get_po(fnsku):
    result = func("SELECT `箱号`, `存放位置`, `数量1` FROM `storage`.`warehouse` WHERE `FNSKU1` = '%s' and `状态` = '已打包'" % fnsku)
    name = func("SELECT `品名` FROM `data_read`.`listing` where `FNSKU`='%s'" % fnsku)
    num = 0
    for i in result:
        num += int(i[2])
    for i in result:
        if i[1]:
            msg = f"箱号：{i[0]}   存放位置：{i[1]}   数量：{i[2]}"
            return [name[0][0], fnsku, msg, num]
        else:
            msg = f"箱号：{i[0]}   存放位置：这箱还没有匹配位置   数量：{i[2]}"
            return [name[0][0], fnsku, msg, num]


def func(sql, m='r'):
    py = pymysql.connect(host='3354n8l084.goho.co', user='test_user', password='a123456', port=24824, db='storage')
    cursor = py.cursor()
    data = None
    # print(sql)
    try:
        cursor.execute(sql)
        if m == 'r':
            data = cursor.fetchall()
        elif m == 'w':
            py.commit()
            data = cursor.rowcount
    except:
        data = False
        py.rollback()
    py.close()
    return data

class Quantity (object):
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
        response = requests.post (url, data=payload, headers=headers, params=querystring)
        result = json.loads (response.text)
        # print(response.text)
        self.access_token = result['data']['access_token']
        self.refresh_token = result['data']['refresh_token']
        self.time = datetime.datetime.now ().strftime ("%Y-%m-%d")
        self.time = datetime.datetime.strptime (self.time, "%Y-%m-%d")
        # self.time = "2021-12-06"
        self.start_time = self.time - datetime.timedelta (days=1)
        self.time = self.time.strftime ("%Y-%m-%d")
        self.start_time = self.start_time.strftime ("%Y-%m-%d")
        # self.start_time = '2022-03-07'
        print (self.time, self.start_time)

    def sql(self):
        self.connection = pymysql.connect (host='3354n8l084.goho.co',  # 数据库地址
                                           port=24824,
                                           user='test_user',  # 数据库用户名
                                           password='a123456',  # 数据库密码
                                           db='storage',  # 数据库名称
                                           charset='utf8',
                                           cursorclass=pymysql.cursors.DictCursor)
        # 使用 cursor() 方法创建一个游标对象 cursor
        self.cursor = self.connection.cursor ()

    def sql_close(self):
        self.cursor.close ()
        self.connection.close ()

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
                # print(str(urllib.parse.quote(body[p])))
                continue
            str_parm = str_parm + str (p) + "=" + str (body[p]).replace (" ", "") + "&"
            # print(str(body[p]).replace(" ",""))
        # 加上对应的key
        str_parm = str_parm.rstrip ('&')
        # print("字符串拼接:", str_parm)

        # 转换md5串
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
        eg = EncryptDate(apikey)  # 这里密钥的长度必须是16的倍数
        res = eg.encrypt(md5_sign)
        # print("AES加密:", res)
        # print(eg.decrypt(res))
        return res

    def get_warehouse_num(self, sku):
        # 生成sign签名
        # API接口路径
        url = "https://openapi.lingxing.com/erp/sc/routing/data/local_inventory/inventoryDetails"
        body = {"access_token": self.access_token,
                "timestamp": int(time.time()),
                "app_key": "ak_nEfE94OSogf3x", "offset": 0, "length": 400
               }
        # "wid": "2156,1489,2382,1490,1461,1488,1476,1477,1399,1478,414", "offset": 0, "length": 400
        res = self.get_sign(body)
        # res = ''
        querystring = {"access_token": self.access_token,
                       "timestamp": int(time.time()),
                       "app_key": self.app_id,
                       "sign": res
                       }
        payload = {"wid": "", "offset": 0, "length": 400}
        payload = json.dumps(payload)
        headers = {
            "Content-Type": "application/json",
            "Authorization": "bearer {{access_token}}"
        }
        response = requests.request("POST", url, data=payload, headers=headers, params=querystring)
        result1 = json.loads(response.text)
        num_total = 0
        # print(result1)
        # 判断数据是否正常获取
        if result1['code'] == 0 and result1['message'] == "success":
            # print(len(result1['data']))
            # 获取库存明细数据条数
            length = result1['total']
            # length = 620
            # print(length)
            i = int(length/400)
            # print(i)
            # 以四百条数据为一页分页查询
            for k in range(0, i+1):
                # 分页查询
                payload = {"wid": '', "offset": k*400, "length": 400}
                if k == i:
                    body['length'] = length-k*400
                    payload['length'] = length-k*400
                body['offset'] = k*400
                print(payload)
                res = self.get_sign(body)
                querystring['sign'] = res
                payload = json.dumps(payload)
                response = requests.request("POST", url, data=payload, headers=headers, params=querystring)
                result = json.loads(response.text)
                # print(result)
                # print(result['data'][0])
                for q in result['data']:
                    if len(sku) == 10:
                        if q['fnsku'] == sku:
                            print(q)
                            num_total += q['product_total']
                    else:
                        if q['sku'] == sku:
                            print(q)
                            num_total += q['product_total']
        else:
            print(result1)
        print(num_total)
        return num_total


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
