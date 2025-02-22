from datetime import timedelta
import json
import re
from random import randint
import uuid

from maze import app,redissession, ADMINS, g
from flask import Flask, render_template, request, flash, session, redirect, url_for, jsonify, \
      make_response, Response
from flask.ext.mail import Message, Mail
from models import db, User, UserAttributes, PasswordToken, msg_handler, first_user
from maze.common import auth, confirm_token, errorhandler
from maze.handlers import generate_confirmation_token, send_email
from twilio.rest import TwilioRestClient
from flask_classful import FlaskView, route


class Users(FlaskView):
    route_base = "/"
    #decorators = [errorhandler]

    def index(self):
        pass

    ''' Show user '''
    @auth.login_required  
    @errorhandler
    def get(self, user_id):
        try:
            user = User.query.filter_by(userId=user_id).first()
            if not user:
                return 'User not found', 'user_id: %s, request.url: %s' \
                    % (user_id, request.url), 400
                        
            attr = UserAttributes.query.filter_by(userId=user_id).first()
            if not attr:
                return 'User data not found', 'user_id: %s, request.url: %s' \
                    % (user_id, request.url), 400
            return show_user(user, attr)
                
        except Exception as err:
                return  'Error while retreiving user :%s' % str(err), 'user_id: %s, request.url: %s' \
                    % (user_id, request.url), 400

    ''' Update user '''
    @auth.login_required
    @errorhandler
    def put(self, user_id):
        try:
            data = request.get_json(force=True)
            user = User.query.filter_by(userId=user_id).first()
            if not user:
                return 'User not found', 'user_id: %s, request.url: %s' \
                    % (user_id, request.url), 400

            attr = UserAttributes.query.filter_by(userId=user_id).first()
            if not attr:
                return 'User data not found', 'user_id: %s, request.url: %s' \
                    % (user_id, request.url), 400
            
            return update_user(data, user, attr)

        except Exception as err:
            return 'Error while updating user data :%s' % str(err), 'user_id: %s, data: %s, request.url: %s' \
                    % (user_id, str(data), request.url), 500

    ''' Create user '''
    @errorhandler
    def post(self):
        try:
            data = request.get_json(force=True)
    
            if User.query.filter_by(emailId=data['emailId']).first() is not None:
                return 'Email id is registered with another user', 'data: %s, request.url: %s' \
                    % (str(data), request.url), 400 # existing user

            return create_user(data)
        
        except Exception as err:
            return 'An error occured while creating user: %s' % str(err), 'data: %s, request.url: %s' \
                    % (str(data), request.url), 400

    #@auth.login_required 
    def delete(self, id):
        pass


    ''' Logout user '''
    @auth.login_required 
    @errorhandler
    @route('logout', methods=['GET']) 
    def logout(self):
        try: 
            token = request.authorization.get('username', '')
            redissession.get(token)
            redissession.delete(token)
            resp = Response("User logged out",
                   status=200, mimetype="application/json")
            return resp, '' , 200
        except Exception as err:
            return 'Error logging out :%s' % str(err), 'request.url: %s' \
                    % (request.url), 400

       
    ''' Login user '''
    @errorhandler
    @route('login', methods=['POST'])   
    def user_login(self):
        data = request.get_json(force=True)
        try:
            user = User.query.filter_by(emailId=data['emailId']).first()
            if not user:
                return 'User not found', 'data: %s, request.url: %s' \
                    % (str(data), request.url), 400

            return login(user)
    
        except Exception as err:
            return 'Error logging in :%s' % str(err),  'data: %s, request.url: %s' \
                    % (str(data), request.url), 400



