import datetime
from flask import Flask, render_template, request
import pymysql
import os
import requests
import json
import time
from reportlab.pdfgen import canvas
import barcode
from PIL import Image, ImageDraw, ImageFont
from barcode.writer import ImageWriter
import global_var
import search
import shipment
import create_msku
import stores_requisition
import male_parent
import parent_message
import upload_image
from flask import session
from concurrent.futures import ThreadPoolExecutor

executor = ThreadPoolExecutor(10)
# from flask.ext.login import LoginManger, login_required

app = Flask(__name__, template_folder='./static/templates')
# app.secret_key = 'Cobak'
# login_manager = LoginManger()
# login_manager.session_protection = 'strong'
# login_manager.login_view = 'auth.login'
# login_manager.init_app(app)
app.permanent_session_lifetime = datetime.timedelta(seconds=60*60*24)
app.config['UPLOAD_FOLDER'] = 'F:/html_windows/static/FNSKU装箱信息'
app.config['SECRET_KEY'] = 'Cobak'


# 跨域支持response.setHeader("Set - Cookie", "HttpOnly;Secure;SameSite = None")
def after_request(resp):
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp


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


def save_pdf(fnsku, pa_name, num, name, supplier):
    enc = barcode.get_barcode_class('code128')
    # 生成条形码
    encoder = enc(pa_name, writer=ImageWriter())
    encoder.save("./static/图片/photo/{name}".format(name=pa_name), {'format': 'PNG', 'font_size': 40, 'dpi': 600})
    os.makedirs(f"./static/图片/{pa_name}")
    jpg_path = './static/图片/photo/{name}.png'.format(name=pa_name)
    pdf_path = './static/图片/{pa}/{name}.pdf'.format(pa=pa_name, name=pa_name)
    # 向条形码图片中写入内容
    # img = Image.new('RGB', (378, 567), (255, 255, 255)),'module_width': 0.1, 'module_height': 7
    img = Image.new('RGB', (756, 1134), (255, 255, 255))
    pyq = Image.open(jpg_path)
    img.paste(pyq, (0, 584))
    draw = ImageDraw.Draw(img)
    i = 1
    j = 0
    font = ImageFont.truetype ("simhei.ttf", 40, encoding="unic")  # 设置字体
    # 将品名和个数依次写入图片中
    text_data = name
    if len(text_data) > 17 and len(text_data) < 36:
        draw.text((20, 550 - i * 36 - 46), u'{text}'.format(text=text_data[0:18]), 'black', font)
        draw.text((20, 550 - i * 36), u'{text}'.format(text=text_data[18:]), 'black', font)
        draw.text((20, 550 - i * 36 + 46), u'{text}'.format(text=fnsku), 'black', font)
        draw.text((300, 550 - i * 36 + 46), u'{text}'.format(text=num), 'black', font)
        draw.text((400, 550 - i * 36 + 46), u'{text}'.format(text=supplier), 'black', font)
        i += 4
        j += 1
    elif len(text_data) >= 36:
        draw.text((20, 550 - i * 36 - 92), u'{text}'.format(text=text_data[0:18]), 'black', font)
        draw.text((20, 550 - i * 36 - 46), u'{text}'.format(text=text_data[18:36]), 'black', font)
        draw.text((20, 550 - i * 36), u'{text}'.format(text=text_data[36:]), 'black', font)
        draw.text((20, 550 - i * 36 + 46), u'{text}'.format(text=fnsku), 'black', font)
        draw.text((300, 550 - i * 36 + 46), u'{text}'.format(text=num), 'black', font)
        draw.text((400, 550 - i * 36 + 46), u'{text}'.format(text=supplier), 'black', font)
        i += 4
        j += 2
    else:
        draw.text((20, 550 - i * 36), u'{text}'.format(text=text_data), 'black', font)
        draw.text((20, 550 - i * 36 + 46), u'{text}'.format(text=fnsku), 'black', font)
        draw.text((300, 550 - i * 36 + 46), u'{text}'.format(text=num), 'black', font)
        draw.text((400, 550 - i * 36 + 46), u'{text}'.format(text=supplier), 'black', font)
        i += 3
        j += 1
    img.save(jpg_path, 'JPEG', quality=100)
    jpg_to_pdf(jpg_path, pdf_path)
    path = f'../图片/{pa_name}/{pa_name}.pdf'
    return path


def jpg_to_pdf(jpg, pdf_path):
    (w, h) = Image.open(jpg).size
    user = canvas.Canvas(pdf_path, pagesize=(w, h))
    user.drawImage(jpg, 0, 0, w, h)
    user.showPage()
    user.save()


# 请求拦截器，对未登录的链接进行拦截，防止非法访问
@app.before_request
def before_user():
    if request.path == "/login":
        return None
    if request.path.startswith("/static/images"):
        return None
    if request.path.startswith("/api"):
        return None
    if not session.get("username"):
        return render_template('login.html')


@app.route('/', methods=["POST", "GET"])
def index():
    if request.method == 'GET':
        return render_template('login.html')


@app.route('/login', methods=["POST"])
def upload_asinking():
    dict_data = dict(request.form)
    print(dict_data)
    username = dict_data['username']
    password = dict_data['password']
    # print(username, password)
    global_var.s = requests.Session()
    # 登录url
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
    data = {'account': username, 'pwd': password}
    data = json.dumps(data)
    try:
        r = global_var.s.post(login_url, headers=headers, data=data)
        r.raise_for_status()
        r1 = r.text
        # print(r1)
        r2 = json.loads(r1)
        r3 = r2['msg']
    except:
        r3 = '网络错误失败'
    if r3 == '操作成功' or r3 == '登录成功':
        session['username'] = username
        session.permanent = True
        return '<script>alert("登录成功");location.href="/home_page";</script>'
    else:
        return '<script>alert("登录失败");location.href="/";</script>'


@app.route('/home_page')
def page():
    return render_template('home_Page.html')


@app.route('/pa_msg',methods=["POST"])
def pa_msg():
    if request.method == 'POST':
        dict_data = json.loads(request.form['data'])
        print(dict_data)
        pa_name = dict_data['pa_name']
        if pa_name:
            data = func("select * from `storage`.`warehouse` where `箱号` = '%s'" % pa_name)
            if data:
                name = func("SELECT `品名` FROM `data_read`.`listing` where `FNSKU`='%s'" % data[0][1])
                list_pa = {'msg': 'success', 'data': {'箱号': data[0][0], 'fnsku': data[0][1], '品名': name[0][0], '装箱数量': data[0][2], '装箱状态': data[0][11]}}
            else:
                list_pa = {'msg': 'error', 'data': f"{pa_name}, 请检查输入是否正确"}
        else:
            list_pa = {'msg': 'error', 'data': '请先输入箱号'}
        return json.dumps(list_pa)
    else:
        return json.dumps({'msg': 'error'})


@app.route('/packing/del_pa',methods=["POST"])
def del_pa():
    if request.method == 'POST':
        dict_data = json.loads(request.form['data'])
        pa_name = dict_data['pa_name']
        if pa_name:
            quantity_msg = search.Quantity()
            msg, message = quantity_msg.delect_box(pa_name)
            if msg:
                return json.dumps({'msg': 'success', 'data': message})
            else:
                return json.dumps({'msg': 'error', 'data': message})
        else:
            return json.dumps({'msg': 'error'})
    else:
        return json.dumps({'msg': 'error'})


@app.route('/get_pa', methods=["GET"])
def get_pa():
    if request.method == 'GET':
        global_var.fnsku = None
        global_var.num = 0
        time_now = time.strftime("%y%m%d%H%M%S", time.localtime())
        pa_name = f"PA{time_now}"
        # global_var.pa_name = pa_name
        dict_pa_name = {'success': pa_name}
        return json.dumps(dict_pa_name)
    else:
        return json.dumps ({'msg': 'error'})


