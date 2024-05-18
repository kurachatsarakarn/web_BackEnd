from flask import Flask, render_template,request,jsonify,send_file
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
CORS(app)  # เปิดใช้งาน CORS
socketio = SocketIO(app, cors_allowed_origins="*")
camera = VideoCamera()

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
    print(datas)
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
    filename = request.args.get('filename')
    if(filename):
        return send_file(filename, mimetype='image/jpeg')


if __name__ == '__main__':
    app.run()
