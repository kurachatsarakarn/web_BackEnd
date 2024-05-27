from flask import Flask,render_template,request,jsonify,send_file,make_response,session
import mysql.connector
from mysql.connector import Error
from flask_socketio import SocketIO
from camera import VideoCamera
import os
from flask_cors import CORS
import base64
import cv2
import numpy as np
from io import BytesIO
from PIL import Image
from datetime import datetime

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False
CORS(app)  # เปิดใช้งาน CORS
socketio = SocketIO(app, cors_allowed_origins="*")
camera = VideoCamera()

# host='192.168.2.130'
# user='test'
# password='test'
# database='cornai'


host='localhost'
user='root'
password=''
database='cornai'

######################################################################
#API base
@app.route('/')
def index():
    return ""
######################################################################

######################################################################
# API Product
#ดึงproductทั้งหมด
@app.route('/api/products' ,methods=['GET'])
def products():
    try:
        mydb = mysql.connector.connect(host=host,user=user,password=password,database=database)
        mycursor = mydb.cursor(dictionary=True)
        mycursor.execute("SELECT * FROM `products`")
        myresult = mycursor.fetchall()
        mydb.close()
    except Error as e:
        print(f"Error: {e}")
        return make_response(jsonify({"msg": e}),500)    
    return make_response(jsonify(myresult),200)

#ดึงproductตามid
@app.route('/api/products/<id>' ,methods=['GET'])
def products_id_losts(id):
    try:
        mydb = mysql.connector.connect(host=host,user=user,password=password,database=database)
        mycursor = mydb.cursor(dictionary=True)
        sql = "SELECT * FROM products  WHERE products.id_lots = %s;"
        val = (f"{id}",)
        mycursor.execute(sql,val)
        result = mycursor.fetchall()
        mydb.close()
    except Error as e:
        print(f"Error: {e}")
        return make_response(jsonify({"msg": e}),500)
    return make_response(jsonify(result),200)

#insert product
@app.route('/api/products', methods=['POST'])
def products_insert():
    try:
        mydb = mysql.connector.connect(host=host, user=user, password=password, database=database)
        data = request.get_json()
        mycursor = mydb.cursor(dictionary=True)
        query = "SELECT * FROM user WHERE user.name = %s"
        valquery = (data['user'],)
        mycursor.execute(query,valquery)
        result = mycursor.fetchall()
        print(result[0]['id'])
        sql = """INSERT INTO products (id_lots, id_user, BreakClean, CompleteSeeds, Dust, MoldSpores, broken, fullbrokenseeds, path)
                 VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"""
        val = (
             data['id'],result[0]['id'], data['BreakClean'], data['CompleteSeeds'], data['Dust'],
            data['MoldSpores'], data['broken'], data['fullbrokenseeds'], data['path']
        )
        mycursor.execute(sql, val)
        mydb.commit()
        mycursor.close()
        mydb.close()
        return make_response(jsonify({"rowcount": mycursor.rowcount}), 200)
    except Error as e:
        error_msg = str(e)
        print(f"Error: {error_msg}")
        return make_response(jsonify({"msg": error_msg}), 500)

#update product
@app.route('/api/products', methods=['PUT'])
def products_update():
    try:
        mydb = mysql.connector.connect(host=host,user=user,password=password,database=database)
        data = request.get_json()
        mycursor = mydb.cursor(dictionary=True)
        sql = "UPDATE `products` SET `id_lots`=%s WHERE products.id = %s;"
        val = (data['id_lots'],data['id'])
        mycursor.execute(sql, val)
        mydb.commit()
        mydb.close()
    except Error as e:
        print(f"Error: {e}")
        return make_response(jsonify({"msg": e}),500)
    return make_response(jsonify({"rowcount": mycursor.rowcount}),200)

#delete product
@app.route('/api/products/<id>', methods=['DELETE'])
def products_delete(id):
    try:
        mydb = mysql.connector.connect(host=host,user=user,password=password,database=database)
        mycursor = mydb.cursor(dictionary=True)
        sql = "DELETE FROM `products` WHERE products.id = %s;"
        val = (f"{id}",)
        mycursor.execute(sql, val)  
        mydb.commit()
        mydb.close()
    except Error as e:
        print(f"Error: {e}")
        return make_response(jsonify({"msg": e}),500)
    return make_response(jsonify({"rowcount": mycursor.rowcount}),200)
