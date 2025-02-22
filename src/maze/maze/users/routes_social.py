from maze import app, redissession, ADMINS
from flask import Flask, render_template, request, flash, session, redirect, url_for, jsonify
from flask.ext.mail import Message, Mail
from models import db, User, UserAttributes, PasswordToken, first_user
import json
from functools import wraps
from flask import request, redirect, url_for

from flask import Flask, session, redirect, url_for, escape, request

from flask import make_response, request, current_app
from flask import Response
from maze.common import auth, errorhandler
from rauth import OAuth1Service, OAuth2Service

class FacebookSignIn(object):
 
   def __init__(self):
       credentials = app.config['OAUTH_CREDENTIALS']['facebook'] #takes the app credentials obtained in Facebook  
       self.consumer_id = credentials['id']
       self.consumer_secret = credentials['secret']
       self.service = OAuth2Service(
           name='facebook',
           client_id=self.consumer_id,
           client_secret=self.consumer_secret,
           authorize_url='https://www.facebook.com/dialog/oauth',
           access_token_url='https://graph.facebook.com/oauth/access_token',
           base_url='https://graph.facebook.com/'
       ) # initialize the OAuth2 service object with the app credentials and URLs required by the OAuth2 machinery

   def authorize(self, referer):
        return redirect(self.service.get_authorize_url(
            scope='public_profile,email',
            response_type='code',
            redirect_uri=self.get_callback_url(),
            state=referer
    ))

   def get_callback_url(self):
        return 'https://mazebuzz.com/api/users/authorize/callback'

   def callback(self):
        if 'code' not in request.args:
            return None, None, None, None
        oauth_session = self.service.get_auth_session(
            data={'code': request.args['code'],
                  'redirect_uri': self.get_callback_url()
            }
        )
        user_data = oauth_session.get('me?fields=id,email,first_name,last_name,picture.width(800).height(800)').json()
        return (
            user_data.get('id'),
            user_data.get('email'),
            user_data.get('first_name'),
            user_data.get('last_name'),
            user_data.get('picture')['data']['url']
        )

@app.route('/users/authorize', methods=['GET'])
def facebook_authorize():
    referer = 'mazeindex.html'
    req = request.query_string.split('=')
    if len(req) > 1:
        referer = req[1]
        if len(req) > 2:
            referer = req[1] + '=' + req[2]
    oauth = FacebookSignIn() # if user anonymous, begin the authorization phase
    return oauth.authorize(referer)

@app.route('/users/authorize/callback', methods=['GET'])
def oauth_callback():
    oauth = FacebookSignIn()
    referer = request.args.get('state','mazeindex.html')
    facebook_id, email, first_name, last_name, pic = oauth.callback()
    if facebook_id is None:
        return render_template("loader.html", 
                            user_id = 0,
                            isPhoneVerified = 'False',
                            isEmailVerified = 'False',
                            isProfessional = 'False',
                            token = 'ae0',
                            emailstr = 'null',
                            username = 'null',
                            referer = referer,
                            error = 'No+Facebook+account+found')
    
    user = User.query.filter_by(emailId=email).first()
    if user and user.socialId != facebook_id:
        return render_template("loader.html", 
                            user_id = 0,
                            isPhoneVerified = 'False',
                            isEmailVerified = 'False',
                            isProfessional = 'False',
                            token = 'ae0',
                            emailstr = 'null',
                            username = 'null',
                            referer = referer,
                            error = 'Email+id+is+registered+with+another+user')
  
    user = User.query.filter_by(socialId=facebook_id).first()
    if not user:
        first_user()
        user = User (first_name.title(),
                        last_name.title(),
                        email,
                        '111111',
                        0)

        db.session.add(user)
        user.update({'socialId':facebook_id})
        user.update({'profilePicture':pic})
        user.update({'isEmailVerified':True})
        db.session.commit()
        user = User.query.filter_by(socialId=facebook_id).first()
        # Initialize attributes
        newattr = UserAttributes(user.userId)
        db.session.add(newattr)
        db.session.commit()
        user.new_user_req(user, True)
        
    token = user.generate_auth_token()

    return render_template("loader.html", 
                            user_id = user.userId,
                            isPhoneVerified = user.isPhoneVerified,
                            isEmailVerified = user.isEmailVerified,
                            isProfessional = user.isProfessional,
                            token = token,
                            emailstr = user.emailId,
                            username = user.firstName,
                            referer = referer,
                            error = '')
