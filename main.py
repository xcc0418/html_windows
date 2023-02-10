from flask import Flask, render_template, request
from werkzeug.utils import secure_filename
import pymysql
import os
import requests
import json
import global_var
import time
from reportlab.pdfgen import canvas
import barcode
# from pystrich.code128 import Code128Encoder
from PIL import Image, ImageDraw, ImageFont
from barcode.writer import ImageWriter
import global_var
import search
import shipment
# import encode
from waitress import serve

app = Flask(__name__, template_folder='./static/templates')
app.config['UPLOAD_FOLDER'] = 'F:/html_windows/static/FNSKU装箱信息'


# 跨域支持
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


def save_pdf(fnsku, pa_name, num, name):
    enc = barcode.get_barcode_class('code128')
    # 生成条形码
    encoder = enc(name, writer=ImageWriter())
    encoder.save("C:/图片/photo/{name}".format(name=name), {'format': 'PNG', 'font_size': 40, 'dpi': 600})
    os.makedirs(f"C:/图片/{name}".format(name=name))
    jpg_path = 'C:/图片/photo/{name}.png'.format(name=name)
    pdf_path = 'C:/图片/{pa}/{name}.pdf'.format(pa=name, name=name)
    # 向条形码图片中写入内容
    # img = Image.new('RGB', (378, 567), (255, 255, 255)),'module_width': 0.1, 'module_height': 7
    img = Image.new('RGB', (756, 1134), (255, 255, 255))
    pyq = Image.open(jpg_path)
    img.paste(pyq, (0, 584))
    draw = ImageDraw.Draw (img)
    i = 1
    j = 0
    font = ImageFont.truetype ("simhei.ttf", 40, encoding="unic")  # 设置字体
    # 将品名和个数依次写入图片中
    text_data = name
    if len(text_data) > 17 and len (text_data) < 36:
        draw.text((20, 550 - i * 36 - 46), u'{text}'.format(text=text_data[0:18]), 'black', font)
        draw.text((20, 550 - i * 36), u'{text}'.format(text=text_data[18:]), 'black', font)
        draw.text((20, 550 - i * 36 + 46), u'{text}'.format(text=fnsku), 'black', font)
        draw.text((300, 550 - i * 36 + 46), u'{text}'.format(text=num), 'black', font)
        draw.text((400, 550 - i * 36 + 46), u'{text}'.format(text=pa_name), 'black', font)
        i += 4
        j += 1
    elif len(text_data) >= 36:
        draw.text((20, 550 - i * 36 - 92), u'{text}'.format(text=text_data[0:18]), 'black', font)
        draw.text((20, 550 - i * 36 - 46), u'{text}'.format(text=text_data[18:36]), 'black', font)
        draw.text((20, 550 - i * 36), u'{text}'.format(text=text_data[36:]), 'black', font)
        draw.text((20, 550 - i * 36 + 46), u'{text}'.format(text=fnsku), 'black', font)
        draw.text((300, 550 - i * 36 + 46), u'{text}'.format(text=num), 'black', font)
        draw.text((400, 550 - i * 36 + 46), u'{text}'.format(text=pa_name), 'black', font)
        i += 4
        j += 2
    else:
        draw.text((20, 550 - i * 36), u'{text}'.format(text=text_data), 'black', font)
        draw.text((20, 550 - i * 36 + 46), u'{text}'.format(text=fnsku), 'black', font)
        draw.text((300, 550 - i * 36 + 46), u'{text}'.format(text=num), 'black', font)
        draw.text((400, 550 - i * 36 + 46), u'{text}'.format(text=pa_name), 'black', font)
        i += 3
        j += 1
    img.save(jpg_path, 'JPEG', quality=100)
    jpg_to_pdf(jpg_path, pdf_path)
    return pdf_path


def jpg_to_pdf(jpg, pdf_path):
    (w, h) = Image.open(jpg).size
    user = canvas.Canvas(pdf_path, pagesize=(w, h))
    user.drawImage(jpg, 0, 0, w, h)
    user.showPage()
    user.save()


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
        list_pa = None
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
                print(fnsku_msg)
                return json.dumps(fnsku_msg)
            else:
                fnsku_msg = {'msg': 'error', 'data': '请先获取箱号'}
                print(fnsku_msg)
                return json.dumps(fnsku_msg)
        # else:
        #     fnsku_msg = {'msg': 'error', 'data': '请先输入fnsku'}
        #     print(fnsku_msg)
        #     return json.dumps(fnsku_msg)


