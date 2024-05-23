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

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False
CORS(app)  # เปิดใช้งาน CORS
socketio = SocketIO(app, cors_allowed_origins="*")
camera = VideoCamera()

host='192.168.2.130'
user='test'
password='test'
database='cornai'


@app.route('/')
def index():
    return render_template('index.html')



#api sql เส้น product
@app.route('/api/products' ,methods=['GET'])
def products():
    mydb = mysql.connector.connect(host=host,user=user,password=password,database=database)
    mycursor = mydb.cursor(dictionary=True)
    mycursor.execute("SELECT * FROM `products`")
    myresult = mycursor.fetchall()
    mydb.close()
    return make_response(jsonify(myresult),200)

@app.route('/api/products/<id>' ,methods=['GET'])
def products_id_losts(id):
    mydb = mysql.connector.connect(host=host,user=user,password=password,database=database)
    mycursor = mydb.cursor(dictionary=True)
    sql = "SELECT * FROM products  WHERE products.id_lots = %s;"
    val = (f"{id}",)
    mycursor.execute(sql,val)
    result = mycursor.fetchall()
    mydb.close()
    return make_response(jsonify(result),200)

@app.route('/api/products' ,methods=['POST'])
def products_insert():
    mydb = mysql.connector.connect(host=host,user=user,password=password,database=database)
    data = request.get_json()
    mycursor = mydb.cursor(dictionary=True)
    sql = """INSERT INTO `products`(`id_lots`, `id_user`, `BreakClean`, 
            `CompleteSeeds`, `Dust`, `MoldSpores`, `broken`, `fullbrokenseeds`, `path`)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
    val = (
            data['id'],data['user'],data['BreakClean'], data['CompleteSeeds'], data['Dust'],
            data['MoldSpores'], data['broken'], data['fullbrokenseeds'],data['path']
        )
        
    mycursor.execute(sql, val)
    mydb.commit()
    mydb.close()
    return make_response(jsonify({"rowcount": mycursor.rowcount}),200)

@app.route('/api/products', methods=['PUT'])
def products_update():
    mydb = mysql.connector.connect(host=host,user=user,password=password,database=database)
    data = request.get_json()
    mycursor = mydb.cursor(dictionary=True)
    sql = "UPDATE `products` SET `id_lots`=%s WHERE products.id = %s;"
    val = (data['id_lots'],data['id'])
    mycursor.execute(sql, val)
    mydb.commit()
    mydb.close()
    return make_response(jsonify({"rowcount": mycursor.rowcount}),200)

@app.route('/api/products/<id>', methods=['DELETE'])
def products_delete(id):
    mydb = mysql.connector.connect(host=host,user=user,password=password,database=database)
    mycursor = mydb.cursor(dictionary=True)
    sql = "DELETE FROM `products` WHERE products.id = %s;"
    val = (f"{id}",)
    mycursor.execute(sql, val)  
    mydb.commit()
    mydb.close()
    return make_response(jsonify({"rowcount": mycursor.rowcount}),200)



#api sql  lots
@app.route('/api/lots',methods=['GET'])
def lots():
    mydb = mysql.connector.connect(host=host,user=user,password=password,database=database)
    mycursor = mydb.cursor(dictionary=True)
    mycursor.execute("SELECT * FROM `lots`")
    myresult = mycursor.fetchall()
    mydb.close()
    return make_response(jsonify(myresult),200)

@app.route('/api/lots/search/<id>',methods=['GET'])
def lots_like_id(id):
    mydb = mysql.connector.connect(host=host,user=user,password=password,database=database)
    mycursor = mydb.cursor(dictionary=True)
    sql = ("SELECT * FROM lots WHERE lots.name LIKE %s;")
    val = (f"%{id}%",) 
    mycursor.execute(sql, val)
    myresult = mycursor.fetchall()
    mydb.close()
    return make_response(jsonify(myresult),200)

@app.route('/api/lots/<id>', methods=['GET'])
def lots_id(id):
    mydb = mysql.connector.connect(host=host,user=user,password=password,database=database)
    mycursor = mydb.cursor(dictionary=True)
    sql = ("SELECT * FROM lots WHERE lots.id = %s;")
    val = (f"{id}",)
    mycursor.execute(sql, val)
    myresult = mycursor.fetchall()
    mydb.close()
    return make_response(jsonify(myresult),200)

@app.route('/api/lots', methods=['POST'])
def lots_insert():
    mydb = mysql.connector.connect(host=host,user=user,password=password,database=database)
    mycursor = mydb.cursor(dictionary=True)
    data = request.get_json()
    name = "lots_"+data['date']
    sql = ("INSERT INTO `lots`(`name`, `date`) VALUES (%s,%s);")
    val = (name,data['date'])
    mycursor.execute(sql, val)
    mydb.commit()
    mydb.close()
    return make_response(jsonify({"rowcount": mycursor.rowcount}),200)

@app.route('/api/lots/<id>', methods=['DELETE'])
def lots_delete(id):
    mydb = mysql.connector.connect(host=host,user=user,password=password,database=database)
    mycursor = mydb.cursor(dictionary=True)
    sql = ("DELETE FROM lots WHERE lots.id = %s;")
    val =(f"{id}",)
    mycursor.execute(sql, val)
    mydb.commit()
    mydb.close()
    return make_response(jsonify({"rowcount": mycursor.rowcount}),200)

#######################################################
#Login

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usernameu = request.form['username']
        passwordu = request.form['password']
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
                return 'Internal Server Error', 500

        finally:
            if mycursor:
                mycursor.close()
            if mydb:
                mydb.close()

    return render_template('loginpage.html')


#######################################################




# api เส้น detect 
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
        response_data = {
        "num": num,      # ข้อมูลตัวเลข
        "filename": filename  # ชื่อไฟล์
        
        }
        if frames is not None: 
            print(num)
            return jsonify(response_data)
        else:   
            return "Error: Failed to grab frame from camera"
    else :
        print("ssss")

@app.route('/delete_capture', methods=['POST'])
def delete_capture():
    data = request.get_json()
    filename = data['filename']
    if os.path.exists(filename):
        os.remove(filename)
        return jsonify({'status': 'kuy', 'data_received': data}), 200
    else:
        return jsonify({'error': 'No data provided'}), 400


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
            socketio.emit('response', {'frame':frames, 'num': num})
        else:
            return "Error: Failed to grab frame from camera"

@app.route('/image', methods=['GET'])
def image():
    filename = request.args.get('filename')
    print("aaaaa=" + filename)
    file_path = os.path.join(app.root_path, filename) 
    if os.path.exists(file_path):  # ตรวจสอบว่าไฟล์มีอยู่จริงหรือไม่
        return send_file(file_path, mimetype='image/jpeg')
    else:
        return "File not found", 404  # ส่งโค้ด 404 หากไม่พบไฟล์




if __name__ == '__main__':
    app.run()