@app.route('/get_fnsku', methods=["POST"])
def get_fnsku():
    if request.method == 'POST':
        dict_data = json.loads(request.form['data'])
        print(dict_data)
        if dict_data:
            fnsku_value = dict_data['fnsku_value'].strip()
            pa_name = dict_data['pa_name']
            if pa_name and len(pa_name) == 14:
                name = func("SELECT `品名` FROM `data_read`.`listing` where `FNSKU`='%s'" % fnsku_value)
                if name:
                    fnsku_msg = {'msg': 'success', 'data': {'fnsku': fnsku_value, '品名': name[0][0], '装箱数量': 1}}
                else:
                    fnsku_msg = {'msg': 'error', 'data': '这个fnsku没找到，请检查'}
                return json.dumps(fnsku_msg)
            else:
                fnsku_msg = {'msg': 'error', 'data': '请先获取箱号'}
                return json.dumps(fnsku_msg)
        else:
            fnsku_msg = {'msg': 'error', 'data': '请先输入fnsku'}
            return json.dumps(fnsku_msg)
    else:
        return json.dumps ({'msg': 'error'})


@app.route('/pack_pa', methods=["POST"])
def pack_pa():
    if request.method == 'POST':
        dict_data = json.loads(request.form['data'])
        print(dict_data)
        if dict_data:
            pa_name = dict_data['pa_name']
            fnsku = dict_data['fnsku']
            num = int(dict_data['num'])
            name = str(dict_data['name'])
            sql1 = "SELECT `供应商` FROM `data_read`.`listing` where `FNSKU`='%s'" % fnsku
            supplier = func(sql1)[0][0]
            sql = "INSERT INTO `storage`.`warehouse`(`箱号`,`FNSKU1`,`数量1`,`状态`) VALUES ('%s','%s',%d,'%s')" % (
            pa_name, fnsku, num, '已打包')
            result = func(sql, m='w')
            if result:
                pdf_path = save_pdf(fnsku, pa_name, num, name, supplier)
                msg = {'msg': 'success', 'data': {'filename': pdf_path}}
            else:
                msg = {'msg': 'error', 'data': '装箱失败'}
        else:
            msg = {'msg': 'error', 'data': '请先开始装箱操作'}
        return json.dumps(msg)
    else:
        return json.dumps ({'msg': 'error'})


@app.route('/search_msg', methods=["POST"])
def search_msg():
    if request.method == 'POST':
        dict_data = json.loads(request.form['data'])
        if dict_data:
            index = dict_data['index']
            index_data = dict_data['index_data']
            # index_data = ['X0033WDOUV', 'X003H2NKFB']
            print(index_data)
            search_msg = search.Quantity()
            result = search_msg.get_msg(index, index_data)
            if result:
                if index == 'FNSKU':
                    list_data, num_local = search.get_po(index_data)
                    if list_data:
                        msg = {'msg': "success", 'data': {'file': result[0], 'filename': result[1], 'list_data': {'data_list': list_data, '装箱总数量': num_local}}}
                        return json.dumps(msg)
                    else:
                        msg = {'msg': "error", 'data': f'{index_data}没有装箱信息'}
                        return json.dumps(msg)
                else:
                    msg = {'msg': "success", 'data': result}
                    return json.dumps(msg)
            else:
                msg = {'msg': "error", 'data': '没有找到这个信息'}
                return json.dumps(msg)
        else:
            return json.dumps({'msg': "error", 'data': '请先输入要查询的数据'})
    else:
        return json.dumps ({'msg': 'error'})


@app.route('/change_location', methods=["POST"])
def change_location():
    if request.method == 'POST':
        dict_data = json.loads(request.form['data'])
        print(dict_data)
        if dict_data:
            pa_name = dict_data['pa_name']
            location = dict_data['location']
            result = func("UPDATE `storage`.`warehouse` SET `存放位置` = '%s' WHERE `箱号` = '%s'" % (location, pa_name), 'w')
            if result:
                msg = {'msg': "success"}
            else:
                msg = {'msg': "error"}
            return json.dumps(msg)
        else:
            return json.dumps({'msg': 'error'})
    else:
        return json.dumps({'msg': 'error'})


@app.route('/uploader', methods=["POST"])
def uploader():
    if request.method == 'POST':
        filename = request.files['myfile']
        print(filename)
        data_time = datetime.datetime.now().strftime("%Y%m%d%H%M")
        path = f'D:/FNSKU装箱信息/装箱信息{data_time}.xlsx'
        filename.save(os.path.join('UPLOAD_FOLDER', path))
        search_msg = search.Quantity()
        msg = search_msg.get_warehouse(filename)
        if msg:
            return json.dumps({'msg': 'success', 'data': {'file': msg[0], 'filename': msg[1]}})
        else:
            return json.dumps({'msg': 'error'})
    else:
        return json.dumps ({'msg': 'error'})


@app.route('/get_order', methods=["POST"])
def get_order():
    if request.method == 'POST':
        dict_data = json.loads(request.form['data'])
        print(dict_data)
        if dict_data:
            index = dict_data['index']
            order = dict_data['order'].strip()
            msg = shipment.get_order_msg(index, order)
            if msg:
                return json.dumps({'msg': 'success', 'data': msg})
            else:
                return json.dumps({'msg': 'error', 'data': '出库失败'})
        else:
            return json.dumps({'msg': 'error', 'data': '请先输入要出库的物料'})
    else:
        return json.dumps ({'msg': 'error'})


@app.route('/shipment_upload', methods=["POST"])
def shipment_upload():
    if request.method == 'POST':
        dict_data = json.loads(request.form['data'])
        if dict_data:
            list_index = []
            list_num = []
            for i in dict_data['list_data']:
                list_index.append(i[0])
                list_num.append(i[2])
            warehouse = dict_data['warehouse']
            quantity_msg = shipment.Quantity()
            msg = quantity_msg.order_out(list_index, list_num, warehouse)
            if msg:
                return json.dumps({'msg': "success"})
            else:
                return json.dumps({'msg': 'error'})
        else:
            return json.dumps({'msg': 'error'})
    else:
        return json.dumps ({'msg': 'error'})


@app.route('/shipment_put', methods=["POST"])
def shipment_put():
    if request.method == 'POST':
        dict_data = json.loads(request.form['data'])
        if dict_data:
            list_index = []
            list_num = []
            for i in dict_data['list_data']:
                list_index.append(i[0])
                list_num.append(i[2])
            warehouse = dict_data['warehouse']
            quantity_msg = shipment.Quantity()
            msg = quantity_msg.order_put(list_index, list_num, warehouse)
            if msg:
                return json.dumps({'msg': "success"})
            else:
                return json.dumps({'msg': 'error'})
        else:
            return json.dumps({'msg': 'error'})
    else:
        return json.dumps ({'msg': 'error'})


@app.route('/get_fba', methods=["POST"])
def get_fba():
    if request.method == 'POST':
        dict_data = json.loads(request.form['data'])
        print(dict_data)
        if dict_data:
            msg = shipment.download_fab(dict_data['fba'], dict_data['box_num'])
            if msg[0]:
                print(msg[1])
                list_data, list_fnsku = shipment.read_excl()
                return json.dumps({'msg': "success", 'data': list_data, 'data_fnsku': list_fnsku})
            else:
                return json.dumps({'msg': 'error', 'data': msg[1]})
        else:
            return json.dumps({'msg': 'error', 'data': '请先输入FBA货件单号'})
    else:
        return json.dumps ({'msg': 'error'})


