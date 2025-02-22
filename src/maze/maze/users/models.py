from werkzeug import generate_password_hash, check_password_hash
from sqlalchemy.dialects.mysql import BIGINT
from maze import db, app, redissession, redisnotify
from flask import render_template
import datetime
import os
from redis import Redis
import base64
import hmac
import hashlib
import string
import time, random, md5
from uuid import uuid4
from sqlalchemy import event
from sqlalchemy import DDL
from maze.handlers import send_email, generate_confirmation_token
#redissession =  app.extensions['redis']['REDIS']

class Helper:
    def to_dict(self, exclude=None):
        ret_attrs = set([c.name for c in self.__table__.columns])
        if exclude:
            ret_attrs = ret_attrs - set(exclude)
        return dict((c, getattr(self, c)) for c in ret_attrs)

    def update(self, values):
        for c in self.__table__.columns:
            if c.name in values:
                setattr(self, c.name, values[c.name])

    def increment(self, attr):
        for c in self.__table__.columns:
            if c.name  == attr:
                a = getattr(self, c.name)
                setattr(self, c.name, a + 1)
 
class User(db.Model, Helper):
  __tablename__ = 'users'
  userId = db.Column(BIGINT(unsigned=True), primary_key = True, autoincrement = True)
  socialId = db.Column(db.String(64), unique=True)
  firstName = db.Column(db.String(100))
  lastName = db.Column(db.String(100))
  phoneNumber = db.Column(db.String(24))
  emailId = db.Column(db.String(120), unique=True)
  pwdhash = db.Column(db.String(1000))
  address1 = db.Column(db.String(1000), default=None)
  address2 = db.Column(db.String(1000), default=None)
  city = db.Column(db.String(54), default=None)
  state = db.Column(db.String(54), default=None)
  country = db.Column(db.String(54), default=None)
  zipcode = db.Column(db.Integer)
  ethnicity =  db.Column(db.String(54), default='') 
  isOnline = db.Column(db.Boolean, default= False) 
  isPhoneVerified = db.Column(db.Boolean, default= False) 
  lastOnline = db.Column(db.DateTime, default=datetime.datetime.utcnow) 
  isProfessional = db.Column(db.Boolean, default = False) 
  profilePicture = db.Column(db.String(256), default = app.config['FILE_SERVER'] + app.config['FILE_URL_PATH']  
         + app.config['DEFAULT_IMAGE'])
  profession = db.Column(db.String(256), default = None)
  subprofession = db.Column(db.String(256), default = None)
  isEmailVerified = db.Column(db.Boolean, default = False)
  isPhoneVerified = db.Column(db.Boolean, default = False)
  phoneCode = db.Column(db.Integer, default=0)
  timestamp = db.Column(db.DateTime)
  timezone = db.Column(db.String(100), default = None)

  def __init__(self, firstName, lastName, emailId, password, zipcode):
    self.firstName = firstName.title()
    self.lastName = lastName.title()
    self.emailId = emailId.lower()
    self.set_password(password)
    self.zipcode = zipcode
    self.timestamp = datetime.datetime.utcnow()

  def generateSessionID(self):
     t1 = time.time()
     print t1
     t2 = t1 + random.random()
     print t2
     base = md5.new(str(t1 +t2))
     sid = base.hexdigest()
     return sid   
     
  def set_password(self, password):
    self.pwdhash = generate_password_hash(password)
   
  def check_password(self, password):
    return check_password_hash(self.pwdhash, password)

  def generate_auth_token(self, expiration = 600):
    sid = self.generateSessionID()
    redissession.set(sid, self.userId)
    #redissession.expire(sid, 6000)
    return sid

  @staticmethod
  def verify_auth_token(token):
    userId = redissession.get(token)
    if userId:
        user = User.query.get(userId)
        return user
    else:    
        return None # valid token, but expired
    
  def data_pop(self, user_info):
    user_info['lastOnline'] = str(user_info['lastOnline']) + ' UTC'
    user_info['timestamp'] = user_info['timestamp'].strftime("%Y-%m-%d UTC")
    user_info.pop('pwdhash')
    user_info.pop('phoneCode', None)
    user_info.pop('profession', None)
    user_info.pop('subprofession', None)
    user_info.pop('ethnicity', None)
    if user_info['socialId']:
        user_info['social'] = True
    user_info.pop('socialId', None)
    return user_info

  def new_user_req(self, user, social=False):
    token = generate_confirmation_token(user. emailId)
    url_path = app.config['VERIFY_URL_PATH'] + str(user.userId) + '/' + token
    hostname = app.config['FILE_SERVER']

    url = hostname + url_path
    if not social:  
        msg = 'Please visit this link to verify your email ' + url
        send_email("Welcome to MazeBuzz", 'mazelogging@gmail.com', [user.emailId], msg , '')

    # Send welcome email
    msg = 'Your journey at Maze begins today'
    send_email("%s: Your journey at MazeBuzz begins today" % \
            (user.firstName), 
            'mazelogging@gmail.com', [user.emailId], 'msg', \
            render_template("send_welcome_email.html", my_user = user))
    # Send welcome message
    content = " Your journey at Maze begins today"
    msg_details = {"subject": "Welcome to Maze", 'content' : content, 'hasAttachment':None }
    msg_handler(1, user.userId, msg_details, True)