@app.route('/pack_pa', methods=["POST"])
def pack_pa():
    if request.method == 'POST':
        dict_data = json.loads(request.form['data'])
        print(dict_data)
        if dict_data:
            pa_name = dict_data['pa_name']
            fnsku = dict_data['fnsku']
            num = dict_data['num']
            name = dict_data['name']
            time1 = time.strftime ("%Y-%m-%d-%H-%M", time.localtime ())
            sql = "INSERT INTO `storage`.`warehouse`(`箱号`,`FNSKU1`,`数量1`,`状态`, `创建时间`,`修改时间`) VALUES ('%s','%s',%d,'%s','%s','%s')" % (
            pa_name, fnsku, num, '已打包', time1, time1)
            result = func(sql, m='w')
            if result:
                pdf_path = save_pdf(fnsku, pa_name, num, name)
                msg = {'msg': 'success', 'data': {'filename': pdf_path}}
            else:
                msg = {'msg': 'error', 'data': '装箱失败'}
        else:
            msg = {'msg': 'error', 'data': '请先开始装箱操作'}
        return json.dumps(msg)


@app.route('/search_msg', methods=["POST"])
def search_msg():
    if request.method == 'POST':
        dict_data = json.loads(request.form['data'])
        print(dict_data)
        if dict_data:
            index = dict_data['index']
            index_data = dict_data['index_data']
            result = search.get_msg(index, index_data)
            print(result)
            if result:
                msg = {'msg': "success", 'data': result}
                print(msg)
                return json.dumps(msg)
            else:
                msg = {'msg': "error", 'data': '没有找到这个箱号'}
                return json.dumps(msg)


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


@app.route('/uploader', methods=["POST"])
def uploader():
    if request.method == 'POST':
        filename = request.files['file']
        print(filename)
        # if filename.find('xlsx') >= 0 or filename.find('xls') >= 0:
        filename.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(filename.filename)))
        download_file = search.get_warehouse(filename)
        if download_file:
            return json.dumps({'msg': 'success', 'data': {'filename': download_file}})
        else:
            return json.dumps({'msg': 'error'})
        # else:
        #     return {'msg': 'error', 'data': '请选择表格文件'}


@app.route('/get_order', methods=["POST"])
def get_order():
    if request.method == 'POST':
        dict_data = json.loads(request.form['data'])
        print(dict_data)
        if dict_data:
            index = dict_data['index']
            order = dict_data['order']
            msg = shipment.get_order_msg(index, order)
            if msg:
                print(msg)
                return json.dumps({'msg': 'success', 'data': msg})
            else:
                return json.dumps({'msg': 'error'})


@app.route('/shipment_upload', methods=["POST"])
def shipment_upload():
    if request.method == 'POST':
        dict_data = json.loads(request.form['data'])
        print(dict_data)
        if dict_data:
            list_index = list(dict_data.keys())
            list_num = list(dict_data.values())
            msg = shipment.uploading_pdd(list_index, list_num)
            if msg:
                return json.dumps({'msg': "success"})
            else:
                return json.dumps({'msg': 'error'})


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


@app.route('/get_number', methods=["POST"])
def get_number():
    if request.method == 'POST':
        dict_data = json.loads(request.form['data'])
        list_fnsku = dict_data['list_fnsku']
        data_num = dict_data['data_num']
        list_order_num = dict_data['list_order_num']
        for i in range(0, len(list_order_num)):
            num_order = 0
            for j in data_num[i]:
                num_order += j
            if num_order < list_order_num[i]:
                return json.dumps({'msg': 'error', 'data': f"{list_fnsku[i]}货物总数量不足，没有完全装箱！"})
            if num_order > list_order_num[i]:
                return json.dumps({'msg': 'error', 'data': f"{list_fnsku[i]}货物总数量超出申报量，请仔细检查！"})


@app.route('/FBA_shipment/get_fnsku', methods=["POST"])
def get_fnsku():
    if request.method == 'POST':
        dict_data = json.loads(request.form['data'])
        index = dict_data['index'].strip()
        if len(index) == 10:
            return json.dumps({'msg': "success", 'data': {'fnsku': index, 'num': 1}})
        if len(index) == 14:
            result = func("select `FNSKU1`, `数量1` from `storage`.`warehouse` where `箱号` = '%s' and `状态` = '已打包'")
            if result:
                return json.dumps({'msg': "success", 'data': {'fnsku': result[0][0], 'num': result[0][1]}})
            else:
                return json.dumps({'msg': 'error', 'data': f"这个{index}箱号没找到，请重试！"})
        else:
            return json.dumps({'msg': 'error', 'data': f"{index}格式不正确，请检查输入是否正确！"})


if __name__ == '__main__':
    app.after_request(after_request)
    app.run(port=80)
