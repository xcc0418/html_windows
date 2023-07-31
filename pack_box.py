import pymysql
import os
from reportlab.pdfgen import canvas
import barcode
from PIL import Image, ImageDraw, ImageFont
from barcode.writer import ImageWriter


class Pack_Box():
    def __init__(self):
        self.connection = None
        self.cursor = None

    # 数据库：由于数据库使用花生壳的内网穿透服务，所以连接有时不稳定，比如一个连接的链接时间过长有可能会被数据库主动kill，或者在某一个时间段内多次频繁的连接数据库，会让数据库无响应。
    # 这里将数据库的连接与关闭封装成两个函数，在进行数据库的访问时，合理安排连接与关闭时间。
    # self.connection。commit()方法：如果一个一个commit数据库语句会导致程序执行速率慢，如果将所有语句一起commit有可能会导致数据库宕机。
    # 示例：下面这个循环大概有3000次，如果将这循环里的所有数语句一次性提交数据库，会导致数据宕机，所以这里设置每一百个语句提交一次数据库，
    #     flag = 0
    #     for i in list_msg:
    #          sql3 = "insert into `data_read`.`product_image`(`本地品名`, `SKU`,`品名`, `状态`) VALUES" \
    #                 "('%s','%s','%s','%s')" % (i[0], i[1], i[2], i[3])
    #         self.cursor.execute(sql3)
    #         flag += 1
    #         if flag % 100 == 0:
    #             self.connection.commit()
    #     self.connection.commit()
    # 关于pymysql模块cursor、fetchall、commit方法区别请参考：https://blog.csdn.net/XC_SunnyBoy/article/details/108546128
    # 数据库连接函数
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

    # 关闭数据库
    def sql_close(self):
        self.cursor.close()
        self.connection.close()

    # 将箱号的装箱信息及条码生成PDF文件
    def save_pdf(self, fnsku, pa_name, num, name, supplier):
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
        font = ImageFont.truetype("simhei.ttf", 40, encoding="unic")  # 设置字体
        # 将品名和个数依次写入图片中
        text_data = name
        if len (text_data) > 17 and len (text_data) < 36:
            draw.text((20, 550 - i * 36 - 46), u'{text}'.format(text=text_data[0:18]), 'black', font)
            draw.text((20, 550 - i * 36), u'{text}'.format(text=text_data[18:]), 'black', font)
            draw.text((20, 550 - i * 36 + 46), u'{text}'.format(text=fnsku), 'black', font)
            draw.text((300, 550 - i * 36 + 46), u'{text}'.format(text=num), 'black', font)
            draw.text((400, 550 - i * 36 + 46), u'{text}'.format(text=supplier), 'black', font)
            i += 4
            j += 1
        elif len (text_data) >= 36:
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
        self.jpg_to_pdf(jpg_path, pdf_path)
        path = f'../图片/{pa_name}/{pa_name}.pdf'
        return path

    # jpg格式转pdf格式
    def jpg_to_pdf(self, jpg, pdf_path):
        (w, h) = Image.open(jpg).size
        user = canvas.Canvas(pdf_path, pagesize=(w, h))
        user.drawImage(jpg, 0, 0, w, h)
        user.showPage()
        user.save()

    def find_pa(self, pa_name):
        self.sql()
        sql = "select * from `storage`.`warehouse` where `箱号` = '%s'" % pa_name
        self.cursor.execute(sql)
        result = self.cursor.fetchall()
        self.sql_close()
        if result:
            msg, name = self.get_name(result[0]['FNSKU1'])
            return True, {'箱号': pa_name, 'fnsku': result[0]['FNSKU1'], '品名': name, '装箱数量': result[0]['数量1'], '装箱状态': result[0]['状态']}
        else:
            return False, f"{pa_name}未找到, 请检查输入是否正确"

    def get_name(self, fnsku):
        self.sql()
        sql = "SELECT `品名` FROM `data_read`.`listing` where `FNSKU`='%s'" % fnsku
        self.cursor.execute(sql)
        result = self.cursor.fetchall()
        self.sql_close()
        if result:
            return True, result[0]['品名']
        else:
            return False, f'没有找到{fnsku}，请检查。'

    def pack_pa(self, pa_name, fnsku, name, num):
        try:
            self.sql()
            sql1 = "SELECT `供应商` FROM `data_read`.`listing` where `FNSKU`='%s'" % fnsku
            # 提交数据库语句
            self.cursor.execute(sql1)
            # 获取数据库查找语句的返回结果
            supplier = self.cursor.fetchall()[0]['供应商']
            sql2 = "INSERT INTO `storage`.`warehouse`(`箱号`,`FNSKU1`,`数量1`,`状态`) VALUES ('%s','%s',%d,'%s')" % (pa_name, fnsku, num, '已打包')
            self.cursor.execute(sql2)
            # 执行提交的增、删、改语句
            self.connection.commit()
            pdf_path = self.save_pdf(fnsku, pa_name, num, name, supplier)
            return True, pdf_path
        except Exception as e:
            # 数据库语句回滚
            self.connection.rollback()
            print(e)
            return False, str(e)

    def delect_box(self, pa_name):
        self.sql()
        sql1 = "SELECT `状态` from `storage`.`warehouse` WHERE `箱号` = '%s'" % pa_name
        self.cursor.execute(sql1)
        result = self.cursor.fetchall()
        self.sql_close()
        if result:
            if result[0]['状态'] == "已删除":
                return False, '这箱物料已删除'
            elif result[0]['状态'] == "已出货":
                return False, "这箱物料已出货"
            else:
                self.sql()
                status = "已删除"
                sql2 = "UPDATE `storage`.`warehouse` SET `状态` = '%s' WHERE `箱号` = '%s'" % (status, pa_name)
                self.cursor.execute(sql2)
                self.connection.commit()
                self.sql_close()
                return True, '删除成功'
        else:
            return False, '请查看箱号是否正确'

