from config import params
from flask import (
    abort, Flask, render_template, Response, request, url_for, redirect, session)
from utils import yolo, dropbox, queue
from hashlib import sha256
import cv2 as cv
import os
import rq_dashboard
import redis
import sys
import hmac
import json

app = Flask(__name__)

app.config.from_object(rq_dashboard.default_settings)
app.config["RQ_DASHBOARD_REDIS_URL"] = params.REDIS_URL
app.register_blueprint(rq_dashboard.blueprint, url_prefix="/rq")
app.secret_key = params.FLASK_SECRET_KEY

redis_client = redis.from_url(params.REDIS_URL, decode_responses=True)

@app.route('/')
def index():
    print(session.get('account_id'), file = sys.stderr)
    queue.index_files(session.get('account_id'))

    return render_template('index.html', 
        login_url=url_for('login'),
    )

# dropbox webhook verification
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
    refresh_token = auth_result.refresh_token
    session['account_id'] = account
    redis_client.hset('tokens', account, access_token)
    redis_client.hset('refresh_tokens', account, refresh_token)
    return redirect(url_for('index'))

# dropbox external login
@app.route('/login')
def login():
    return redirect(dropbox.get_flow().start()) 

# actual dropbox webhook
@app.route('/webhook', methods=['POST'])
def webhook():
    signature = request.headers.get('X-Dropbox-Signature')
    key = bytes(params.DROPBOX_APP_SECRET, encoding="ascii")
    computed_signature = hmac.new(key, request.data, sha256).hexdigest()
    print('one', file = sys.stderr)
    if not hmac.compare_digest(signature, computed_signature):
        abort(403)
    print('two', file = sys.stderr)
    for account in json.loads(request.data)['list_folder']['accounts']:
        print(account, file = sys.stderr)
        queue.index_files(session.get('account_id'))
    return ''

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=params.FLASK_PORT)