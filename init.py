from flask import Flask, render_template
from rq import Queue
from utils import yolo
from worker import conn
import cv2 as cv
import os
import rq_dashboard

app = Flask(__name__)
app.config.from_object(rq_dashboard.default_settings)
app.config["RQ_DASHBOARD_REDIS_URL"] = os.getenv('REDISTOGO_URL', 'redis://redis:6379')
app.register_blueprint(rq_dashboard.blueprint, url_prefix="/rq")

q = Queue(connection=conn)

@app.route('/')
def sample():
    yolopath = "./yolo-fish"
    confidence = 0.25
    threshold = 0.45

    image_name = 'sample.jpg'
    image_path = os.path.sep.join(["./static", image_name])
    image = cv.imread(image_path)
    boxes, idxs, labels = yolo.runYOLOBoundingBoxes(
        image, 
        yolopath, 
        confidence, 
        threshold
    )

    result = q.enqueue(yolo.count_words_at_url, 'http://heroku.com')

    return render_template('sample.html', 
        boxes = boxes, 
        has_boxes = len(idxs) > 0,
        idxs = idxs.flatten() if len(idxs) > 0 else [],
        image_name = image_name,       
        labels = labels,
        result = result
    )

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)