@app.route('/FBA_shipment/get_fnsku', methods=["POST"])
def get_shipment_fnsku():
    if request.method == 'POST':
        dict_data = json.loads(request.form['data'])
        index = dict_data['index'].strip()
        list_pa = dict_data['list_pa']
        print(index)
        if len(index) == 10:
            return json.dumps({'msg': "success", 'data': {'fnsku': index, 'num': 1}})
        if len(index) == 14:
            if index in list_pa:
                return json.dumps({'msg': 'error', 'data': f"这个{index}箱号已重复，请重试！"})
            else:
                result = func(f"select `FNSKU1`, `数量1` from `storage`.`warehouse` where `箱号` = '{index}' and `状态` = '已打包'")
                if result:
                    return json.dumps({'msg': "success", 'data': {'fnsku': result[0][0], 'num': result[0][1]}})
                else:
                    return json.dumps({'msg': 'error', 'data': f"这个{index}箱号没找到，请重试！"})
        else:
            return json.dumps({'msg': 'error', 'data': f"{index}格式不正确，请检查输入是否正确！"})
    else:
        return json.dumps ({'msg': 'error'})


@app.route('/FBA_shipment/save_table', methods=["POST"])
def save_table():
    if request.method == 'POST':
        dict_data = json.loads(request.form['data'])
        list_data = dict_data['list_data']
        shipment_id = dict_data['shipment_id']
        list_pa = dict_data['list_pa']
        box_num = dict_data['box_num']
        msg, message = shipment.change_excl(list_data, shipment_id, box_num, list_pa)
        if msg:
            return json.dumps({'msg': "success", 'data': {'filename': message[0], 'time_data': message[1]}})
        else:
            return json.dumps({'msg': 'error', 'data': message})
    else:
        return json.dumps ({'msg': 'error'})


@app.route('/FBA_shipment/shipment_order', methods=["POST"])
def shipment_order():
    if request.method == 'POST':
        dict_data = json.loads(request.form['data'])
        list_data = dict_data['list_data']
        shipment_id = dict_data['shipment_id']
        list_pa = dict_data['list_pa']
        msg, message = shipment.submmit(list_data, shipment_id, list_pa)
        if msg:
            return json.dumps({'msg': "success", 'data': {'filename': message[0], 'time_data': message[1]}})
        else:
            return json.dumps({'msg': 'error', 'data': message})
    else:
        return json.dumps ({'msg': 'error'})


@app.route('/FBA_shipment/upload_file', methods=["POST"])
def upload_file():
    if request.method == 'POST':
        filename = request.files['myfile']
        print(filename)
        data_time = datetime.datetime.now().strftime("%Y%m%d%H%M")
        path = f'D:/装箱信息单/装箱信息{data_time}.xlsx'
        filename.save(os.path.join('UPLOAD_FOLDER', path))
        list_data, fba_id, box_num, list_pa = shipment.read_upload_excl(path)
        return json.dumps({'msg': "success", 'data': {'list_data': list_data, 'list_pa': list_pa, 'fba_id': fba_id,
                                                      'box_num': box_num}})
    else:
        return json.dumps({'msg': 'error'})


@app.route('/FBA_shipment/add_box', methods=["POST"])
def add_box():
    if request.method == 'POST':
        dict_data = json.loads(request.form['data'])
        list_data = dict_data['list_data']
        shipment_id = dict_data['shipment_id']
        list_pa = dict_data['list_pa']
        box_num = int(dict_data['box_num'])+1
        list_data_new = []
        for i in range(1, len(list_data)):
            list_new = list_data[i]
            list_new.append(0)
            list_data_new.append(list_new)
        return json.dumps({'msg': "success", 'data': {'list_data': list_data_new, 'list_pa': list_pa, 'fba_id': shipment_id, 'box_num': box_num}})
    else:
        return json.dumps({'msg': 'error'})


@app.route('/FBA_shipment/minus_box', methods=["POST"])
def minus_box():
    if request.method == 'POST':
        dict_data = json.loads(request.form['data'])
        list_data = dict_data['list_data']
        shipment_id = dict_data['shipment_id']
        list_pa = dict_data['list_pa']
        box_num = int(dict_data['box_num'])-1
        list_data_new = []
        for i in range(1, len(list_data)):
            list_new = list_data[i]
            list_new.pop()
            list_data_new.append(list_new)
        return json.dumps({'msg': "success", 'data': {'list_data': list_data_new, 'list_pa': list_pa, 'fba_id': shipment_id, 'box_num': box_num}})
    else:
        return json.dumps ({'msg': 'error'})


@app.route('/stores_requisition/get_class', methods=["GET"])
def get_class():
    if request.method == "GET":
        quantity = stores_requisition.Quantity()
        list_class = quantity.get_class()
        return json.dumps({'msg': "success", 'data': {'list_class': list_class}})
    else:
        return json.dumps({'msg': 'error'})


@app.route('/stores_requisition/find_po', methods=["POST"])
def find_po():
    if request.method == "POST":
        dict_data = json.loads(request.form['data'])
        po_name = dict_data['po_name']
        class_name = dict_data['class_name']
        quantity = stores_requisition.Quantity()
        msg, message = quantity.find_po(po_name, class_name)
        if msg:
            return json.dumps({'msg': "success", 'data': message})
        else:
            return json.dumps({'msg': "error", 'data': message})
    else:
        return json.dumps({'msg': 'error'})


@app.route('/stores_requisition/upload_table', methods=["POST"])
def upload_table():
    if request.method == "POST":
        dict_data = json.loads(request.form['data'])
        po_name = dict_data['po_name']
        class_name = dict_data['class_name']
        list_sku = dict_data['list_sku']
        list_order = []
        quantity = stores_requisition.Quantity()
        # print(list_sku)
        for i in list_sku:
            if i[0] != '——' and i[1] != '0':
                if len(i[0]) > 20:
                    sku = quantity.find_sku(i[0], 'sku')
                else:
                    sku = i[0]
                if len(i[1]) > 50:
                    num = quantity.find_sku(i[1], 'num')
                else:
                    num = ''.join([x for x in i[1] if x.isdigit()])
                list_order.append([sku, int(num)])
        # print(list_order)
        msg, message = quantity.write_sql(po_name, class_name, list_order)
        # msg = False
        # message = [False, False]
        if msg:
            return json.dumps({'msg': "success", 'data': {"file": message[0], "filename": message[1]}})
        else:
            return json.dumps({'msg': "error", 'data': message})
    else:
        return json.dumps({'msg': 'error'})


@app.route('/stores_requisition/add_class', methods=["POST"])
def add_class():
    if request.method == "POST":
        dict_data = json.loads(request.form['data'])
        class_name = dict_data['class_name'].strip()
        quantity = stores_requisition.Quantity()
        msg, message = quantity.add_class(class_name)
        if msg:
            return json.dumps({'msg': "success", 'data': message})
        else:
            return json.dumps({'msg': "error", 'data': message})
    else:
        return json.dumps({'msg': 'error'})


@app.route('/show_requisition/get_po', methods=["POST"])
def get_po():
    if request.method == "POST":
        dict_data = json.loads(request.form['data'])
        po_name = dict_data['po_name']
        # print(po_name)
        quantity = stores_requisition.Quantity()
        msg = quantity.get_po(po_name)
        if msg:
            return json.dumps({'msg': "success", 'data': msg})
        else:
            return json.dumps({'msg': "error", 'data': f"没有找到{po_name}这个订单号，请检查"})
    else:
        return json.dumps({'msg': 'error'})


@app.route('/show_requisition/uploader_sql', methods=["POST"])
def uploader_sql():
    if request.method == 'POST':
        filename = request.files['myfile']
        print(filename)
        data_time = datetime.datetime.now().strftime("%Y%m%d%H%M")
        path = f'D:/生产日程表/生产日程表{data_time}.xlsx'
        quantity = stores_requisition.Quantity()
        filename.save(os.path.join('UPLOAD_FOLDER', path))
        msg, message = quantity.upload_sql(path)
        print(message)
        if msg:
            return json.dumps({'msg': "success"})
        else:
            return json.dumps({'msg': 'error', 'data': str(message)})
    else:
        return json.dumps({'msg': 'error'})


