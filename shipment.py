import pymysql
import os
import json
import global_var
import openpyxl
import time
import shutil


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


def get_order_msg(index, order):
    try:
        if index == "SKU":
            name = func("SELECT `品名` FROM `data_read`.`listing` where `SKU`='%s'" % order)
            return {'SKU': order, 'name': name[0][0]}
        if index == "FNSKU":
            name = func("SELECT `品名` FROM `data_read`.`listing` where `FNSKU`='%s'" % order)
            if name[0]:
                return {'FNSKU': order, 'name': name[0][0]}
            else:
                return {'FNSKU': order, 'name': '-'}
        if index == "次品出库":
            if len(order) == 10:
                name = func("SELECT `品名` FROM `data_read`.`listing` where `SKU`='%s'" % order)
                return {'SKU': order, 'name': name[0][0]}
            else:
                name = func("SELECT `品名` FROM `data_read`.`listing` where `FNSKU`='%s'" % order)
                if name[0]:
                    return {'FNSKU': order, 'name': name[0][0]}
                else:
                    return {'FNSKU': order, 'name': '-'}
        if index == "计划单号":
            sql = ''
        if index == "PDD/ZX":
            if order.find('XNWL') > 0:
                sku = func(f"select `SKU` from `storage`.`sku_map` where `条形码` = '{order}'")[0]
                return {'SKU': sku[0], 'name': sku[1]}
            else:
                name = get_productname(order)
                return {'SKU': order, 'name': name}
    except Exception as e:
        print(e)
        return False


def get_productname(sku):
    url = f"https://erp.lingxing.com/api/product/lists?search_field_time=create_time&sort_field=create_time&" \
          f"sort_type=desc&search_field=sku&search_value={sku}&attribute=&status=&is_matched_alibaba=&" \
          f"senior_search_list=[]&offset=0&is_combo=&length=500&is_aux=0&product_type[]=1&product_type[]=2&" \
          f"selected_product_ids=&req_time_sequence=%2Fapi%2Fproduct%2Flists$$"
    get_headers = {'user-agent': 'Mozilla/5.0', 'Referer': 'https://erp.lingxing.com/erp/productManage'}
    get_msg = global_var.s.get(url, headers=get_headers)
    get_msg = json.loads(get_msg.text)
    productname = ''
    for i in get_msg['list']:
        if i['sku'] == sku:
            productname = i['product_name']
    return productname


