from config import params
from flask import (
    Flask, render_template, Response, request, url_for, redirect, session)
from utils import yolo, dropbox, queue
import cv2 as cv
import os
import rq_dashboard
import redis

app = Flask(__name__)

app.config.from_object(rq_dashboard.default_settings)
app.config["RQ_DASHBOARD_REDIS_URL"] = params.REDIS_URL
app.register_blueprint(rq_dashboard.blueprint, url_prefix="/rq")
app.secret_key = params.FLASK_SECRET_KEY

redis_client = redis.from_url(params.REDIS_URL, decode_responses=True)

@app.route('/')
def index():
    queue.index_files(session.get('account_id'))

    return render_template('index.html', 
        login_url=url_for('login'),
    )

# dropbox webhook
@app.route('/webhook', methods=['GET'])
def verify():
    resp = Response(request.args.get('challenge'))
    resp.headers['Content-Type'] = 'text/plain'
    resp.headers['X-Content-Type-Options'] = 'nosniff'
    return resp

# dropbox oauth
@app.route('/oauth_callback')
def oauth_callback():
    auth_result = dropbox.get_flow().finish(request.args)
    account = auth_result.account_id
    access_token = auth_result.access_token
    session['account_id'] = account
    redis_client.hset('tokens', account, access_token)
    return redirect(url_for('index'))

# dropbox external login
@app.route('/login')
def login():
    return redirect(dropbox.get_flow().start()) 

# sample route
@app.route('/sample')
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

    #result = q.enqueue(yolo.count_words_at_url, 'http://heroku.com')

    return render_template('sample.html', 
        boxes = boxes, 
        has_boxes = len(idxs) > 0,
        idxs = idxs.flatten() if len(idxs) > 0 else [],
        image_name = params.SAMPLE_IMAGE_NAME,       
        labels = labels,
        login_url=url_for('login'),
    )


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=params.FLASK_PORT)