# yolo 버전
import base64
import json
import numpy as np
from flask import Flask, jsonify, request
from PIL import Image
from io import BytesIO

import yolo



class detector():
    def __init__(self):
        # weight, cfg, names 파일 경로
        self.meta = {'person': ['cfg/yolov4-custom.cfg', 'weights/yolov4-custom_best.weights', 'meta/obj.data'],
                     'car': ['cfg/yolov4.cfg', 'weights/yolov4.weights', 'meta/coco.data']}
        self.models = {}
        self.load_model()

    def load_model(self):
        for key, value in self.meta.items():
            self.models[key] = yolo.Yolo(value[0], value[1], value[2])

    def get_prediction(self, label, img):
        # 해당 레이블이 로드되어있지 않으면
        if label not in self.meta.keys():
            return False
        numpy_img = np.array(img)
        result_detect = self.models[label].detect(label, numpy_img) # 해당 레이블의 박스 검출
        result = [x[2] for x in result_detect] # x,y,w,h 데이터만 반환
        return result

app = Flask(__name__)

# 준비된 클래스 종류 전달
# @app.route('/get_class')
# def get_class():
#     print(list(detector.meta.keys()))
#     response = {'classes': list(detector.meta.keys())}
#     return jsonify(response)

@app.route('/prediction', methods=['POST'])
def prediction():
    json_data = request.get_data()

    if not json_data:
        return 'No Parameter'

    dict_data = json.loads(json_data)
    label, img = dict_data['label'], dict_data['img']

    img_64_decode = base64.b64decode(img)
    image = Image.open(BytesIO(img_64_decode))

    results = detector.get_prediction(label, image)
    response = {'box': results}
    return jsonify(response)


if __name__ == '__main__':
    detector = detector()

    app.run(host='0.0.0.0', port='5050', debug=True)