def uploading_pdd(list_sku, list_num):
    dict_product = []
    complete_flag = 0
    please_url = "https://erp.lingxing.com/api/module/inventoryReceipt/Outbound/completeOrder"
    find_headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:95.0) Gecko/20100101 Firefox/95.0'
        , 'Referer': 'https://erp.lingxing.com/erp/outbound_manual', 'Accept': 'application/json, text/plain, */*',
                    'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Content-Type': 'application/json;charset=utf-8',
                    'X-AK-Request-Id': '03cabda1-739d-4cd7-bd94-6650f97775a8',
                    'X-AK-Company-Id': '90136229927150080',
                    'X-AK-Request-Source': 'erp',
                    'X-AK-ENV-KEY': 'SAAS-10',
                    'X-AK-Version': '2.8.5.1.2.033',
                    'X-AK-Zid': '109810',
                    'Content-Length': '481',
                    'Origin': 'https://erp.lingxing.com',
                    'Connection': 'keep-alive'}
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
    for j in range(0, len (list_sku)):
        # dict_product.append(j)
        # dict_product[j] = {}
        # print(dict_product)
        sku = list_sku[j]
        get_url = "https://erp.lingxing.com/api/storage/lists"
        data = {"wid_list": "", "mid_list": "", "sid_list": "", "cid_list": "", "bid_list": "",
                "principal_list": "",
                "product_type_list": "", "product_attribute": "", "product_status": "", "search_field": "sku",
                "search_value": f"{sku}", "is_sku_merge_show": 0, "is_hide_zero_stock": 0, "offset": 0,
                "length": 200, "sort_field": "pre_total", "sort_type": "desc", "gtag_ids": "",
                "senior_search_list": "[]", "req_time_sequence": "/api/storage/lists$$"}
        data = json.dumps (data)
        get_msg = global_var.s.post (get_url, headers=get_headers, data=data)
        get_msg = json.loads (get_msg.text)
        # print(text)
        list_text = []
        list_list = get_msg['data']['list']
        print(get_msg['data']['list'])
        for i in range(0, len(list_list)):
            if list_list[i]['wh_name'] == '横中路仓库-美国' and list_list[i]['sku'] == sku:
                list_text.append(list_list[i])
        print(list_text)
        if list_text:
            sku_name = list_text[0]['product_name']
            sku_name = sku_name.replace('/', '%2F')
            sku_name = sku_name.replace('-', '%2D')
            # sku_name = sku_name.replace('%', '%25')
            sku_name = sku_name.replace('#', '%23')
            sku_name = sku_name.replace('&', '%26')
            sku_name = sku_name.replace('+', '%2B')
            sku_name = sku_name.replace('(', '%28')
            sku_name = sku_name.replace(')', '%29')
            if list_text[0]['total'] >= int(list_num[j]):
                dict1 = {}
                dict1['bad_num'] = 0
                dict1['fnsku'] = ""
                dict1['good_num'] = str(list_num[j])
                dict1['item_id'] = 0
                dict1['product_id'] = list_text[0]['product_id']
                dict1['product_name'] = sku_name
                dict1['seller_id'] = '0'
                dict1['sid_str'] = ""
                dict1['sku'] = sku
                # print(dict1)
                dict_product.append (dict1)
                # print(dict_product)
            else:
                complete_flag = 1
        else:
            complete_flag = 1
    if complete_flag == 0:
        dict_pdd = {}
        dict_pdd['audit_user'] = []
        dict_pdd['cg_uid'] = ""
        dict_pdd['fee_part_type'] = 0
        dict_pdd['flow_id'] = ""
        dict_pdd['bin_type'] = 0
        dict_pdd['order_sn'] = ""
        dict_pdd['other_fee'] = ""
        dict_pdd['product_list'] = dict_product
        dict_pdd['purchase_order_sn'] = ""
        dict_pdd['remark'] = ""
        dict_pdd['req_time_sequence'] = "/api/module/inventoryReceipt/Outbound/completeOrder$$1"
        dict_pdd['return_price'] = ""
        dict_pdd['supplier_id'] = ""
        dict_pdd['to_wid'] = ""
        dict_pdd['type'] = 11
        dict_pdd['wid'] = 1461
        # please_pdd = urlencode(dict_pdd, encoding='gb2312')
        please_pdd = json.dumps(dict_pdd, ensure_ascii=False).encode ("utf-8")
        # please_pdd = json.dumps(dict_pdd)
        # please_pdd = dict_pdd
        print(please_pdd)
        # please_pdd = please_pdd.encode('utf-8')
        please = global_var.s.post(please_url, headers=find_headers, data=please_pdd)
        print(please.text)
        print(please.status_code)
        net_msg = json.loads(please.text)
        if net_msg['code'] == 1 and net_msg['msg'] == '请求成功':
            return True
        else:
            return False
    else:
        return False