@app.route('/create_msku/get_msku', methods=["POST"])
def get_msku():
    if request.method == "POST":
        dict_data = json.loads(request.form['data'])
        # print(dict_data)
        sku = dict_data['sku'].strip()
        country = dict_data['country'].strip()
        supplier = dict_data['supplier'].strip()
        num = int(dict_data['num'].strip())
        msku = dict_data['msku'].strip()
        if sku and country and supplier and num and msku:
            if len(msku) <= 23:
                quantity = create_msku.Quantity()
                msg, message = quantity.create_msku(sku, country, supplier, num, msku)
                if msg:
                    return json.dumps({'msg': "success", 'data': {"file": message[0], "filename": message[1]}})
                else:
                    if message:
                        return json.dumps({'msg': 'error', 'data': message})
                    else:
                        return json.dumps({'msg': 'error', 'data': '创建失败'})
            else:
                return json.dumps({'msg': 'error', 'data': 'msku模板长度超出，请重试'})
        else:
            return json.dumps({'msg': 'error', 'data': '请检查输入是否正确'})
    else:
        return json.dumps({'msg': 'error'})


@app.route('/create_msku/uploader_msku', methods=["POST"])
def uploader_msku():
    if request.method == "POST":
        filename = request.files['myfile']
        # print(filename)
        data_time = datetime.datetime.now().strftime("%Y%m%d%H%M")
        path = f'D:/MSKU生成/MSKU生成{data_time}.xlsx'
        quantity = create_msku.Quantity()
        filename.save(os.path.join('UPLOAD_FOLDER', path))
        msg, message = quantity.upload_excl(path)
        if msg:
            return json.dumps({'msg': "success", 'data': {"file": message[0], "filename": message[1]}})
        else:
            return json.dumps({'msg': 'error', 'data': message})
    else:
        return json.dumps({'msg': 'error'})


@app.route('/change_fnsku/find_fnsku', methods=["POST"])
def find_fnsku_change():
    if request.method == "POST":
        dict_data = json.loads(request.form['data'])
        # print(dict_data)
        sku = dict_data['sku'].strip()
        country = dict_data['country'].strip()
        if sku and country:
            quantity = create_msku.Quantity()
            msg, message = quantity.find_fnsku(sku, country)
            if msg:
                return json.dumps({'msg': 'success', 'data': message})
            else:
                return json.dumps({'msg': 'error', 'data': message})
        else:
            if not sku:
                return json.dumps({'msg': 'error', 'data': '请检查输入SKU'})
            elif not country:
                return json.dumps({'msg': 'error', 'data': '请检查输入国家'})
    else:
        return json.dumps({'msg': 'error'})


@app.route('/change_fnsku/get_fnsku', methods=["POST"])
def get_fnsku_change():
    if request.method == "POST":
        dict_data = json.loads(request.form['data'])
        # print(dict_data)
        sku = dict_data['sku'].strip()
        country = dict_data['country'].strip()
        num = int(dict_data['num'].strip())
        if sku and country:
            quantity = create_msku.Quantity()
            msg, message = quantity.get_fnsku(sku, country, num)
            if msg:
                return json.dumps({'msg': 'success', 'data': {"file": message[0], "filename": message[1]}})
            else:
                return json.dumps({'msg': 'error', 'data': message})
        else:
            if not sku:
                return json.dumps({'msg': 'error', 'data': '请检查输入SKU'})
            elif not country:
                return json.dumps({'msg': 'error', 'data': '请检查输入国家'})
    else:
        return json.dumps({'msg': 'error'})


@app.route('/change_fnsku/upload_fnsku', methods=["POST"])
def upload_fnsku():
    if request.method == "POST":
        filename = request.files['myfile']
        # print(filename)
        data_time = datetime.datetime.now().strftime("%Y%m%d%H%M")
        path = f'D:/FNSKU获取/FNSKU获取{data_time}.xlsx'
        quantity = create_msku.Quantity()
        filename.save(os.path.join('UPLOAD_FOLDER', path))
        msg, message = quantity.read_excl(path)
        if msg:
            return json.dumps({'msg': "success", 'data': {"file": message[0], "filename": message[1]}})
        else:
            return json.dumps({'msg': 'error', 'data': message})
    else:
        return json.dumps({'msg': 'error'})


@app.route('/change_fnsku/upload_warehouse', methods=["POST"])
def upload_warehouse():
    if request.method == "POST":
        filename = request.files['myfile']
        # print(filename)
        warehouse = request.form['warehouse']
        # warehouse = None
        print(filename, warehouse)
        if warehouse:
            data_time = datetime.datetime.now().strftime("%Y%m%d%H%M")
            path = f'D:/换标调整/换标调整{data_time}.xlsx'
            quantity = create_msku.Quantity()
            filename.save(os.path.join('UPLOAD_FOLDER', path))
            msg, message = quantity.change_fnsku(path, warehouse)
            if msg:
                return json.dumps({'msg': "success", 'data': {"file": message[0], "filename": message[1]}})
            else:
                return json.dumps({'msg': 'error', 'data': message})
        return json.dumps({'msg': 'error', 'data': '请先选择换标仓库'})
    else:
        return json.dumps({'msg': 'error'})


@app.route('/change_fnsku/pair_msku', methods=["GET"])
def pair_msku():
    if request.method == "GET":
        find_msku = create_msku.Find_order()
        flag = find_msku.grt_flag()
        if int(flag) == 1:
            return json.dumps({'msg': "error", 'message': '当前正在配对，请勿重复操作'})
        else:
            executor.submit(find_msku.get_msku)
            # print(msg)
            return json.dumps({'msg': "success"})
    else:
        return json.dumps({'msg': 'error'})


@app.route('/pair_msku/pair', methods=["POST"])
def pair():
    if request.method == "POST":
        dict_data = json.loads(request.form['data'])
        # print(dict_data)
        sku = dict_data['sku'].strip()
        asin = dict_data['asin'].strip()
        store = dict_data['store'].strip()
        version = dict_data['version'].strip()
        msku = dict_data['msku'].strip()
        fnsku = dict_data['fnsku'].strip()
        male_sku = dict_data['male_sku']
        male_parent = dict_data['male_parent']
        if sku and asin and store and version and msku and fnsku:
            quantity = create_msku.Quantity()
            msg, message = quantity.pair_msku(sku, asin, store, float(version), msku, fnsku, male_parent, male_sku)
            if msg:
                quantity.add_image_msg(asin, sku, fnsku, msku)
                return json.dumps({'msg': "success"})
            else:
                return json.dumps({'msg': 'error', 'data': message})
        else:
            return json.dumps({'msg': 'error', 'data': '请检查输入是否正确'})
    else:
        return json.dumps({'msg': 'error'})


@app.route('/pair_msku/upload_pair', methods=["POST"])
def upload_pair():
    if request.method == "POST":
        filename = request.files['myfile']
        # print(filename)
        data_time = datetime.datetime.now().strftime("%Y%m%d%H%M")
        path = f'D:/批量配对/批量配对{data_time}.xlsx'
        quantity = create_msku.Quantity()
        filename.save(os.path.join('UPLOAD_FOLDER', path))
        msg, message = quantity.batch_pair(path)
        return json.dumps({'msg': "success", 'data': {"file": msg, "filename": message}})
    else:
        return json.dumps({'msg': 'error'})