def first_user():
        if User.query.filter_by(emailId='mazelogging@gmail.com').first() is None:
            newuser = User ('Maze','Admin','mazelogging@gmail.com','111111',95050)
            db.session.add(newuser)
            attr = UserAttributes(newuser.userId)
            db.session.add(attr)
            db.session.commit()

#event.listen(
#    User.__table__,
#    "after_create",
#    first_user
#)


class UserAttributes(db.Model, Helper):
  __tablename__ = 'userAttributes'
  userId = db.Column(BIGINT(unsigned=True), primary_key = True)
  noOfQuestAsked = db.Column(BIGINT(unsigned=True), default = 0)
  noOfVoiceCalls = db.Column(BIGINT(unsigned=True), default = 0)
  noOfVideoCalls = db.Column(BIGINT(unsigned=True), default = 0)
  noOfTimesPaid = db.Column(BIGINT(unsigned=True), default = 0)
  noOfReviewsReqs = db.Column(BIGINT(unsigned=True), default = 0)
  totalInboxNotifications = db.Column(BIGINT(unsigned=True), default = 0)
  totalApptmentNotifications = db.Column(BIGINT(unsigned=True), default = 0)

  def __init__(self, userId):
    self.userId = userId

class Inbox(db.Model, Helper):
  __tablename__ = 'inbox'
  userId = db.Column(BIGINT(unsigned=True), primary_key = True)
  convId =  db.Column(BIGINT(unsigned=True), primary_key = True)
  hasUnread = db.Column(db.Boolean, default = False)
  typedText = db.Column(db.UnicodeText(), default = u'')

  def __init__(self, userId, convId):
    self.userId = userId
    self.convId = convId

class Conversations(db.Model, Helper):
  __tablename__ = 'conversations'
  convId =  db.Column(BIGINT(unsigned=True), primary_key = True, autoincrement = True)
  totalMessages = db.Column(BIGINT(unsigned=True), default = 0)
  user1 = db.Column(BIGINT(unsigned=True))
  user2 = db.Column(BIGINT(unsigned=True))
  timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)
  isConversationOpen = db.Column(db.Boolean, default = True)
  subject = db.Column(db.String(100), default = '')
  stripeCust = db.Column(db.String(1000), default = '')
  paid = db.Column(db.Boolean, default = False)
  systemMessage = db.Column(db.Boolean, default = False)
  price = db.Column(BIGINT(unsigned=True))

  def __init__(self, user1, user2, subject):
    self.user1 = user1
    self.user2 = user2
    self.subject = subject

class ConversationHasMessages(db.Model, Helper):
  __tablename__ = 'conversationhasmessages'
  convId = db.Column(BIGINT(unsigned=True), primary_key = True)
  messageId = db.Column(BIGINT(unsigned=True), primary_key = True)

  def __init__(self, convId, messageId):
    self.convId = convId
    self.messageId = messageId