class Email(Users):
    route_base = "email"

    ''' Update email '''
    @auth.login_required
    @errorhandler
    def put(self, user_id):
        try: 
            data = request.get_json(force=True)
            user = User.query.filter_by(userId=user_id).first()
            if not user:
                return 'User not found', 'user_id: %s, data: %s, request.url: %s' \
                    % (user_id, str(data), request.url), 400

            if not user.check_password(data['password']):
                return 'Incorrect password', 'user_id: %s, data: %s, request.url: %s' \
                    % (user_id, str(data), request.url), 400
            
            return update_email(data, user)
        
        except Exception as err:
            return  'Error updating email :%s' %str(err), 'user_id: %s, data: %s, request.url: %s' \
                    % (user_id, str(data), request.url), 400

    ''' Request email verification '''
    @auth.login_required
    @errorhandler
    def post(self, user_id):
        try: 
            # Create first user if does not exist
            first_user()
            
            user = User.query.filter_by(userId=user_id).first()
            if not user:
                return 'User not found', 'user_id: %s, data: %s, request.url: %s' \
                    % (user_id, str(data), request.url), 400

            if user.isEmailVerified:
                return 'Account already verified', 'user_id: %s, request.url: %s' \
                    % (user_id, request.url), 400
            return verify_email(user)
        
        except Exception as err:
            return  'Error updating email :%s' %str(err), 'user_id: %s, request.url: %s' \
                    % (user_id, request.url), 400

    ''' Confirm email verification '''
    @errorhandler
    def get(self, user_id, token):
        user = User.query.filter_by(userId=user_id).first()
        if not user:
             return 'User not found', 'user_id: %s, request.url: %s' \
                    % (user_id, request.url), 400
                    
        try:
            emailId = confirm_token(token)
            if not emailId:
                return 'Confirmation link is invalid or has expired', 'user_id: %s, request.url: %s' \
                    % (user_id, request.url), 400
        except:
            return ('The confirmation link is invalid or has expired', 'user_id: %s request.url: %s' \
                    % (user_id,request.url), 500)

        try:
            if user.emailId != emailId:
                return "The confirmation link is invalid", 'user_id: %s, request.url: %s' \
                    % (user_id, request.url), 400
    
            if user.isEmailVerified:
                return('Account already confirmed. Please login', 'user_id: %s, request.url: %s' \
                    % (user_id, request.url),  400)
            else:
                user.isEmailVerified = True
                db.session.add(user)
                db.session.commit()
                return "Account Verified Successfully", "", 200
        
        except Exception as err:
            return  'Error updating email :%s' %str(err), 'user_id: %s, request.url: %s' \
                    % (user_id, request.url), 400




class Password(Users):
    route_base = "password"

    ''' Forgot Password '''
    @errorhandler
    def post(self, user_id):
        data = request.get_json(force=True)
        try: 
            user = User.query.filter_by(userId=user_id).first()
            if not user:
                return 'User not found', 'user_id: %s, data: %s, request.url: %s' \
                    % (user_id, str(data), request.url), 400

            return forgot_password(data, user)
        
        except Exception as err:
            return  'Error updating password :%s' %str(err), 'user_id: %s, data: %s, request.url: %s' \
                    % (user_id, str(data), request.url), 400
  

    ''' Change password '''
    @auth.login_required
    @errorhandler
    def put(self, user_id):
        data = request.get_json(force=True)
        try: 
            user = User.query.filter_by(userId=user_id).first()
            if not user:
                return 'User not found', 'user_id: %s, data: %s, request.url: %s' \
                    % (user_id, str(data), request.url), 400

            if not user.check_password(data['oldPassword']):
                return 'Incorrect password', 'user_id: %s, data: %s, request.url: %s' \
                    % (user_id, str(data), request.url), 400
            
            return update_password(data, user)
        
        except Exception as err:
            return  'Error updating password :%s' %str(err), 'user_id: %s, data: %s, request.url: %s' \
                    % (user_id, str(data), request.url), 400

    ''' Change social login password '''
    @auth.login_required
    @errorhandler
    @route('/social/<int:user_id>', methods=['PUT'])
    def social(self, user_id):
        data = request.get_json(force=True)
        try: 
            user = User.query.filter_by(userId=user_id).first()
            if not user:
                return 'User not found', 'user_id: %s, data: %s, request.url: %s' \
                    % (user_id, str(data), request.url), 400
            return update_social_password(data, user)
        
        except Exception as err:
            return  'Error updating password :%s' %str(err), 'user_id: %s, data: %s, request.url: %s' \
                    % (user_id, str(data), request.url), 400

    ''' Reset password '''
    @errorhandler
    @route('/reset/', methods=['POST'])
    def reset(self):
        data = request.get_json(force=True)
        try: 
            user = User.query.filter_by(emailId=data['emailId']).first()
            if not user:
                return 'User not found', 'data: %s, request.url: %s' \
                    % (str(data), request.url), 400
            return reset_password(user)
        
        except Exception as err:
            return  'An error occured while resetting password : %s' %str(err), \
                    'user_id: %s, data: %s, request.url: %s' \
                    % (user_id, str(data), request.url), 400


