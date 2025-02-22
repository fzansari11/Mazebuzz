from maze import app, redissession, redisnotify
from flask.ext.mail import Message, Mail
from models import db, User, UserAttributes, Inbox, Conversations, \
        ConversationHasMessages, OneMessage, msg_handler,ProfConsulted
import json
from maze.common import errorhandler
from datetime import timedelta
from flask import make_response, request, current_app
from flask import Response
from sqlalchemy import desc
import datetime
from flask import render_template
from maze.common import auth
from maze.handlers import generate_confirmation_token, send_email
from twilio.rest import TwilioRestClient
from flask_classful import FlaskView, route
from models import db, User, Appointment, Twiliocalls
from maze.common import auth, confirm_token, errorhandler
from maze.handlers import send_email

class Messages(FlaskView):
    route_base = '/'
    decorators = [
                  auth.login_required,
                  errorhandler
                  ]
    
    def index(self):
        pass

    ''' Send a message '''
    def post(self, user_id):
        try:
            data = request.get_json(force=True)

            # Make sure sending user is same as user_id.
            fromUser = int(user_id)

            # Make sure sending user is valid.
            my_user = User.query.filter_by(userId = user_id).first()
            if not my_user:
                return "User invalid", "", 400
            
            toUser = data['toUser']
            to_user = User.query.filter_by(userId = toUser).first()
            if not to_user:
                return "Receiving User invalid", 'user_id: %s, data: %s, request.url: %s' \
                    % (user_id, str(data), request.url), 400
            
            if fromUser == toUser:
                return "Cannot send message to self", 'user_id: %s, data: %s, request.url: %s' \
                    % (user_id, str(data), request.url), 400
        
            if not to_user.isEmailVerified:
                return "Other user's email is not verified", 'user_id: %s, data: %s, request.url: %s' \
                    % (user_id, str(data), request.url), 400

            if not my_user.isEmailVerified:
                return "Please verify your email", 'user_id: %s, data: %s, request.url: %s' \
                    % (user_id, str(data), request.url), 400

            resp = send_message(my_user, to_user, data)
            
            msg = "Message sent to User: %s %s " % (to_user.firstName, to_user.lastName)

            # Send email confirmation
            send_email("Maze: %s %s sent you a message" % (my_user.firstName, my_user.lastName), 
                    'mazelogging@gmail.com', [to_user.emailId], msg, render_template("send_message.html",
                    my_user = my_user, subject=data['subject'], text=data['content']))

            return resp, '', 200

        except Exception as err:
            return 'Error sending message: %s' % str(err), 'user_id: %s, data: %s, request.url: %s' \
                    % (user_id, str(data), request.url), 400

    ''' Update a conversation '''
    def put(self, user_id, conv_id):
        try: 
            user_id = int(user_id)
            conv_id = int(conv_id)
            data = request.get_json(force=True)        
            conversation = Conversations.query.filter_by(convId = conv_id).first()
            conv = conversation.to_dict()
            if conv['user2'] != user_id and conv['user1'] != user_id :
                return "Requesting user is not the right one", 'user_id: %s, data: %s, request.url: %s' \
                    % (user_id, str(data), request.url), 400
            
            conversation.isConversationOpen = data['isConversationOpen']
            db.session.commit()

            resp = Response(response=json.dumps({'Conversation updated': 'True'}),
                    status=200, \
                    mimetype="application/json")

            return resp, '' , 200
  
        except Exception as err:
            return 'Error updating conversation: %s' % str(err), 'user_id: %s, data: %s, request.url: %s' \
                    % (user_id, str(data), request.url), 400

    ''' Get a conversation '''
    def conversation(self, user_id, conv_id):
        try:
            user_id = int(user_id)
            conv_id = int(conv_id)
            conversation = Conversations.query.filter_by(convId = conv_id).first()
            conv = conversation.to_dict()
            if conv['user2'] != user_id and conv['user1'] != user_id :
                    return "Requesting user is not the right one", 'user_id: %s, request.url: %s' \
                    % (user_id, request.url), 400
            
            user = User.query.filter_by(userId= user_id).first()
            if not user:
                return "User invalid",'user_id: %s, request.url: %s' % (user_id, request.url), 400

            return get_conversation(user_id, conv_id)
        except Exception as err:
            return 'Error getting conversation: %s' % str(err), 'user_id: %s, request.url: %s' \
                    % (user_id, request.url), 400


    ''' Get all conversations '''
    def conversations(self, user_id):
        try:
            user_id = int(user_id)
            return get_conversations(user_id)
        except Exception as err:
            return 'Error getting all conversations: %s' % str(err), 'user_id: %s, request.url: %s' \
                    % (user_id, request.url) , 400

def send_message(from_user, to_user, data):
        # Create new message
        fromUser = from_user.userId
        toUser = to_user.userId

        msg_handler(fromUser, toUser, data)

        # prof consulted
        if to_user.isProfessional:
            cons = ProfConsulted.query.filter_by(userid = fromUser). \
                    filter_by(profid=toUser).first()
            if not cons:
                consult = ProfConsulted(fromUser, toUser)
                db.session.add(consult)
            else:
                # Mark this as reviewed:False since every new appointment should give user an 
                # option to review
                cons.reviewed = False
 
            db.session.commit()

        response = json.dumps({'Message sent': 'success'})
    
        resp = Response(response,
                mimetype="application/json",
                status=200)
        return resp

