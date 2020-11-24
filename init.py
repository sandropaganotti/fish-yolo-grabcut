from flask import Flask, render_template
from utils import yolo
import cv2 as cv
import os

app = Flask(__name__)

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

    return render_template('sample.html', 
        boxes = boxes, 
        has_boxes = len(idxs) > 0,
        idxs = idxs.flatten() if len(idxs) > 0 else [],
        image_name = image_name,       
        labels = labels
    )

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)