@app.route('/change_fnsku/get_pair_msg', methods=["POST"])
def get_pair_msg():
    if request.method == "POST":
        find_msku = create_msku.Find_order()
        flag = find_msku.grt_flag()
        if int(flag) == 1:
            return json.dumps({'msg': "error", 'message': '当前正在配对，请稍后查询'})
        else:
            filename = request.files['myfile']
            # print(filename)
            data_time = datetime.datetime.now().strftime("%Y%m%d%H%M")
            path = f'D:/批量配对/批量配对{data_time}.xlsx'
            quantity = create_msku.Quantity()
            filename.save(os.path.join('UPLOAD_FOLDER', path))
            msg, message = quantity.get_pair_msg(path)
            print(msg)
            return json.dumps({'msg': "success", 'data': {"file": msg, "filename": message}})
    else:
        return json.dumps({'msg': 'error'})


@app.route('/male_parent/parent_function', methods=["POST"])
def parent_function():
    if request.method == "POST":
        dict_data = json.loads(request.form['data'])
        parent = dict_data['male_parent']
        if parent:
            index = dict_data['index']
            quantity = male_parent.Quantity()
            msg, message = "", ""
            if index == "关联":
                sku = dict_data['sku']
                if sku:
                    msg, message = quantity.relevance_male(parent.strip(), sku.strip())
                else:
                    msg, message = False, "请先输入SKU"
            elif index == "解除关联":
                sku = dict_data['sku']
                if sku:
                    msg, message = quantity.relieve_male(parent.strip(), sku.strip())
                else:
                    msg, message = False, "请先输入SKU"
            elif index == "创建父体":
                msg, message = quantity.add_male(parent.strip())
            elif index == "创建父体并关联":
                sku = dict_data['sku']
                if sku:
                    msg, message = quantity.add_male(parent.strip())
                    if msg:
                        msg, message = quantity.relevance_male(parent.strip(), sku.strip())
                    else:
                        msg = False
                else:
                    msg, message = False, "请先输入SKU"
            elif index == "删除":
                msg, message = quantity.delete_male(parent.strip())
            elif index == "关联亚马逊父体":
                amazon_parent = dict_data['sku']
                if amazon_parent:
                    msg, message = quantity.relevance_amazon(parent.strip(), amazon_parent.strip())
                else:
                    msg, message = False, "请先输入亚马逊父体"
            elif index == "解除亚马逊父体关联":
                amazon_parent = dict_data['sku']
                if amazon_parent:
                    msg, message = quantity.relieve_amazon(parent.strip(), amazon_parent.strip())
                else:
                    msg, message = False, "请先输入亚马逊父体"
            if msg:
                if index == '关联' or index == '解除关联' or index == '创建父体并关联' or index == '删除':
                    upload_json = parent_message.Quantity()
                    executor.submit(upload_json.update_json)
                return json.dumps({'msg': "success", 'message': f"{index}成功"})
            else:
                return json.dumps({'msg': "error", 'message': message})
        else:
            return json.dumps({'msg': "error", 'message': '请先输入本地父体'})
    else:
        return json.dumps({'msg': 'error'})


@app.route('/male_parent/local_function', methods=["POST"])
def local_function():
    if request.method == "POST":
        dict_data = json.loads(request.form['data'])
        parent = dict_data['male_parent']
        if parent:
            index = dict_data['index']
            quantity = male_parent.Quantity()
            msg, message = "", ""
            if index == "关联":
                sku = dict_data['sku']
                if sku:
                    msg, message = quantity.relevance_sku(parent.strip(), sku.strip())
                    if msg:
                        quantity.add_image_msg([sku.strip(), parent.strip()])
                else:
                    msg, message = False, "请先输入SKU"
            elif index == "解除关联":
                sku = dict_data['sku']
                if sku:
                    msg, message = quantity.relieve_sku(parent.strip(), sku.strip())
                    if msg:
                        quantity.add_image_msg([sku.strip(), parent.strip()])
                else:
                    msg, message = False, "请先输入SKU"
            elif index == "创建品名":
                msg, message = quantity.add_sku(parent.strip())
            elif index == "创建品名并关联":
                sku = dict_data['sku']
                if sku:
                    msg, message = quantity.add_sku(parent.strip())
                    if msg:
                        msg, message = quantity.relevance_sku(parent.strip(), sku.strip())
                        if msg:
                            quantity.add_image_msg([sku.strip(), parent.strip()])
                    else:
                        msg = False
                else:
                    msg, message = False, "请先输入SKU"
            elif index == "删除":
                msg, message = quantity.delete_sku(parent.strip())
            if msg:
                if index == '关联' or index == '解除关联' or index == '创建品名并关联' or index == '删除':
                    upload_json = parent_message.Quantity()
                    executor.submit(upload_json.update_json)
                return json.dumps({'msg': "success", 'message': f"{index}成功"})
            else:
                return json.dumps({'msg': "error", 'message': message})
        else:
            return json.dumps({'msg': "error", 'message': '请先输入本地父体'})
    else:
        return json.dumps({'msg': 'error'})


@app.route('/male_parent/upload_male', methods=["POST"])
def upload_male():
    if request.method == "POST":
        filename = request.files['myfile']
        data_time = datetime.datetime.now().strftime("%Y%m%d%H%M")
        index = request.form['index']
        msg, message = '', ''
        if index == "关联":
            path = f'D:/本地父体/本地父体关联{data_time}.xlsx'
            filename.save(os.path.join('UPLOAD_FOLDER', path))
            quantity = male_parent.Quantity()
            msg, message = quantity.upload_parent(path)
        elif index == "解除关联":
            path = f'D:/本地父体/本地父体解除关联{data_time}.xlsx'
            filename.save(os.path.join('UPLOAD_FOLDER', path))
            quantity = male_parent.Quantity()
            msg, message = quantity.upload_relieve_male(path)
        elif index == "创建父体":
            path = f'D:/本地父体/本地父体新增{data_time}.xlsx'
            filename.save(os.path.join('UPLOAD_FOLDER', path))
            quantity = male_parent.Quantity()
            msg, message = quantity.upload_male(path)
        elif index == "创建父体并关联":
            path = f'D:/本地父体/本地父体新增并关联{data_time}.xlsx'
            filename.save(os.path.join('UPLOAD_FOLDER', path))
            quantity = male_parent.Quantity()
            msg, message = quantity.upload_male(path)
            if msg:
                msg, message = quantity.upload_parent(path)
        elif index == "删除":
            path = f'D:/本地父体/本地父体删除{data_time}.xlsx'
            filename.save(os.path.join('UPLOAD_FOLDER', path))
            quantity = male_parent.Quantity()
            msg = quantity.upload_delete_male(path)
        else:
            return json.dumps({'msg': "error", 'message': "暂不支持批量操作亚马逊父体"})
        if msg:
            if index == '关联' or index == '解除关联' or index == '创建父体并关联' or index == '删除':
                upload_json = parent_message.Quantity()
                executor.submit(upload_json.update_json)
            return json.dumps({'msg': "success", 'message': f"{index}成功"})
        else:
            return json.dumps({'msg': "error", 'message': message})
    else:
        return json.dumps({'msg': "error"})


