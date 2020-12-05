#!/usr/bin/python

from flask import request, url_for, session
from config import params
from dropbox import DropboxOAuth2Flow
import urllib.parse

def get_url(route):
    host = urllib.parse.urlparse(request.url).hostname
    url = url_for(
        route,
        _external=True,
        _scheme='http' if host in ('127.0.0.1', 'localhost') else 'https'
    )
    return url

def get_flow():
    return DropboxOAuth2Flow(
        params.DROPBOX_APP_KEY,
        get_url('oauth_callback'),
        session,
        'dropbox-csrf-token',
        consumer_secret = params.DROPBOX_APP_SECRET,
        token_access_type = 'offline')


