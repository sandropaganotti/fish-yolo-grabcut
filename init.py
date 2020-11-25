from config import params
from flask import Flask, render_template
from rq import Queue
from utils import yolo
from worker import conn
import cv2 as cv
import os
import rq_dashboard

app = Flask(__name__)
app.config.from_object(rq_dashboard.default_settings)
app.config["RQ_DASHBOARD_REDIS_URL"] = params.REDIS_URL
app.register_blueprint(rq_dashboard.blueprint, url_prefix="/rq")

q = Queue(connection=conn)

@app.route('/')
def sample():
    image = cv.imread(params.SAMPLE_IMAGE_PATH)
    boxes, idxs, labels = yolo.runYOLOBoundingBoxes(
        image, 
        params.COCO_NAMES_PATH,
        params.YOLO_WEIGHTS_PATH,
        params.YOLO_NETWORK_PATH,
        params.YOLO_CONFIDENCE,
        params.YOLO_THRESHOLD
    )

    result = q.enqueue(yolo.count_words_at_url, 'http://heroku.com')

    return render_template('sample.html', 
        boxes = boxes, 
        has_boxes = len(idxs) > 0,
        idxs = idxs.flatten() if len(idxs) > 0 else [],
        image_name = params.SAMPLE_IMAGE_NAME,       
        labels = labels,
        result = result
    )

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=params.FLASK_PORT)