@app.route('/male_parent/upload_sku', methods=["POST"])
def upload_sku():
    if request.method == "POST":
        filename = request.files['myfile']
        data_time = datetime.datetime.now().strftime("%Y%m%d%H%M")
        index = request.form['index']
        msg, message = '', ''
        if index == "关联":
            path = f'D:/本地品名/本地品名关联{data_time}.xlsx'
            filename.save(os.path.join('UPLOAD_FOLDER', path))
            quantity = male_parent.Quantity()
            msg, message = quantity.upload_name(path)
        elif index == "解除关联":
            path = f'D:/本地品名/本地品名解除关联{data_time}.xlsx'
            filename.save(os.path.join('UPLOAD_FOLDER', path))
            quantity = male_parent.Quantity()
            msg, message = quantity.upload_relieve_sku(path)
        elif index == "创建品名":
            path = f'D:/本地品名/本地品名新增{data_time}.xlsx'
            filename.save(os.path.join('UPLOAD_FOLDER', path))
            quantity = male_parent.Quantity()
            msg, message = quantity.upload_sku(path)
        elif index == "创建品名并关联":
            path = f'D:/本地品名/本地品名新增并关联{data_time}.xlsx'
            filename.save(os.path.join('UPLOAD_FOLDER', path))
            quantity = male_parent.Quantity()
            msg, message = quantity.upload_sku(path)
            if msg:
                msg, message = quantity.upload_name(path)
        elif index == "删除":
            path = f'D:/本地品名/本地品名删除{data_time}.xlsx'
            filename.save(os.path.join('UPLOAD_FOLDER', path))
            quantity = male_parent.Quantity()
            msg = quantity.upload_delete_sku(path)
        if msg:
            if index == '关联' or index == '解除关联' or index == '创建品名并关联' or index == '删除':
                upload_json = parent_message.Quantity()
                executor.submit(upload_json.update_json)
            return json.dumps({'msg': "success", 'message': f"{index}成功"})
        else:
            return json.dumps({'msg': "error", 'message': message})
    else:
        return json.dumps({'msg': "error"})


@app.route('/male_parent/change_parent', methods=["POST"])
def change_parent():
    if request.method == "POST":
        dict_data = json.loads(request.form['data'])
        parent = dict_data['parent']
        change_parent = dict_data['change_parent']
        if parent and change_parent:
            quantity = male_parent.Quantity()
            msg, message = quantity.change_parent(parent.strip(), change_parent.strip())
            if msg:
                return json.dumps({'msg': "success", 'message': "更改成功"})
            else:
                return json.dumps({'msg': "error", 'message': message})
        else:
            return json.dumps({'msg': "error", 'message': "请先输入要更改的本地父体"})
    else:
        return json.dumps({'msg': "error"})


@app.route('/male_parent/change_male_sku', methods=["POST"])
def change_male_sku():
    if request.method == "POST":
        dict_data = json.loads(request.form['data'])
        sku = dict_data['sku']
        change_sku = dict_data['change_sku']
        if sku and change_sku:
            quantity = male_parent.Quantity()
            msg, message = quantity.change_sku(sku.strip(), change_sku.strip())
            if msg:
                return json.dumps({'msg': "success", 'message': "更改成功"})
            else:
                return json.dumps({'msg': "error", 'message': message})
        else:
            return json.dumps({'msg': "error", 'message': "请先输入要更改的本地父体"})
    else:
        return json.dumps({'msg': "error"})


@app.route('/male_parent/derive_table', methods=["POST"])
def derive_table():
    if request.method == "POST":
        dict_data = json.loads(request.form['data'])
        table_name = dict_data['table_name']
        if table_name == "table1":
            list_table = dict_data['list_msg'][0]
            list_header = []
        elif table_name == "table2":
            list_table = dict_data['list_msg'][1]
            list_header = []
        elif table_name == "parent_table":
            list_parent = dict_data['list_msg']['list']
            list_header = dict_data['list_header']
            quantity_parent = parent_message.Quantity()
            list_table = quantity_parent.get_list_parent(list_parent, len(list_header))
        else:
            list_amazon = dict_data['list_msg']['list']
            list_header = dict_data['list_header']
            quantity_parent = parent_message.Quantity()
            list_table = quantity_parent.get_list_amazon(list_amazon, len(list_header))
        if list_table:
            quantity = male_parent.Quantity()
            path, filename, download_name = quantity.write_xlsx(list_table, list_header)
            return json.dumps({'msg': "success", 'data': {"file": path, "filename": filename, "download_name": download_name}})
        else:
            if table_name == "table1":
                return json.dumps({'msg': "error", 'data': "请先获取本地父体详情"})
            else:
                return json.dumps({'msg': "error", 'data': "请先获取本地品名详情"})
    else:
        return json.dumps({'msg': "error"})


@app.route('/male_parent/get_male', methods=["POST"])
def get_male():
    if request.method == "POST":
        dict_data = json.loads(request.form['data'])
        index = dict_data['index']
        index_data = dict_data['index_data']
        quantity = male_parent.Quantity()
        list_data, index = quantity.get_male_parent(index, index_data)
        if list_data:
            return json.dumps({'msg': "success", 'data': list_data, 'index': index})
        else:
            return json.dumps({'msg': "error", 'message': "当前没有本地父体关系"})
    else:
        return json.dumps({'msg': 'error'})


@app.route('/male_parent/get_sku', methods=["POST"])
def get_sku_male():
    if request.method == "POST":
        dict_data = json.loads(request.form['data'])
        index = dict_data['index']
        index_data = dict_data['index_data']
        quantity = male_parent.Quantity()
        list_data, index = quantity.get_male_sku(index, index_data)
        if list_data:
            return json.dumps({'msg': "success", 'data': list_data, 'index': index})
        else:
            return json.dumps({'msg': "error", 'message': "当前没有本地品名关系"})
    else:
        return json.dumps({'msg': 'error'})


@app.route('/parent_message/get_list_male', methods=["GET"])
def get_list_male():
    if request.method == "GET":
        quantity = parent_message.Quantity()
        username = session.get('username')
        list_msg = quantity.get_list_male(username=username)
        if list_msg:
            return json.dumps({'msg': "success", 'data': list_msg})
        else:
            return json.dumps({'msg': "error", 'message': "当前没有本地父体"})
    else:
        return json.dumps({'msg': 'error'})


@app.route('/parent_message/get_list_header', methods=["GET"])
def get_list_header():
    if request.method == "GET":
        quantity = parent_message.Quantity()
        username = session.get('username')
        list_header = quantity.get_list_header(username)
        return json.dumps({'msg': "success", 'list_header': list_header})
    else:
        return json.dumps({'msg': 'error'})


@app.route('/parent_message/find_list_male', methods=["POST"])
def find_list_male():
    if request.method == "POST":
        dict_data = json.loads(request.form['data'])
        asin = dict_data['asin']
        username = session.get('username')
        quantity = parent_message.Quantity()
        list_msg = quantity.get_list_male(username=username, parent=asin)
        if list_msg:
            return json.dumps({'msg': "success", 'data': list_msg})
        else:
            return json.dumps({'msg': "error", 'message': "没有找到这个父体"})
    else:
        return json.dumps({'msg': 'error'})


@app.route('/parent_message/get_amazon_parent', methods=["POST"])
def get_amazon_parent():
    if request.method == "POST":
        dict_data = json.loads(request.form['data'])
        male_parent = dict_data['male_parent']
        if male_parent.find('*') >= 0:
            male_parent = male_parent[1:]
        quantity = parent_message.Quantity()
        list_msg = quantity.amazon_parent(male_parent)
        if list_msg:
            return json.dumps({'msg': "success", 'data': list_msg})
        else:
            return json.dumps({'msg': "error", 'message': f"{male_parent}没有关联的亚马逊父体"})
    else:
        return json.dumps({'msg': 'error'})


@app.route('/parent_message/menu_collect', methods=["POST"])
def menu_collect():
    if request.method == "POST":
        dict_data = json.loads(request.form['data'])
        male_parent = dict_data['male_parent']
        username = session.get('username')
        quantity = parent_message.Quantity()
        quantity.parent_collect(username=username, parent=male_parent)
        list_msg = quantity.get_list_male(username=username)
        if list_msg:
            return json.dumps({'msg': "success", 'data': list_msg})
        else:
            return json.dumps({'msg': "error", 'message': f"{male_parent}没有关联的亚马逊父体"})
    else:
        return json.dumps({'msg': 'error'})