######################################################################



######################################################################
# API Lots

#ดึงข้อมูลเป็นหน้าๆ
@app.route('/api/lots/<page>', methods=['GET'])
def lots_page(page):
    try:
        page_value = int(page)
        max_value = (page_value*8)-1 
        min_value = (page_value-1)*8
        print(max_value)
        print(min_value)
        if max_value is None or min_value is None:
            return make_response(jsonify({"msg": "Missing 'max' or 'min' in request"}), 400)

        sql = """
            SELECT lots.id as id,lots.name as lots,lots.date as date,t2.path as path , status.status as status
            FROM lots INNER JOIN (SELECT p.id_lots AS max_id, p.path FROM products AS p
            JOIN (SELECT MAX(id) AS id, id_lots FROM products GROUP BY id_lots) AS p_max 
            ON p.id = p_max.id AND p.id_lots = p_max.id_lots) as t2
			on t2.max_id = lots.id 
            left JOIN status ON lots.id = status.id_lots
           	ORDER BY lots.id DESC 
            LIMIT %s OFFSET %s;
        """
        values = (max_value, min_value)
        with mysql.connector.connect(host=host, user=user, password=password, database=database) as mydb:
            with mydb.cursor(dictionary=True) as mycursor:
                mycursor.execute(sql, values)
                myresult = mycursor.fetchall()
    except Error as e:
        print(f"Error: {e}")
        return make_response(jsonify({"msg": str(e)}), 500)
    return make_response(jsonify(myresult), 200)
 

#ดึงจำนวนหน้า
@app.route('/api/lots/sum',methods=['GET'])
def lots_sum():
    try:
        mydb = mysql.connector.connect(host=host,user=user,password=password,database=database)
        mycursor = mydb.cursor(dictionary=True)
        mycursor.execute("SELECT COUNT(lots.id) as sum FROM lots;")
        myresult = mycursor.fetchall()
        count = myresult[0]['sum']
        sum = count//8
        if(count%8 != 0):
            sum += 1
        mydb.close()
    except Error as e:
        print(f"Error: {e}")
        return make_response(jsonify({"msg": e}),500)
    return make_response(jsonify({"sum":sum}),200)

#ดึงจำนวนหน้าที่ค้นหา
@app.route('/api/lots/search/sum',methods=['POST'])
def lots_like_sum():
    try:
        mydb = mysql.connector.connect(host=host,user=user,password=password,database=database)
        mycursor = mydb.cursor(dictionary=True)
        data = request.get_json()
        id = data.get('id')
        sql = "SELECT COUNT(lots.id) as sum FROM lots WHERE lots.name LIKE %s;"
        val = (f"%{id}%",)
        mycursor.execute(sql,val)
        myresult = mycursor.fetchall()
        count = myresult[0]['sum']
        sum = count//8
        if(count%8 != 0):
            sum += 1
        mydb.close()
    except Error as e:
        print(f"Error: {e}")
        return make_response(jsonify({"msg": e}),500)
    return make_response(jsonify(sum),200)

#ดึงหน้าที่ค้นหา
@app.route('/api/lots/search',methods=['POST'])
def lots_like_id():
    try:
        mydb = mysql.connector.connect(host=host,user=user,password=password,database=database)
        mycursor = mydb.cursor(dictionary=True)
        data = request.get_json()
        page = data.get('page')
        id = data.get('id')
        page_value = int(page)
        max_value = (page_value*8)-1 
        min_value = (page_value-1)*8
        sql = ("""
        SELECT lots.id as id,lots.name as lots,lots.date as date,t2.path as path
            FROM lots INNER JOIN (SELECT p.id_lots AS max_id, p.path FROM products AS p
            JOIN (SELECT MAX(id) AS id, id_lots FROM products GROUP BY id_lots) AS p_max 
            ON p.id = p_max.id AND p.id_lots = p_max.id_lots) as t2
			on t2.max_id = lots.id
            WHERE lots.name LIKE %s
           	ORDER BY lots.id DESC 
            LIMIT %s OFFSET %s;
        """)
        val = ("%"+id+"%",max_value,min_value) 
        mycursor.execute(sql, val)
        myresult = mycursor.fetchall()
        mydb.close()
    except Error as e:
        print(f"Error: {e}")
        return make_response(jsonify({"msg": e}),500)
    return make_response(jsonify(myresult),200)