class OneMessage(db.Model, Helper):
  __tablename__ = 'messages'
  messageId = db.Column(BIGINT(unsigned=True), primary_key = True)
  timeStamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)
  fromUser = db.Column(BIGINT(unsigned=True), default = 0)
  toUser = db.Column(BIGINT(unsigned=True), default = 0)
  content = db.Column(db.UnicodeText(), default = u'')
  hasAttachment = db.Column(db.Boolean, default = False) 
  attachmentUrl1 = db.Column(db.String(1000), default='')  
  attachmentUrl2 = db.Column(db.String(1000), default='')
  isUnread = db.Column(db.Boolean, default = True)

  def __init__(self, fromUser, toUser):
    self.fromUser = fromUser
    self.toUser = toUser


class Appointment(db.Model, Helper):
  __tablename__ = 'appointments'
  appointId = db.Column(BIGINT(unsigned=True), primary_key = True)
  fromUser = db.Column(BIGINT(unsigned=True), default = 0)
  toUser = db.Column(BIGINT(unsigned=True), default = 0)
  day1 = db.Column(db.DateTime, default=datetime.datetime.utcnow)
  starttime1 = db.Column(db.DateTime, default=datetime.datetime.utcnow)
  endtime1 = db.Column(db.DateTime, default=datetime.datetime.utcnow)
  day2 = db.Column(db.DateTime)
  starttime2 = db.Column(db.DateTime)
  endtime2 = db.Column(db.DateTime)
  day3 = db.Column(db.DateTime)
  starttime3= db.Column(db.DateTime)
  endtime3 = db.Column(db.DateTime)
  duration = db.Column(BIGINT(unsigned=True), default = 0)
  isRejected =  db.Column(db.Boolean, default = False)
  isCancelled =  db.Column(db.Boolean, default = False)
  isRefunded =  db.Column(db.Boolean, default = False)
  isRejectedWithNewProposedTime = db.Column(db.UnicodeText(), default = u'')
  rejectReason = db.Column(db.UnicodeText(), default = u'')
  cancelReason = db.Column(db.UnicodeText(), default = u'')
  refundReason = db.Column(db.UnicodeText(), default = u'')
  isScheduled = db.Column(db.Boolean, default = True)
  isConfirmed =  db.Column(db.Boolean, default = False)
  confirmtime = db.Column(db.DateTime)
  confirmday = db.Column(db.DateTime)
  subject = db.Column(db.String(1000))
  apptType = db.Column(db.String(10))
  totoken = db.Column(db.String(1000))
  fromtoken = db.Column(db.String(1000))
  stripeCust = db.Column(db.String(1000), default = '')
  paid = db.Column(db.Boolean, default = False)
  price = db.Column(BIGINT(unsigned=True))
  convId = db.Column(BIGINT(unsigned=True))

  def __init__(self, fromUser, toUser, day1, starttime1, endtime1, duration, subject, apptType):
    self.fromUser = fromUser
    self.toUser = toUser
    self.day1 = day1
    self.starttime1 = starttime1
    self.endtime1 = endtime1
    self.duration = duration
    self.subject = subject
    self.apptType = apptType

  def data_pop(self, new_appt, user_id):
    new_appt.pop('day1', None)
    new_appt.pop('day2', None)
    new_appt.pop('day3', None)
    new_appt.pop('starttime1', None)
    new_appt.pop('endtime1', None)
    new_appt.pop('starttime2', None)
    new_appt.pop('endtime2', None)
    new_appt.pop('starttime3', None)
    new_appt.pop('endtime3', None)
    if user_id == new_appt['toUser']:
        new_appt['isProf'] = True
    else:
        new_appt['isProf'] = False
    new_appt.pop('toUser', None)
    new_appt.pop('fromUser', None)
    #new_appt.pop('confirmtime', None)
    #new_appt.pop('confirmday', None)
    new_appt.pop('isScheduled', None)
    new_appt.pop('isConfirmed', None)
    new_appt.pop('isRejected', None)
    new_appt.pop('rejectReason', None)
    new_appt.pop('totoken', None)
    new_appt.pop('fromtoken', None)
    new_appt.pop('stripeCust', None)
    new_appt.pop('isRejectedWithNewProposedTime', None)

    return new_appt

class Twiliocalls(db.Model, Helper):
    __tablename__ = 'twiliocalls'
    appointId = db.Column(BIGINT(unsigned=True), primary_key = True)
    fromEndpoint = db.Column(db.String(100))
    toEndpoint = db.Column(db.String(100))
    fromUser = db.Column(BIGINT(unsigned=True), default = 0)
    toUser = db.Column(BIGINT(unsigned=True), default = 0)

    def __init__(self, appointId, fromEndpoint, toEndpoint, fromUser, toUser):
      self.appointId = appointId
      self.fromEndpoint = fromEndpoint
      self.toEndpoint = toEndpoint
      self.fromUser = fromUser
      self.toUser = toUser