@app.route('/parent_message/menu_unbind', methods=["POST"])
def menu_unbind():
    if request.method == "POST":
        dict_data = json.loads(request.form['data'])
        male_parent = dict_data['male_parent']
        username = session.get('username')
        quantity = parent_message.Quantity()
        quantity.parent_unbind(username=username, parent=male_parent)
        list_msg = quantity.get_list_male(username=username)
        if list_msg:
            return json.dumps({'msg': "success", 'data': list_msg})
        else:
            return json.dumps({'msg': "error", 'message': f"{male_parent}没有关联的亚马逊父体"})
    else:
        return json.dumps({'msg': 'error'})


@app.route('/parent_message/update_male', methods=["GET"])
def update_male_message():
    if request.method == "GET":
        quantity = parent_message.Quantity()
        msg, message = quantity.update_json()
        if msg:
            return json.dumps({'msg': "success", 'message': '更新成功'})
        else:
            return json.dumps({'msg': "error", 'message': message})
    else:
        return json.dumps({'msg': 'error'})


@app.route('/parent_message/find_list_asin', methods=["POST"])
def find_list_asin():
    if request.method == "POST":
        dict_data = json.loads(request.form['data'])
        asin = dict_data['asin']
        if asin.find('*') >= 0:
            asin = asin[1:]
        country = dict_data['country']
        quantity = parent_message.Quantity()
        if asin and country:
            data = dict_data['data']
            list_header = dict_data['list_header']
            list_amazon = quantity.get_amazon_msg(asin, country, list_header)
            if data['list']:
                list_parent = quantity.get_list_parent(data['list'], len(list_header))
                parent_asin = data['parent_asin']
            else:
                list_parent = []
                parent_asin = ''
            list_msg = quantity.string_splicing(list_parent, list_amazon, list_header, parent_asin, asin)
            # print(list_msg)
            if list_msg:
                return json.dumps({'msg': "success", 'data_html': list_msg})
            else:
                return json.dumps({'msg': "error", 'message': "没有找到这个父体"})
        else:
            if asin:
                return json.dumps({'msg': "error", 'message': "请先选择店铺"})
            else:
                return json.dumps({'msg': "error", 'message': "请先输入亚马逊父体"})
    else:
        return json.dumps({'msg': 'error'})


@app.route('/parent_message/find_asin_parent', methods=["POST"])
def find_asin_parent():
    if request.method == "POST":
        dict_data = json.loads(request.form['data'])
        asin = dict_data['asin']
        if asin.find('*') >= 0:
            asin = asin[1:]
        country = dict_data['country']
        quantity = parent_message.Quantity()
        # print(asin)
        if country:
            if asin.find('B0') >= 0:
                data = dict_data['data']
                list_header = dict_data['list_header']
                list_amazon = quantity.get_amazon_msg(asin, country, list_header)
                if data['list']:
                    list_parent = quantity.get_list_parent(data['list'], len(list_header))
                    parent_asin = data['parent_asin']
                else:
                    list_parent = []
                    parent_asin = ''
                # print(list_parent)
                list_msg = quantity.string_splicing(list_parent, list_amazon, list_header, parent_asin, asin)
                if list_msg:
                    # print("success")
                    return json.dumps({'msg': "success", 'data_html': list_msg, 'male': "亚马逊父体"})
                else:
                    # print("error")
                    return json.dumps({'msg': "error", 'message': "没有找到这个父体信息"})
            else:
                data = dict_data['data']
                list_header = dict_data['list_header']
                list_parent = quantity.get_male_msg(asin, country, list_header)
                if list_parent:
                    if data['list']:
                        list_amazon = quantity.get_list_amazon(data['list'], len(list_header))
                        amazon_asin = data['amazon_asin']
                    else:
                        list_amazon = []
                        amazon_asin = ''
                    list_msg = quantity.string_splicing(list_parent, list_amazon, list_header, asin, amazon_asin)
                    if list_msg:
                        # print("success")
                        return json.dumps({'msg': "success", 'data_html': list_msg, 'male': "本地父体"})
                    else:
                        # print("error")
                        return json.dumps({'msg': "error", 'message': "没有找到这个父体信息"})
                else:
                    # print("error")
                    return json.dumps({'msg': "error", 'message': "没有找到这个父体信息"})
        else:
            return json.dumps({'msg': "error", 'message': "请先选择店铺"})
    else:
        return json.dumps({'msg': 'error'})


@app.route('/parent_message/change_column', methods=["POST"])
def change_column():
    if request.method == "POST":
        dict_data = json.loads(request.form['data'])
        data = dict_data['data']
        list_header = dict_data['list_header']
        country = dict_data['country']
        username = session.get('username')
        quantity = parent_message.Quantity()
        msg, message = quantity.change_list_header(username, list_header)
        if msg:
            parent_asin = data['parent_asin']
            amazon_asin = data['amazon_asin']
            if parent_asin or amazon_asin:
                list_1 = []
                list2 = []
                if parent_asin:
                    list_1 = quantity.get_male_msg(parent_asin, country, list_header)
                if amazon_asin:
                    list2 = quantity.get_amazon_msg(amazon_asin, country, list_header)
                list_msg = quantity.string_splicing(list_1, list2, list_header, data['parent_asin'], data['amazon_asin'])
                return json.dumps({'msg': "success", 'data_html': list_msg})
            else:
                return json.dumps({'msg': "error1"})
        else:
            return json.dumps({'msg': "error2", 'message': f'列配置失败，{message}'})
    else:
        return json.dumps({'msg': 'error'})


@app.route('/parent_message/contrast_parent', methods=["POST"])
def contrast_parent():
    if request.method == "POST":
        dict_data = json.loads(request.form['data'])
        data = dict_data['data']
        list_header = dict_data['list_header']
        quantity = parent_message.Quantity()
        list_parent = quantity.get_list_parent(data['list'], len(list_header))
        list_amazon = quantity.get_list_amazon(data['list'], len(list_header))
        if list_amazon and list_parent:
            list_1, list2 = quantity.contrast_parent(list_parent, list_amazon)
            list_msg = quantity.string_splicing(list_1, list2, list_header, data['parent_asin'], data['amazon_asin'])
            return json.dumps({'msg': "success", 'data_html': list_msg})
        else:
            return json.dumps({'msg': "error", 'message': "请先获取要对比的父体"})
    else:
        return json.dumps({'msg': 'error'})


@app.route('/parent_message/windows_msg', methods=["POST"])
def windows_msg():
    if request.method == "POST":
        dict_data = json.loads(request.form['data'])
        sku = dict_data['sku']
        if sku:
            asin = dict_data['asin']
            if asin.find('*') >= 0:
                asin = asin[1:]
            country = dict_data['country']
            quantity = parent_message.Quantity()
            list_1 = quantity.windows_msg(sku, asin, country)
            if list_1:
                return json.dumps({'msg': "success", 'data': list_1})
            else:
                return json.dumps({'msg': "error", 'message': "SKU详情获取失败"})
        else:
            return json.dumps({'msg': "error", 'message': "SKU详情获取失败"})
    else:
        return json.dumps({'msg': 'error'})


@app.route('/parent_message/ascending_sort', methods=["POST"])
def ascending_sort():
    if request.method == "POST":
        dict_data = json.loads(request.form['data'])
        data = dict_data['data']
        list_header = dict_data['list_header']
        index = dict_data['index']
        sort_asin = dict_data['sort_asin']
        quantity = parent_message.Quantity()
        list_parent = quantity.get_list_parent(data['list'], len(list_header))
        list_amazon = quantity.get_list_amazon(data['list'], len(list_header))
        if list_amazon or list_parent:
            index_num = int(list_header.index(index) + 2)
            list_1, list2 = quantity.ascending_sort(list_parent, list_amazon, index_num, sort_asin)
            list_msg = quantity.string_splicing(list_1, list2, list_header, data['parent_asin'], data['amazon_asin'])
            return json.dumps({'msg': "success", 'data_html': list_msg})
        else:
            return json.dumps({'msg': "error", 'message': "请先获取数据"})
    else:
        return json.dumps({'msg': 'error'})