def create_user(data):
        newuser = User (data['firstName'].title(),
                    data['lastName'].title(),
                    data['emailId'],
                    data['password'],
                    data['zipcode'])
    
        db.session.add(newuser)
        user = User.query.filter_by(emailId=data['emailId']).first()

        # Initialize attributes
        newattr = UserAttributes(user.userId)
        db.session.add(newattr)

        db.session.commit()

        token = user.generate_auth_token()
        data_response = json.dumps({ 'token': token, 'userId': user.userId, 'firstName': user.firstName, 
                                     'lastName': user.lastName, 'isEmailVerified': user.isEmailVerified, 
                                     'isPhoneVerified': user.isPhoneVerified})

        user.new_user_req(user)
        resp = Response(response=data_response,
                status=200, \
                mimetype="application/json")



        return resp, '' , 200
 

def show_user(user, attr):
    user_info = dict(user.to_dict().items() + attr.to_dict().items())
    user_info = user.data_pop(user_info)

    data = json.dumps(user_info)
    resp = Response(response=data,
                status=200, \
                mimetype="application/json")

    return resp, '', 200


attr_table = {'Attributes':UserAttributes}

def increment_attributes(table, attrs, user_id):
    user = table.query.filter_by(userId=user_id).first()
    for attr in attrs:
        user.increment(attr)

def convert_to_us(country):
    new_country = country.lower().strip(' ')
    if new_country == 'usa' or new_country == 'u.s.a' or new_country == 'us' or \
            new_country == 'unitedstates' or new_country == 'unitedstates ofamerica':
       country = 'USA'
    return country


def update_user(data, user, attr):
    for key in data.keys():
        if key in attr_table.keys():
            increment_attributes(attr_table[key], data[key], user_id)
        else:
            # if phone updated make it unverified again
            if key == 'phoneNumber':
                if user.phoneNumber != data['phoneNumber']:
                    user.update({'isPhoneVerified': False})
            if key == 'country':
                data[key] = convert_to_us(data[key])
            if key == 'city' or key == 'state':
                data[key] = data[key].title()
            user.update({key:data[key]})
    # Update timezone for Professional if city and state filled
    if user.isProfessional:
        if 'city' in data.keys() or 'state' in data.keys():
            city_str = user.city + user.state
            user.timezone = g.timezone(g.geocode(city_str).point).zone
    db.session.commit()
    user_info = user.to_dict()
    user_info = user.data_pop(user_info)
    resp = Response(response=json.dumps(user_info),
                status=200, \
                mimetype="application/json")
    return resp, '', 200


def update_email(data, user):
    user.update({'emailId':data['emailId']})
    user.update({'isEmailVerified':False})
    db.session.commit()
    resp_data = json.dumps({'Email update':'success'})
    resp = Response(response=resp_data,
                    status=200, \
                    mimetype="application/json")

    token = generate_confirmation_token(data['emailId'])
    url_path = app.config['VERIFY_URL_PATH'] + str(user.userId) + '/' + token
    hostname = app.config['FILE_SERVER']

    url = hostname + url_path
    msg = 'Please visit this link to verify your email ' + url
    send_email("Welcome to Maze", 'mazelogging@gmail.com', [data['emailId']], msg , '')

    return resp, '' , 200


def verify_email(user):
    token = generate_confirmation_token(user.emailId)
    url_path = app.config['VERIFY_URL_PATH'] + str(user.userId) + '/' + token
    hostname = app.config['FILE_SERVER']

    url = hostname + url_path
    msg = 'Please visit this link to verify your email ' + url
    send_email("Welcome to Maze", 'mazelogging@gmail.com', [user.emailId], msg , '')

    resp = Response(response=json.dumps({'Email verify': 'Success'}),
                status=200, \
                mimetype="application/json")
    return resp, "", 200
  

def update_social_password(data, user):
    user.set_password(data['newPassword'])
    user.update({'socialId':None})
    db.session.commit()
    data = json.dumps({'Password Update': 'Success'})
    resp = Response(response=data,
                    status=200, \
                    mimetype="application/json")

    return resp, '', 200


def update_password(data, user):
    user.set_password(data['newPassword'])
    db.session.commit()
    resp = Response(response=json.dumps({'Password Update': 'Success'}),
                    status=200, \
                    mimetype="application/json")

    return resp, '', 200


