from flask import Flask, render_template
from utils import yolo, GrabCut
import cv2 as cv
import os

app = Flask(__name__)

@app.route('/')
def sample():
    yolopath = "./yolo-fish"
    confidence = 0.25
    threshold = 0.45

    image = cv.imread("./static/DSC_0061.JPG")
    boxes, idxs = yolo.runYOLOBoundingBoxes_streamlit(image, yolopath, confidence, threshold)
    #result_images = GrabCut.runGrabCut(image, boxes, idxs)

    return render_template('sample.html', 
        boxes = boxes, 
        has_boxes = len(idxs) > 0,
        idxs = idxs.flatten()
    )

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)