@app.route('/parent_message/descending_sort', methods=["POST"])
def descending_sort():
    if request.method == "POST":
        dict_data = json.loads(request.form['data'])
        data = dict_data['data']
        list_header = dict_data['list_header']
        index = dict_data['index']
        sort_asin = dict_data['sort_asin']
        quantity = parent_message.Quantity()
        list_parent = quantity.get_list_parent(data['list'], len(list_header))
        list_amazon = quantity.get_list_amazon(data['list'], len(list_header))
        if list_amazon or list_parent:
            index_num = int(list_header.index(index) + 2)
            list_1, list2 = quantity.descending_sort(list_parent, list_amazon, index_num, sort_asin)
            list_msg = quantity.string_splicing(list_1, list2, list_header, data['parent_asin'], data['amazon_asin'])
            return json.dumps({'msg': "success", 'data_html': list_msg})
        else:
            return json.dumps({'msg': "error", 'message': "请先获取数据"})
    else:
        return json.dumps({'msg': 'error'})


@app.route('/parent_message/ascending_sort2', methods=["POST"])
def ascending_sort2():
    if request.method == "POST":
        dict_data = json.loads(request.form['data'])
        list_msg = dict_data['list_msg']
        index = dict_data['index']
        quantity = parent_message.Quantity()
        list_data = quantity.ascending_sort2(list_msg, index)
        if list_data:
            return json.dumps({'msg': "success", 'data': list_data})
        else:
            return json.dumps({'msg': "error", 'message': "发生未知错误"})
    else:
        return json.dumps({'msg': 'error'})


@app.route('/parent_message/descending_sort2', methods=["POST"])
def descending_sort2():
    if request.method == "POST":
        dict_data = json.loads(request.form['data'])
        list_msg = dict_data['list_msg']
        index = dict_data['index']
        quantity = parent_message.Quantity()
        list_data = quantity.descending_sort2(list_msg, index)
        if list_data:
            return json.dumps({'msg': "success", 'data': list_data})
        else:
            return json.dumps({'msg': "error", 'message': "发生未知错误"})
    else:
        return json.dumps({'msg': 'error'})


@app.route('/parent_message/download_parent', methods=["POST"])
def download_parent():
    if request.method == "POST":
        dict_data = json.loads(request.form['data'])
        asin = dict_data['asin']
        data_time = dict_data['data_time']
        quantity = parent_message.Quantity()
        msg, message = quantity.download_parent(asin, data_time)
        if msg:
            return json.dumps({'msg': "success", 'filename': message[1], "file": message[0]})
        else:
            return json.dumps({'msg': "error", 'message': message})
    else:
        return json.dumps({'msg': 'error'})


@app.route('/parent_message/menu_relieve_sku', methods=["POST"])
def menu_relieve_sku():
    if request.method == "POST":
        dict_data = json.loads(request.form['data'])
        parent_asin = dict_data['parent_asin']
        if parent_asin.find('*') >= 0:
            parent_asin = parent_asin[1:]
        sku = dict_data['sku']
        quantity = male_parent.Quantity()
        msg, message = quantity.relieve_male(parent_asin, sku)
        if msg:
            upload_json = parent_message.Quantity()
            executor.submit(upload_json.update_json)
            return json.dumps({'msg': "success", 'message': message})
        else:
            return json.dumps({'msg': "error", 'message': message})
    else:
        return json.dumps({'msg': 'error'})


@app.route('/parent_message/menu_relevance_sku', methods=["POST"])
def menu_relevance_sku():
    if request.method == "POST":
        dict_data = json.loads(request.form['data'])
        parent_asin = dict_data['parent_asin']
        if parent_asin.find('*') >= 0:
            parent_asin = parent_asin[1:]
        sku = dict_data['sku']
        quantity = male_parent.Quantity()
        msg, message = quantity.relevance_male(parent_asin, sku)
        if msg:
            upload_json = parent_message.Quantity()
            executor.submit(upload_json.update_json)
            return json.dumps({'msg': "success", 'message': message})
        else:
            return json.dumps({'msg': "error", 'message': message})
    else:
        return json.dumps({'msg': 'error'})


@app.route('/parent_message/find_parent_sku', methods=["POST"])
def find_parent_sku():
    if request.method == "POST":
        dict_data = json.loads(request.form['data'])
        data = dict_data['data']
        list_header = dict_data['list_header']
        local_sku = dict_data['local_sku']
        shop = dict_data['shop']
        quantity = parent_message.Quantity()
        list_parent = quantity.get_list_parent(data['list'], len(list_header))
        list_amazon = quantity.get_list_amazon(data['list'], len(list_header))
        if list_amazon or list_parent:
            parent_asin = data['parent_asin']
            amazon_asin = data['amazon_asin']
            list_1, list2 = quantity.find_parent_sku(list_parent, list_amazon, local_sku, shop, parent_asin, amazon_asin, list_header)
            list_msg = quantity.string_splicing(list_1, list2, list_header, parent_asin, amazon_asin)
            return json.dumps({'msg': "success", 'data_html': list_msg})
        else:
            return json.dumps({'msg': "error", 'message': "请先获取要搜索的父体"})
    else:
        return json.dumps({'msg': 'error'})


@app.route('/upload_image/get_sku_image', methods=["GET"])
def get_sku_image():
    if request.method == "GET":
        quantity = upload_image.Upload_Image()
        list_msg = quantity.get_sql_sku()
        if list_msg:
            return json.dumps({'msg': "success", 'data': list_msg})
        else:
            return json.dumps({'msg': "error", 'message': '当前没有未同步图片的SKU'})
    else:
        return json.dumps({'msg': 'error'})


@app.route('/upload_image/get_class_image', methods=["POST"])
def get_class_image():
    if request.method == "POST":
        dict_data = json.loads(request.form['data'])
        index = dict_data['index']
        index_data = dict_data['index_data']
        if index:
            quantity = upload_image.Upload_Image()
            if index_data:
                list_msg = quantity.get_class_sku(index, index_data)
            else:
                list_msg = quantity.get_sql_sku()
            if list_msg:
                return json.dumps({'msg': "success", 'data': list_msg})
            else:
                return json.dumps({'msg': "error", 'message': '当前没有未同步图片的SKU'})
        else:
            return json.dumps({'msg': "error", 'message': '请先选择索引'})
    else:
        return json.dumps({'msg': 'error'})


@app.route('/upload_image/get_image_msg', methods=["POST"])
def get_image_msg():
    if request.method == "POST":
        dict_data = json.loads(request.form['data'])
        male_name = dict_data['male_name']
        quantity = upload_image.Upload_Image()
        list_msg = quantity.get_image_msg(male_name)
        if list_msg:
            return json.dumps({'msg': "success", 'data': list_msg})
        else:
            return json.dumps({'msg': "error", 'message': '当前没有有图片的SKU'})
    else:
        return json.dumps({'msg': 'error'})


@app.route('/upload_image/update_image_msg', methods=["GET"])
def update_image_msg():
    if request.method == "GET":
        quantity = upload_image.Quantity()
        msg = quantity.get_flag()
        if msg:
            executor.submit(quantity.update_image_msg())
            return json.dumps({'msg': "success"})
        else:
            return json.dumps({'msg': "error", 'message': '正在更新图片信息，请稍后再试'})
    else:
        return json.dumps({'msg': 'error'})


if __name__ == '__main__':
    app.after_request(after_request)
    app.run(port=80, debug=False, threaded=False, processes=100)
    # app.run(port=80, debug=False)