#ดึงล็อตตามid
@app.route('/api/lots/<id>', methods=['GET'])
def lots_id(id):
    try:
        mydb = mysql.connector.connect(host=host,user=user,password=password,database=database)
        mycursor = mydb.cursor(dictionary=True)
        sql = ("SELECT * FROM lots WHERE lots.id = %s;")
        val = (f"{id}",)
        mycursor.execute(sql,val)
        myresult = mycursor.fetchall()
        mydb.close()
    except Error as e:
        print(f"Error: {e}")
        return make_response(jsonify({"msg": e}),500)
    return make_response(jsonify(myresult),200)

#ดึงล็อตทั้งหมด
@app.route('/api/lots', methods=['GET'])
def lots():
    try:
        mydb = mysql.connector.connect(host=host,user=user,password=password,database=database)
        mycursor = mydb.cursor(dictionary=True)
        sql = "SELECT * FROM lots;"
        mycursor.execute(sql)
        myresult = mycursor.fetchall()
        mydb.close()
        return make_response(jsonify(myresult),200)
    except Error as e:
        print(f"Error: {e}")
        return make_response(jsonify({"msg": e}),500)

#สร้างล็อต
@app.route('/api/lots', methods=['POST'])
def lots_insert():
    try:
        mydb = mysql.connector.connect(host=host,user=user,password=password,database=database)
        mycursor = mydb.cursor(dictionary=True)
        data = request.get_json()
        now = datetime.now()
        current_time = now.strftime("%Y-%m-%d")
        name = data['name']
        sql = ("INSERT INTO `lots`(`name`, `date`) VALUES (%s,%s);")
        val = (name,current_time)
        mycursor.execute(sql, val)
        mydb.commit()
        mydb.close()
    except Error as e:
        print(f"Error: {e}")
        return make_response(jsonify({"msg": e}),500)
    return make_response(jsonify({"rowcount": mycursor.rowcount}),200)

#ลบล็อต
@app.route('/api/lots/<id>', methods=['DELETE'])
def lots_delete(id):
    try:
        mydb = mysql.connector.connect(host=host,user=user,password=password,database=database)
        mycursor = mydb.cursor(dictionary=True)
        sql = ("DELETE FROM lots WHERE lots.id = %s;")
        val =(f"{id}",)
        mycursor.execute(sql, val)
        mydb.commit()
        mydb.close()
    except Error as e:
        print(f"Error: {e}")
        return make_response(jsonify({"msg": e}),500)
    return make_response(jsonify({"rowcount": mycursor.rowcount}),200)

######################################################################

######################################################################
# API Login
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    if data:
        usernameu = data['username']
        passwordu = data['password']
        mydb = None
        mycursor = None
        try:
            # เปิดการเชื่อมต่อกับฐานข้อมูล
            mydb = mysql.connector.connect(host=host, user=user, password=password, database=database)
            mycursor = mydb.cursor(dictionary=True)
            #ใช้คำสั่ง SQL พร้อมกับการป้องกัน SQL Injection โดยใช้พารามิเตอร์
            sql = "SELECT * FROM user WHERE name = %s AND password = %s"
            mycursor.execute(sql, (usernameu, passwordu))
            #ตรวจสอบผลลัพธ์ที่ได้จากฐานข้อมูล
            user_record = mycursor.fetchone()
            if user_record:
                return make_response(jsonify({"user": usernameu}),200)
            else:
                return make_response(jsonify({"msg": "not found user or password"}),401)
        except Error as e:
                print(f"Error: {e}")
                return make_response("Internal Server Error", 500)
        finally:
            if mycursor:
                mycursor.close()
            if mydb:
                mydb.close()
######################################################################