def update_conversation(user_id, conv_id):
    try: 
        data = request.get_json(force=True)        
        conv_list = []
        conv_list.append(conv_id)
        conversation = Conversations.query.filter(Conversations.convId.in_(conv_list)).first()
        conv = conversation.to_dict()
        if conv['user2'] != user_id and conv['user1'] != user_id :
                return "Requesting user is not the right one", 'user_id: %s, data: %s, request.url: %s' \
                    % (user_id, str(data), request.url), 400
            
            
        user = User.query.filter_by(userId= user_id).first()
            
        if not user:
            return "User invalid",'user_id: %s, data: %s, request.url: %s' \
                    % (user_id, str(data), request.url), 400
        if not user.isEmailVerified:
            return "Professional's email is not verified",'user_id: %s, data: %s, request.url: %s' \
                    % (user_id, str(data), request.url), 400
          
        conversation.update(data)
        db.session.commit()

        resp = Response(response=json.dumps(data),
                status=200, \
                mimetype="application/json")

        return resp, '' , 200
  
    except Exception as err:
        #log.error('User %s could not be created: %' %(data[userid], err))  
        return 'Error updating conversation: %s' % str(err), 'user_id: %s, data: %s, request.url: %s' \
                    % (user_id, str(data), request.url), 400


def get_conversation(user_id, conv_id):
        inbox = Inbox.query.filter_by(userId = user_id).filter_by(convId = conv_id).first()
        inbox.hasUnread = False
        typedText = inbox.typedText

        msgs = ConversationHasMessages.query.filter_by(convId = conv_id).all()   

        #take all message ids
        message_id_list = []
        for msg in msgs:
            message_id_list.append(msg.messageId)

        #use message id to get all messages
        messages = OneMessage.query.filter(OneMessage.messageId.in_(message_id_list)).all()

        final_list = []
        for message in messages:
            # When reading messages, remove this notification from redis
            if message.toUser == user_id and message.isUnread:
                email_notif = redisnotify.get(user_id)
                if not email_notif or email_notif == '0':
                    email_notif = 1
                redisnotify.set(user_id, int(email_notif) - 1)
                message.update({'isUnread': False})
            new_message = message.to_dict()
            new_message['timeStamp'] = str(new_message['timeStamp'])
            final_list.append(new_message)
        
        db.session.commit()
        data = json.dumps({'Messages': final_list, 'typedText': typedText})
        resp = Response(response=data,
                status=200, \
                mimetype="application/json")

        return resp, '', 200
  
def get_conversations(user_id):
        latest_read_convId = 0
        latest_read_subject = ''
        # Get conversation
        conversations = Inbox.query.filter_by(userId = user_id).all()

        #make list of all conversation ids
        conv_list = []
        conv_unread_list = []
        for conv in conversations:
           conv_list.append(conv.convId)
           if conv.hasUnread:
                conv_unread_list.append(conv.convId)

        conv_details = Conversations.query.filter(Conversations.convId.in_(conv_list)). \
                        order_by(desc(Conversations.timestamp)).all()   
        
        final_conv_list = []
        found = False
        for conv in conv_details:
            new_conv = conv.to_dict()
            
            # For each conversationId check if it is in unread list, if yes, add a flag to let user know
            if conv.convId in conv_unread_list:
                new_conv['hasUnread'] = True
            else:
                new_conv['hasUnread'] = False
                # This will be the latest read conversation
                if not found:
                    latest_read_convId = conv.convId
                    latest_read_subject =  conv.subject
                    found = True
            
            if new_conv['user2'] != user_id and new_conv['user1'] != user_id :
                return "Requesting user is not the right one", 'user_id: %s, request.url: %s' \
                    % (user_id, request.url), 400
            
                  
            new_conv['withUser'] = new_conv['user2'] if user_id != new_conv['user2'] else new_conv['user1']
            new_conv['userIdProfessional'] = 1 if user_id == new_conv['user2'] else 0
            
            user = User.query.filter_by(userId= new_conv['withUser']).first()
            
            if not user:
                return "User invalid",'user_id: %s, request.url: %s' % (user_id, request.url), 400
          
            if user_id == new_conv['user1'] and user.isProfessional:
                if user.subprofession:
                    new_conv['professionName'] = user.subprofession
                else:
                    new_conv['professionName'] = user.profession
            new_conv.pop("user1" , None)
            new_conv.pop("user2" , None)
            new_conv['firstName'] = user.firstName
            new_conv['lastName'] =  user.lastName
            new_conv['profilePicture'] = user.profilePicture
            new_conv['timestamp'] = str(new_conv['timestamp'])
            final_conv_list.append(new_conv)

        final_list = []
        typedText = ''
        if latest_read_convId:
            inbox = Inbox.query.filter_by(userId = user_id).filter_by(convId = latest_read_convId).first()
            typedText = inbox.typedText
            msgs = ConversationHasMessages.query.filter_by(convId = latest_read_convId).all()

            #take all message ids
            message_id_list = []
            for msg in msgs:
                message_id_list.append(msg.messageId)

            #use message id to get all messages
            messages = OneMessage.query.filter(OneMessage.messageId.in_(message_id_list)).all()

            final_list = []
            for message in messages:
                new_message = message.to_dict()
                new_message['timeStamp'] = str(new_message['timeStamp'])
                final_list.append(new_message)
    
        data = json.dumps({'Conversations': final_conv_list ,
                           'Latest Read': {'ConvId': latest_read_convId, 'Messages': final_list, 
                               'typedText': typedText, 'subject' : latest_read_subject}})

        resp = Response(response=data,
                status=200, \
                mimetype="application/json")

        return resp, '', 200

