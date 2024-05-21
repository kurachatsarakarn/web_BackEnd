import random
import cv2
from ultralytics import YOLO
from datetime import datetime

# opening the file in read mode
with open("utils/new.txt", "r") as my_file:
    class_list = my_file.read().split("\n")
    my_file.close()
# Generate random colors for class list
detection_colors = [(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)) for _ in range(len(class_list))]

# load a pretrained YOLOv8n model
model = YOLO("weights/new.pt", "v8")
save_frame = None

class VideoCamera(object):
    def __init__(self):
        self.video = cv2.VideoCapture(0)

    def __del__(self):
        self.video.release()

    def get_test(self,frame):
       # ทำประมวลผลภาพ
        num = [0] * len(class_list)
        detect_params = model.predict(source=[frame], conf=0.45, save=False)
        DP = detect_params[0].cpu().numpy()
        if len(DP) != 0:
            for i in range(len(detect_params[0])):
                boxes = detect_params[0].boxes
                box = boxes[i]  # returns one box
                clsID = box.cls.cpu().numpy()[0]
                conf = box.conf.cpu().numpy()[0]
                bb = box.xyxy.cpu().numpy()[0]

                cv2.rectangle(
                    frame,
                    (int(bb[0]), int(bb[1])),
                    (int(bb[2]), int(bb[3])),
                    detection_colors[int(clsID)],
                    3,
                    )

                # Display class name and confidence
                font = cv2.FONT_HERSHEY_COMPLEX
                cv2.putText(
                    frame,
                    class_list[int(clsID)] + " " + str(round(conf, 3)) + "%",
                    (int(bb[0]), int(bb[1]) - 10),
                    font,
                    1,
                    (255, 255, 255),
                    2,
                    )
                num[int(clsID)] += 1
        # แปลงภาพเป็น JPEG
        ret, jpeg = cv2.imencode('.jpg', frame)
        if ret:  # ตรวจสอบว่าการแปลงภาพเป็น JPEG สำเร็จหรือไม่
            return jpeg.tobytes(), num
        else:
            return None,None
        
    def get_pic(self,frame):
       # ทำประมวลผลภาพ
        num = [0] * len(class_list)
        detect_params = model.predict(source=[frame], conf=0.45, save=False)
        DP = detect_params[0].cpu().numpy()
        if len(DP) != 0:
            for i in range(len(detect_params[0])):
                boxes = detect_params[0].boxes
                box = boxes[i]  # returns one box
                clsID = box.cls.cpu().numpy()[0]
                conf = box.conf.cpu().numpy()[0]
                bb = box.xyxy.cpu().numpy()[0]

                cv2.rectangle(
                    frame,
                    (int(bb[0]), int(bb[1])),
                    (int(bb[2]), int(bb[3])),
                    detection_colors[int(clsID)],
                    3,
                    )

                # Display class name and confidence
                font = cv2.FONT_HERSHEY_COMPLEX
                cv2.putText(
                    frame,
                    class_list[int(clsID)] + " " + str(round(conf, 3)) + "%",
                    (int(bb[0]), int(bb[1]) - 10),
                    font,
                    1,
                    (255, 255, 255),
                    2,
                    )
                num[int(clsID)] += 1
        # แปลงภาพเป็น JPEG
        ret, jpeg = cv2.imencode('.jpg', frame)
        if ret:  # ตรวจสอบว่าการแปลงภาพเป็น JPEG สำเร็จหรือไม่
            time_now = datetime.now()
            filename = f"pic/frame_{time_now.strftime('%Y-%m-%d_%H-%M-%S')}.jpg"
            cv2.imwrite(filename, frame)
            return jpeg.tobytes(),num,filename
        else:
            return None,None