######################################################################
#API Status
#get status
@app.route('/api/status/<id>',methods=['GET'])
def status_id(id):
    try:
        mydb = mysql.connector.connect(host=host,user=user,password=password,database=database)
        mycursor = mydb.cursor(dictionary=True)
        sql = "SELECT * FROM status WHERE status.id_lots = %s ORDER BY status.id DESC LIMIT 1;"
        val = (f"{id}",)
        mycursor.execute(sql,val)
        myresult = mycursor.fetchall()
        mydb.close()
    except Error as e:
        print(f"Error: {e}")
        return make_response(jsonify({"msg": e}),500)
    return make_response(jsonify(myresult),200)

#insert status
@app.route('/api/status',methods=['POST'])
def status_insert():
    try:
        mydb = mysql.connector.connect(host=host,user=user,password=password,database=database)
        mycursor = mydb.cursor(dictionary=True)
        data = request.get_json()
        sql = """INSERT INTO `status`(`id_lots`, `id_user`, `status`, `date`) VALUES 
        (%s,%s,%s,%s)"""
        val = (data['id_lots'],data['id_user'],data['status'],data['date'])
        mycursor.execute(sql,val)
        mydb.commit()
        mydb.close()
    except Error as e:
        print(f"Error: {e}")
        return make_response(jsonify({"msg": e}),500)
    return make_response(jsonify({"rowcount": mycursor.rowcount}),200)


######################################################################

######################################################################
# API detection
# ส่งรูปจากกล้องมา
@app.route('/request_pic', methods=['POST'])
def handle_request_video():
    # แปลง base64 กลับมาเป็นภาพ
    data = request.get_json()
    datas = data['imageData']
    header, encoded = datas.split(",", 1)
    img_data = base64.b64decode(encoded)
    image = Image.open(BytesIO(img_data))
    frame = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    if frame is not None:
        frames, num,filename = camera.get_pic(frame)
        print(num)
        sum = num[0]+num[1]+num[2]+num[3]+num[4]+num[5]
        false = num[1]
        if(sum != 0):
            percent = (false/sum) *100
        else:
            percent = 0
        response_data = {
        "num": num,      # ข้อมูลตัวเลข
        "filename": filename,  # ชื่อไฟล์
        "percent": percent
        
        }
        if frames is not None: 
            print(num)
            return jsonify(response_data)
        else:   
            return "Error: Failed to grab frame from camera"
    else :
        print("ssss")

# ลบรูปที่ถ่าย
@app.route('/delete_capture', methods=['POST'])
def delete_capture():
    data = request.get_json()
    filename = data['filename']
    if os.path.exists(filename):
        os.remove(filename)
        return jsonify({'status': 'kuy', 'data_received': data}), 200
    else:
        return jsonify({'error': 'No data provided'}), 400

# ส่งVideoกลับไป
@socketio.on('frame')
def handle_frame(data):
    # แปลง base64 กลับมาเป็นภาพ
    header, encoded = data.split(",", 1)
    img_data = base64.b64decode(encoded)
    image = Image.open(BytesIO(img_data))
    frame = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    # ทำการประมวลผลภาพ เช่น แสดงภาพ
    if frame is not None:
        frames, num = camera.get_test(frame)
        if frames is not None: 
            # ส่งข้อมูลเฟรมและตัวเลข num ผ่าน Socket.IO ไปยังเว็บไซต์
            print(num)
            sum = num[0]+num[1]+num[2]+num[3]+num[4]+num[5]
            false = num[1]
            if(sum != 0):
                percent = (false/sum) *100
            else:
                percent = 0
            socketio.emit('response', {'frame':frames, 'num': num,'percent':percent})
        else:
            return "Error: Failed to grab frame from camera"

# ดึงรูปที่ถ่าย
@app.route('/image', methods=['GET'])
def image():
    filename = request.args.get('filename')
    print("aaaaa=" + filename)
    file_path = os.path.join(app.root_path, filename) 
    if os.path.exists(file_path):  # ตรวจสอบว่าไฟล์มีอยู่จริงหรือไม่
        return send_file(file_path, mimetype='image/jpeg')
    else:
        return "File not found", 404  # ส่งโค้ด 404 หากไม่พบไฟล์
######################################################################



######################################################################
# Main
if __name__ == '__main__':
    app.run()
######################################################################