def forgot_password(data, user):
    user.set_password(data['password'])
    db_token = PasswordToken.query.filter_by(userId = user.userId).first()
    if db_token:
        db.session.delete(db_token)
    db.session.commit()
    resp = Response(response=json.dumps({'Password update':'success'}),
                    status=200, \
                    mimetype="application/json")
    return resp, '', 200


def reset_password(user):
        token = generate_confirmation_token(user.emailId)
        url_path = app.config['RESET_PASS_URL_PATH'] + str(user.userId) + '/' + token
        hostname = app.config['FILE_SERVER']

        url = hostname + url_path
        msg = 'Please visit this link to reset your password ' + url
        send_email("Reset your Maze password", 'mazelogging@gmail.com', [user.emailId], msg , '')

        db_token = PasswordToken.query.filter_by(userId = user.userId).first()
        if db_token:
            db.session.delete(db_token)
            db.session.commit()

        # add this token to DB
        new_token = PasswordToken(user.userId, token)
        db.session.add(new_token)
        db.session.commit()

        data = json.dumps({'password':'reset'})
        resp = Response(response=data,
                status=200, \
                mimetype="application/json")
        return resp, "", 200
  

''' open url to reset password '''
@app.route('/users/password/forgot/<user_id>/<token>', methods=['GET'])
def reset_password_url(user_id, token):
        db_token = PasswordToken.query.filter_by(userId = user_id).first()
        if not db_token or db_token.token != token:
            return 'Invalid Password reset request', 400
        
        return render_template('reset_password.html', user_id=user_id)

def login(user):
        token = user.generate_auth_token()
        data = json.dumps({ 'token': token, 'userId': user.userId, 
                            'firstName': user.firstName, 'lastName': user.lastName,
                            'isEmailVerified': user.isEmailVerified, 
                            'isPhoneVerified': user.isPhoneVerified,
                            'isProfessional' : user.isProfessional})
        resp = Response(response=data,
                    status=200, \
                    mimetype="application/json")
        return resp, '', 200


################    PHONE  ######
@app.route('/users/sendsms/<user_id>', methods=['POST'])
@errorhandler
def verify_phone(user_id):
    data = request.get_json(force=True)
    try:
        user = User.query.filter_by(userId=user_id).first()
        if not user:
            return "User not found", 'user_id: %s, data: %s, request.url: %s' \
                    % (user_id, str(data), request.url), 400
        if user.phoneNumber == data['phoneNumber'] and user.isPhoneVerified:
            return "Phone already verified", 'user_id: %s, data: %s, request.url: %s' \
                    % (user_id, str(data), request.url), 400
	twilio_client = TwilioRestClient(app.config['TWILIO_ACCOUNT_SID'], app.config['TWILIO_AUTH_TOKEN'])
	code = randint(10000,99999)
        body = "Maze code: %s" % code
        message = twilio_client.messages.create(to=data['phoneNumber'], from_=app.config['TWILIO_CALLER_ID'],body=body)
        user.phoneCode = code
        user.phoneNumber = data['phoneNumber']
        db.session.commit()
        resp = Response(response=json.dumps({"Phone verification": "true"}),
                status=200, \
                mimetype="application/json")
        return resp, '', 200
    except Exception as err:
        return 'An error occured while verifying phone of user: %s' % str(err), 'user_id: %s, data: %s, request.url: %s' \
                    % (user_id, str(data), request.url), 400


@app.route('/users/verifyphone/<user_id>', methods=['POST'])
@errorhandler
def confirm_phone(user_id):
    data = request.get_json(force=True)
    try:
        user = User.query.filter_by(userId=user_id).first()
        if not user:
            return "User not found", 'user_id: %s, data: %s, request.url: %s' \
                    % (user_id, str(data), request.url), 400
        if user.phoneCode ==  data['phoneCode']:
            user.isPhoneVerified = True
            db.session.add(user)
            db.session.commit()
            resp = Response(response=json.dumps({"Phone verification": "true"}),
                status=200, \
                mimetype="application/json")
            return resp, '', 200
        else:
            return "Incorrect phone code entered", 'user_id: %s, data: %s, request.url: %s' \
                    % (user_id, str(data), request.url), 400
    except Exception as err:
        return 'An error occured while verifying phone code of user: %s' % str(err), 'user_id: %s, data: %s, request.url: %s' \
                    % (user_id, str(data), request.url) ,  400
