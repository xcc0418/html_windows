import pymysql
import os
import json
import global_var
import openpyxl
import datetime


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
        num_all = find_storage(index_data)
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

