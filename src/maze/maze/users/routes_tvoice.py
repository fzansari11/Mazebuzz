from maze import app
from flask import Flask, render_template, request, flash, session, redirect, url_for, jsonify
from flask.ext.mail import Message, Mail
from models import db, User, Inbox, Twiliocalls 

from twilio import twiml
from twilio.rest import TwilioRestClient
from twilio.util import TwilioCapability
from twilio.access_token import AccessToken, ConversationsGrant

from models import db, Appointment, ProfConsulted
from flask import Response
import json
from maze.common import errorhandler
import datetime


# Voice Request URL # This is Phone to Phone
@app.route('/users/call/<int:user_id>', methods=['POST'])
@errorhandler
def call(user_id):
        # Get phone number we need to call
	data = request.get_json(force=True)
	appt_id = data['apptId']
	appt = Appointment.query.filter_by(appointId=appt_id).first()

	if appt.isCancelled:
            return "This appointment has been cancelled already", "", 400
        # Token should be generated only when time is up
        cur_time = datetime.datetime.utcnow()
        appt_time = appt.confirmtime
        # Give 15 minutes buffer
        appt_end_time = appt.confirmtime + datetime.timedelta(minutes=appt.duration + 15)

        if cur_time < appt_time:
            return "Voice Appointment is not yet current. Please wait until the appointment time is due",\
                    "", 400
        
        if cur_time > appt_end_time:
            return "Voice Appointment time has already passed", "", 400 
        
	from_user = user_id
	userfrom = User.query.filter_by(userId=from_user).first()
        from_phone_number = userfrom.phoneNumber

	to_user = appt.toUser if user_id == appt.fromUser else appt.toUser
	userto = User.query.filter_by(userId=to_user).first()
	to_phone_number = userto.phoneNumber

	try:
	        url = "https://c733a264.ngrok.io/api/users/outbound?apptId=" + str(appt_id)
		twilio_client = TwilioRestClient(app.config['TWILIO_ACCOUNT_SID'], app.config['TWILIO_AUTH_TOKEN'])
		call = twilio_client.calls.create(from_=app.config['TWILIO_CALLER_ID'],
			to=from_phone_number,
			method= 'POST',
			url=url,
			fallback_url="https://c733a264.ngrok.io")

		# prof consulted
                cons = ProfConsulted.query.filter_by(userid = appt.fromUser). \
                        filter_by(profid = appt.toUser).first()
                if not cons:
                    consult = ProfConsulted(appt.fromUser, appt.toUser)
                    db.session.add(consult)
                else:
                    # Mark this as reviewed:False since every new appointment should give user an 
                    # option to review
                    cons.reviewed = False

                db.session.commit()

		data = {'message': 'Call incoming soon!'}
	
	        resp = Response(response=json.dumps(data),
                        status=200, \
                        mimetype="application/json")
                return resp, '', 200
		
	except Exception as err:
	    return 'Error calling: %s' % str(err), 'data: %s, request.url: %s' \
                % (str(data), request.url), 500