class Reviews(db.Model, Helper):
  __tablename__ = 'reviews'
  reviewId = db.Column(BIGINT(unsigned=True), primary_key = True)
  fromUser = db.Column(BIGINT(unsigned=True), default = 0)
  toUser = db.Column(BIGINT(unsigned=True), default = 0)
  timeOfReview = db.Column(db.DateTime, default=datetime.datetime.utcnow)
  reviewTitle = db.Column(db.String(50), default = u'')
  stars = db.Column(BIGINT(unsigned=True), default = 0)
  isRejected =  db.Column(db.Boolean, default = False)
  rejectReason = db.Column(db.UnicodeText(), default = u'')
  reviewText = db.Column(db.UnicodeText(), default = u'')

  def __init__(self, fromUser, toUser, reviewTitle, stars, reviewText):
    self.fromUser = fromUser
    self.toUser = toUser
    self.reviewTitle = reviewTitle
    self.stars = stars
    self.reviewText = reviewText


class ProfConsulted(db.Model, Helper):
  __tablename__ = 'profconsulted'
  userid = db.Column(BIGINT(unsigned=True), default = 0, primary_key = True)
  profid = db.Column(BIGINT(unsigned=True), default = 0, primary_key = True)
  reviewed = db.Column(db.Boolean, default = False)

  def __init__(self, userid, profid):
    self.userid = userid
    self.profid = profid

class PasswordToken(db.Model, Helper):
    __tablename = 'passwordtoken'
    userId = db.Column(BIGINT(unsigned=True), default = 0, primary_key = True)
    token = db.Column(db.String(256))

    def __init__(self, userId, token):
        self.userId = userId
        self.token = token

def msg_handler(user1, user2, data = None, systemMessage=False):
    # Create new message
    msg = OneMessage (user1, user2)
    db.session.add(msg)

    msg.update({'content': data['content']})

    if data['hasAttachment']:
        msg.update({'hasAttachment':data['hasAttachment']})
        msg.update({'attachmentUrl1':data['attachmentUrl1']})
        if data.get('attachmentUrl2'):
            msg.update({'attachmentUrl2':data['attachmentUrl2']})

    # Create new conversation for both users
    if not data.get('convId'):
        # Increment number of messages asked for the sending user
        attr = UserAttributes.query.filter_by(userId = user1).first()
        attr.noOfQuestAsked = attr.noOfQuestAsked + 1

        conv = Conversations (user1, user2, data['subject'].capitalize())
        db.session.add(conv)
        db.session.commit()    

        inbox = Inbox(user1, conv.convId)
        db.session.add(inbox)
            
        inbox = Inbox(user2, conv.convId)
        db.session.add(inbox)
    else:
        inbox = Inbox.query.filter_by(userId = user2).filter_by(convId = data.get('convId')).first()

    # Update only for the user this message is being sent to. 
    inbox.hasUnread = True
        
    conv_id  = data.get('convId') if data.get('convId') else conv.convId

    # Conversation exists/ created. Add totalMessages. Update timestamp
    conv = Conversations.query.filter_by(convId = conv_id).first()
    conv.increment('totalMessages')   
    if systemMessage:
        conv.update({'systemMessage':systemMessage})
        # In this case send notification to both
        email_notif = redisnotify.get(user1)
        if not email_notif: 
            email_notif = 0
        redisnotify.set(user1, int(email_notif) + 1)
    else:
        if data.get('price'):
            conv.update({'price' : data['price']})
        if data.get('stripeCust'):
            conv.update({'stripeCust':data['customer']})
    conv.timestamp = datetime.datetime.utcnow()
    #conv.hasUnread = True

    hasmsg = ConversationHasMessages(conv.convId, msg.messageId)   
    db.session.add(hasmsg)
    db.session.commit()
    
    # Add this notification to Redis
    email_notif = redisnotify.get(user2)
    if not email_notif: 
        email_notif = 0
    redisnotify.set(user2, int(email_notif) + 1)
    
    return conv.convId
