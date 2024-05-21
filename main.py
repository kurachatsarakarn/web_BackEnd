from flask import Flask,render_template,request,jsonify,send_file,make_response
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
host = '192.168.2.130'
user = 'test'
password = 'test'
db = 'cornai'

@app.route('/api/cornai' ,methods=['GET'])
def select():
    mydb = mysql.connector.connect(host = host,user= user,password= password ,db=db)
    mycursor = mydb.cursor(dictionary=True)
    mycursor.execute("SELECT * FROM `products`")
    myresult = mycursor.fetchall()
    return make_response(jsonify(myresult),200)

@app.route('/api/cornai' ,methods=['POST'])
def insert():
    data = request.get_json()
    mydb = mysql.connector.connect(host = host,user= user,password= password ,db=db)
    mycursor = mydb.cursor(dictionary=True)
    sql = """
            INSERT INTO `products`(`id`, `BreakClean`, `CompleteSeeds`, `Dust`, `MoldSpores`, `broken`, `fullbrokenseeds`, `results`, `status`, `date`, `picture`)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
    val = (
            data['id'], data['BreakClean'], data['CompleteSeeds'], data['Dust'],
            data['MoldSpores'], data['broken'], data['fullbrokenseeds'], data['results'],
            data['status'], data['date'], data['picture']
        )
        
    mycursor.execute(sql, val)
    mydb.commit()
    return make_response(jsonify({"rowcount": mycursor.rowcount}),200)


@app.route('/')
def index():
    return render_template('index.html')

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
            # socketio.emit('response', {'image': base64.b64encode(frames).decode('utf-8'), 'num': num})
        else:
            return "Error: Failed to grab frame from camera"

@app.route('/image', methods = ['GET'])
def image():
    print("sssssssssssss")
    filename = request.args.get('filename')
    print("aaaaa="+filename)
    if(filename):
        return send_file(filename, mimetype='image/jpeg')


if __name__ == '__main__':
    app.run()