# Token Request URL # This is Browser to Phone
@app.route('/users/twiliotoken/<int:user_id>', methods=['POST'])
@errorhandler
def twiliotoken(user_id):
	'''Returns a Twilio Client token'''
	data = request.get_json(force=True)
	appt_id = data['apptId']
	appt = Appointment.query.filter_by(appointId=appt_id).first()

        if appt.isCancelled:
            return "This appointment has been cancelled already", "", 400
    
        # Token should be generated only when time is up
        cur_time = datetime.datetime.utcnow()
        appt_time = appt.confirmtime
        # Give 15 minutes buffer
        appt_end_time = appt.confirmtime + datetime.timedelta(minutes=appt.duration + 15)

        if cur_time < appt_time:
            return "Voice Appointment is not yet current. Please wait until the appointment time is due",\
                    "", 400
        
        if cur_time > appt_end_time:
            return "Voice Appointment time has already passed", "", 400 


	to_user = appt.toUser if user_id == appt.fromUser else appt.fromUser
	userto = User.query.filter_by(userId=to_user).first()
	phone_number = userto.phoneNumber

        # Create a TwilioCapability object with our Twilio API credentials
	capability = TwilioCapability(app.config['TWILIO_ACCOUNT_SID'],   app.config['TWILIO_AUTH_TOKEN'])
	# Allow our users to make outgoing calls with Twilio Client
	
	capability.allow_client_outgoing( app.config['TWIML_APPLICATION_SID'])
	# If the user is on the support dashboard page, we allow them to accept
        # incoming calls to "support_agent"
        # (in a real app we would also require the user to be authenticated)
	# Otherwise we give them a name of "customer"

        # Generate the capability token
        if not appt.totoken:
	    token = capability.generate()
            appt.update({'totoken' : token})
            db.session.commit()
        else:
            token = appt.totoken
        data = {'token': token, 'agent' : phone_number}

        # prof consulted
        cons = ProfConsulted.query.filter_by(userid = appt.fromUser). \
                    filter_by(profid = appt.toUser).first()
        if not cons:
            consult = ProfConsulted(appt.fromUser, appt.toUser)
            db.session.add(consult)
        else:
            # Mark this as reviewed:False since every new appointment should give user an 
            # option to review
            cons.reviewed = False

        db.session.commit()
    	
    	resp = Response(response=json.dumps(data),
                        status=200, \
                        mimetype="application/json")
        return resp, '', 200

	
@app.route('/users/outbound', methods=['POST'])
def outbound():
	response = twiml.Response()
	sid = request.values.get('CallSid', None)
	print request.values
	appt_id = request.query_string.split('=')[1]
    	appt_id = int(appt_id)
        appt = Appointment.query.filter_by(appointId=appt_id).first()

        from_user = appt.fromUser
	userfrom = User.query.filter_by(userId=from_user).first()
        from_phone_number = userfrom.phoneNumber

	to_user = appt.toUser 
	userto = User.query.filter_by(userId=to_user).first()
	to_phone_number = userto.phoneNumber

	phoneNumber = to_phone_number if request.values.get('Called',None) == from_phone_number else from_phone_number
	if not sid:
	    return str(response) #this is an error condition, will handle better in future
	
	response.say("Hello Mister Mohammad Juned, Lets connect to your brother Shakil...waitttt please!!!",
                 voice='alice')
	with response.dial() as dial:
	    dial.number(phoneNumber)
    
	return str(response)

@app.route('/users/outboundbrowser', methods=['POST'])
def outboundbrowser():
	response = twiml.Response()
	sid = request.values.get('CallSid', None)
	if sid is None:
		return str(response) #this is an error condition, will handle better in future
	
    # Uncomment this code and replace the number with the number you want 
    # your customers to call.
	with response.dial(callerId='4084786924') as dial:
		if 'PhoneNumber' in request.values:
			dial.number(request.values.get('PhoneNumber'))
    
	return str(response)	


#Helper function to terminate call after alloted time for appointment ends
def terminatecall(): 
	account_sid = app.config['TWILIO_ACCOUNT_SID']
	auth_token = app.config['TWILIO_AUTH_TOKEN']
	client = TwilioRestClient(account_sid, auth_token)
	CallSid = "xxxxx" #Call SId should be retrieved from Redis or MySql and replace here, this api is just for reference of functions
	call = client.calls.update(CallSid, status="completed")
	print 'Call Successfully Completed'


 
#Helper function to get the call status
def getcalltranscript(): 
	account_sid = app.config['TWILIO_ACCOUNT_SID']
	auth_token = app.config['TWILIO_AUTH_TOKEN']
	client = TwilioRestClient(account_sid, auth_token)
	CallSid = "xxxxx" #Call SId should be retrieved from Redis or MySql and replace here, this api is just for reference of functions
	call = client.calls.get(CallSid)
	print 'Received call transcript'