def download_fab(sid, boxs):
    # 地址1
    upload_url1 = "https://erp.lingxing.com/api/fba_shipment/showShipment_v2?search_field=shipment_id&search_value=%s&shipment_status[]=WORKING" % sid
    # 请求头1
    headers1 = {"User-Agent": "Mozilla/5.0",
                "Referer": "https://erp.lingxing.com/fbaCargo"}
    res1 = global_var.s.get(upload_url1, headers=headers1)
    r2 = json.loads(res1.text)
    print(r2)
    r3 = r2['msg']
    r4 = int(r2['data']['total'])
    if r4 > 1:
        return [False, "货件单号不唯一，当前只下载第一个。\n请仔细检查货件单号。"]
    list1 = []
    list1 = r2['data']['list']
    if list1:
        dict1 = list1[0]
        id_shipment = dict1['id']
        item_list = dict1['item_list']
        item_num = len(item_list)

        # 地址2
        upload_url2 = "https://erp.lingxing.com/api/fba_shipment/downloadPackingList?id=%s&type=2&box_num=%d" % (
            id_shipment, int(boxs))
        # 请求头2
        headers2 = {"User-Agent": "Mozilla/5.0",
                    "Referer": "https://erp.lingxing.com/fbaCargo"}
        res2 = global_var.s.get(upload_url2, headers=headers2, stream=False)
        with open('./static/装箱信息单/上传装箱信息.xlsx', 'wb') as q:
            q.write(res2.content)
        print("装箱清单下载完成")
        return [True, "装箱清单下载完成"]


def read_excl():
    path = "./static/装箱信息单/上传装箱信息.xlsx"
    wb = openpyxl.load_workbook(path)
    wb_sheet = wb.active
    row = wb_sheet.max_row
    column = wb_sheet.max_column
    list_data = []
    list_fnsku = []
    for i in range(4, row+1):
        id = wb_sheet.cell(row=i, column=1).value
        if id:
            msku = wb_sheet.cell(row=i, column=2).value
            fnsku = wb_sheet.cell(row=i, column=3).value
            name = wb_sheet.cell(row=i, column=4).value
            sku = wb_sheet.cell(row=i, column=5).value
            num = wb_sheet.cell(row=i, column=6).value
            list_data.append({'id': id, 'msku': msku, 'fnsku': fnsku, 'name': name, 'sku': sku, 'num_shipment': num})
            list_fnsku.append(fnsku)
    return list_data, list_fnsku


def write_excl(list_fnsku, list_pa, box_num, shipment_id):
    path = "./上传装箱信息.xlsx"
    if os.path.exists (r'./上传装箱信息.xlsx') == False:
        return "error", "上传装箱信息文件丢失，请重新下载装箱信息。"
    wb = openpyxl.load_workbook(path)
    sheet = wb[wb.sheetnames[0]]
    row = sheet.max_row
    column = sheet.max_column
    if int(box_num) < 15:
        column1 = 6 + int(box_num)
    else:
        column1 = column
    row1 = row - 30
    print ("该表有%d行" % row1)
    print ("该表有", column1, "列")

    count = 4
    finish_code = 0
    # sheet.delete_cols(7)
    for item in list_fnsku:
        print (item)
        long = len(item)
        total = 0
        for t in range(0, long):
            total = total + int(item[t])
        if total < int(item[4]):
            finish_code = 0
            break
        elif total > int(item[4]):
            finish_code = 0
            break
        else:
            for c in range(7, column1 + 1):
                sheet.cell(row=count, column=c, value=item[(c - 7)])
            count = count + 1
        finish_code = 1
    if finish_code:
        # 更新数据库
        flag = 1
        if list_pa:
            for i in list_pa:
                state = "已出货"
                func("UPDATE `storage`.`warehouse` SET `状态` = '%s' WHERE `箱号` = '%s'" % (state, str(i)), 'w')
        if flag == 0:
            wb.save ("上传装箱信息.xlsx")
            # 可以自动上传后，下面的内容就不必了
            time1 = time.strftime("%Y_%m_%d", time.localtime ())
            if os.path.exists('C:/装箱信息单'):
                shutil.copyfile('./上传装箱信息.xlsx',
                                 'C:/装箱信息单/%s上传装箱信息%s.xlsx' % (shipment_id, time1))
            else:
                os.makedirs('C:/装箱信息单')
                shutil.copyfile('./上传装箱信息.xlsx',
                                 'C:/装箱信息单/%s上传装箱信息%s.xlsx' % (shipment_id, time1))
            return True, "提交完成，文件在C盘的<装箱信息单>文件夹。"
            # # 更新数据库

