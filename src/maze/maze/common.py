from maze import app, redissession, mail, ADMINS
#, MAZE_ADMINS
from flask import Flask, render_template, request, flash, session, redirect, url_for, jsonify
from flask.ext.mail import Message, Mail
from threading import Thread
import json

from users.models import db, User
from datetime import timedelta
from flask import make_response, request, current_app
from functools import update_wrapper
from flask import Response
from functools import wraps

from flask.ext.httpauth import HTTPBasicAuth
from handlers import send_email, URLSafeTimedSerializer

def crossdomain(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if request.method == 'OPTIONS':
            resp = Response("Foo bar baz")
            resp.headers['Access-Control-Allow-Origin'] = '*'
            resp.headers['Access-Control-Allow-Methods'] = 'POST, GET, OPTIONS'
            resp.headers['Access-Control-Max-Age'] = 1000
            resp.headers['Access-Control-Allow-Headers'] = 'origin, x-csrftoken, content-type, accept, authorization'
            return resp
        else:

            return func(*args, **kwargs)
    return wrapper

# Global Error handler

def errorhandler(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            data = ''
            msg, data, ret = f(*args, **kwargs)
            # Will be a response object for 200
            if ret == 200:
                return msg
            elif ret == 500:
                send_email("Maze Error", 'mazelogging@gmail.com', ADMINS, msg + data, '')
                return msg, 400
            elif ret == 400:
                #app.logger.error(msg + data)
                return msg, 400
            else:
                send_email("Maze Error", 'mazelogging@gmail.com', ADMINS, msg + data, '')
                return msg, 400
        except Exception as err:
            send_email("Unknown exception occurred", 'mazelogging@gmail.com', ADMINS, str(err) , '')
    return wrapper

# Authentication
auth = HTTPBasicAuth()

@auth.verify_password
def verify_password(username_or_token, password):
    user = User.verify_auth_token(username_or_token)
    if not user:
        # try to authenticate with username/password
        user = User.query.filter_by(emailId = username_or_token).first()
        if not user or not user.check_password(password):
            return False
    return True
    
    response.status_code = 400
    return response



# project/token.py

def confirm_token(token, expiration=3600):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    try:
        email = serializer.loads(
            token,
            salt=app.config['SECURITY_PASSWORD_SALT'],
            max_age=expiration
        )
    except:
        return None
    return email

'''''''''ERROR HANDLERS'''''''''''''''

@auth.error_handler
def auth_error():
    resp = Response(response=json.dumps({
        'responseText': 'User session expired. Please try logging in again',
        'type': 'Login Failed'}),
                    status=402, \
                    mimetype="application/json")

    return resp