def create_token(endpoint):
    account_sid = app.config['TWILIO_ACCOUNT_SID']
    signingkey_sid = app.config['TWILIO_VIDEO_SIGNING_SIDKEY']
    signingkey_secret = app.config['TWILIO_VIDEO_SIGNING_SECRETKEY']
    token = AccessToken(account_sid,signingkey_sid, signingkey_secret)
    token.identity = endpoint
    grant = ConversationsGrant()
    grant.configuration_profile_sid = app.config['TWILIO_CONFIG_PROFILE_SID']
    token.add_grant(grant)
    my_token = token.to_jwt()

    return my_token

	
@app.route('/users/vidtok/<int:user_id>/<int:appt_id>', methods=['GET'])
@errorhandler
def generateVideoToken(user_id, appt_id):
    try:
	appt = Appointment.query.filter_by(appointId=appt_id).first()

        if appt.isCancelled:
            return "This appointment has been cancelled already", "", 400

	# Token should be generated only when time is up
        cur_time = datetime.datetime.utcnow()
        appt_time = appt.confirmtime
        # Give 15 minutes buffer
        appt_end_time = appt.confirmtime + datetime.timedelta(minutes=appt.duration + 15)
        
        if cur_time < appt_time:
            return "Appointment is not yet current. Please wait until the appointment time is due", \
                    "", 400
        
        if cur_time > appt_end_time:
            return "Appointment time has already passed", "", 400    

	tcall = Twiliocalls.query.filter_by(appointId = appt_id).first()
        if user_id == tcall.fromUser:
	    endpoint = tcall.fromEndpoint
	    remote_endpoint = tcall.toEndpoint
        elif user_id ==tcall.toUser:
	    endpoint = tcall.toEndpoint
	    remote_endpoint = tcall.fromEndpoint
	else:
	    return "wrong User", 'user_id: %s, request.url: %s' \
                    % (user_id, request.url), 400

        if user_id == appt.fromUser:
            if not appt.fromtoken:
                my_token = create_token(endpoint)
                appt.update({'fromtoken': my_token})
            else:
                my_token = appt.fromtoken
        else:
            if not appt.totoken:
                my_token = create_token(endpoint)
                appt.update({'totoken': my_token})
            else:
                my_token = appt.totoken

        # prof consulted
        cons = ProfConsulted.query.filter_by(userid = appt.fromUser). \
                        filter_by(profid = appt.toUser).first()
        if not cons:
            consult = ProfConsulted(appt.fromUser, appt.toUser)
            db.session.add(consult)
        else:
            # Mark this as reviewed:False since every new appointment should give user an 
            # option to review
            cons.reviewed = False
        db.session.commit()

	
	data = {'token': my_token, 'remote_endpoint': remote_endpoint}
        resp = Response(response=json.dumps(data),
                status=200, \
                mimetype="application/json")
        return resp, '', 200
    except Exception as err:
         return 'Error getting video token: %s' % str(err), 'user_id: %s,request.url: %s' \
                % (user_id, request.url), 400


@app.route('/users/videoendpoint/<int:appt_id>', methods=['GET'])
@errorhandler
def getEndpoint(appt_id):
	appt = Appointment.query.filter_by(appointId = appt_id).first()
	endpoint = appt.endpoint
	data = {'endpoint': endpoint}
        resp = Response(response=json.dumps(data),
                status=200, \
                mimetype="application/json")
        return resp, '', 200

@app.route('/users/vidtok/<int:appt_id>', methods=['GET'])
@errorhandler
def checkVideoToken(appt_id):
    try:
        appt = Appointment.query.filter_by(appointId = appt_id).first()
        if appt.totoken and appt.fromtoken:
            data = {'tokenReady': True}
            resp = Response(response=json.dumps(data),
                status=200, \
                mimetype="application/json")
            return resp, '', 200
        else:
            data = {'tokenReady': False}

        resp = Response(response=json.dumps(data),
                status=200, \
                mimetype="application/json")
        return resp, '', 200
    except Exception as err:
         return 'Error getting video token information: %s' % str(err), 'appt_id: %s,request.url: %s' \
                % (appt_id, request.url), 400


