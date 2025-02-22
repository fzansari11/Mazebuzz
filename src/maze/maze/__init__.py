from flask import Flask
from flask_sqlalchemy import SQLAlchemy 

from redis import Redis
#from flask.ext.redis import Redis

import logging
from logging.handlers import RotatingFileHandler

from geopy import geocoders

import os
from flask_classful import FlaskView

app = Flask(__name__)
 
app.secret_key = 'development key'

app.config['SECRET_KEY'] =  'development key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:vagrant@localhost/development'
# This is the path to the upload directory
app.config['UPLOAD_FOLDER'] = '/home/vagrant/uploads/'
app.config['FILE_SERVER'] = 'https://33.33.33.33'
app.config['FILE_URL_PATH'] = '/api/upload/'
app.config['VERIFY_URL_PATH'] = '/api/users/email/'
app.config['RESET_PASS_URL_PATH'] = '/api/users/password/forgot/'
app.config['DEFAULT_IMAGE'] = 'profile_default.png'
# These are the extension that we are accepting to be uploaded
app.config['ALLOWED_EXTENSIONS'] = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'JPG'])
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# Log files
app.config['LOG'] = '/home/vagrant/syslog'

# email server
app.config.update(dict(
MAIL_SERVER = 'smtp.gmail.com',
MAIL_PORT = 587,
MAIL_USE_TLS = True,
MAIL_USE_SSL = False
))

db = SQLAlchemy(app)

# REDIS
redissession = Redis(host='127.0.0.1', port=6379, db = 0)
redissession.permanent = True
redisnotify = Redis(host='127.0.0.1', port=6379, db = 1)
#redisappoint = Redis(host='127.0.0.1', port=6379, db = 2)
#redisapptsched = Redis(host='127.0.0.1', port=6379, db = 3)

from flask.ext.mail import Mail
mail = Mail(app)

g = geocoders.GoogleV3()

# Use this for session handling
#app.config['REDIS_HOST'] = 'localhost'
#app.config['REDIS_PORT'] = 6379
#app.config['REDIS_DB'] = 0
#redissession = Redis(app, '')
# Use this for notifications
#app.config['REDIS2_URL'] = 'redis://localhost:6379/1'
#redisnotif = Redis(app, 'REDIS2')


#logging.basicConfig(filename='/var/log/maze.log', level=logging.DEBUG)
#log = logging.getLogger('maze')

#import maze.users.routes
#import maze.users.routes_session
#import maze.users.routes_appoint
from maze.users.Users import Users, Email, Password
Users.register(app, route_prefix='/users')
Email.register(app, route_prefix='/users')
Password.register(app, route_prefix='/users')

from maze.users.Messages import Messages
from maze.users.Appointments import Appointments, Schedule, Confirm, Cancel, Reject
Appointments.register(app, route_prefix='/users/appoint')
Schedule.register(app, route_prefix='/users/appoint')
Confirm.register(app, route_prefix='/users/appoint')
Cancel.register(app, route_prefix='/users/appoint')
Reject.register(app, route_prefix='/users/appoint')
Messages.register(app, route_prefix='/users/message')

import maze.users.routes_social
import maze.users.routes_reviews
import maze.users.routes_upload
import maze.users.routes_tvoice
import maze.users.routes_payment
import maze.professionals.routes
import maze.professionals.routes_keyword
import maze.professionals.routes_search
import maze.professionals.routes_profession

if app.debug is not True: 
    file_handler = RotatingFileHandler(app.config['LOG'], maxBytes=1024 * 1024 * 100, backupCount=20)
    file_handler.setLevel(logging.ERROR)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(formatter)
    app.logger.addHandler(file_handler)


print app.url_map


    
''' 
    class Config:
    APP_NAME = "Test Google Login"
    SECRET_KEY = os.environ.get("SECRET_KEY") or "somethingsecret"


class DevConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, "test.db")


class ProdConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, "prod.db")


config = {
    "dev": DevConfig,
    "prod": ProdConfig,
    "default": DevConfig
}'''
