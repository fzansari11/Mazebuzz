from datetime import timedelta
import json
import pytz
import re
from random import randint
import uuid
from sqlalchemy import desc
import datetime as dt
import datetime 
from sqlalchemy import *
import random
from flask import render_template
import re
from random import randint
import uuid
from twilio.rest import TwilioRestClient
from maze.professionals.models import Profession, SubProfession, Professionals, ProfessionalRatings, Credentials, ProfHasKeywords, ExactKeywordsProf, ApproxKeywordsProf, ProfTimeSlots



from maze import app, redissession, redisnotify, ADMINS, g
from flask import Flask, render_template, request, session, redirect, url_for, jsonify, \
      make_response, Response
from flask.ext.mail import Message, Mail
from models import db, User, UserAttributes, PasswordToken, msg_handler

from twilio.rest import TwilioRestClient
from flask_classful import FlaskView, route
from flask.ext.mail import Message, Mail
from models import db, User, Appointment, Twiliocalls
from maze.common import auth, confirm_token, errorhandler
from maze.handlers import send_email


def timezone_helper(request):
    my_tz = None
    req = request.query_string.split('=')
    if len(req) > 1:
        my_tz = req[1]
    if not my_tz:
        my_tz = 'America/Los_Angeles'
    return pytz.timezone(my_tz)

class Appointments(FlaskView):
    route_base = "/"
    decorators = [errorhandler,
                  #auth.login_required
                  ]

    def index(self):
        pass

class Schedule(Appointments):
    route_base = 'schedule'
    decorators = [errorhandler,
                  #auth.login_required
                  ]

    ''' Schedule an appointment '''
    def post(self, user_id):
        data = request.get_json(force=True)
        try:
            user_tz = timezone_helper(request)
            user_id = int(user_id)
            my_user_id = int(data['fromUser'])

            if my_user_id != user_id:
                return "Requesting user is not the right one", 'user_id: %s, data: %s, request.url: %s' \
                    % (user_id, str(data), request.url), 400

            my_user = User.query.filter_by(userId = my_user_id).first()
            if not my_user:
                return "User is not registered",'', 400

            if not my_user.isEmailVerified:
                return "Please verify your email", 'user_id: %s, data: %s, request.url: %s' \
                        % (user_id, str(data), request.url), 400

            prof_id = int(data['toUser'])
            if my_user_id == prof_id:
                return "Cannot book appointment with self", 'user_id: %s, data: %s, request.url: %s' \
                        % (user_id, str(data), request.url), 400

            prof = User.query.filter_by(userId = prof_id).first()
            if not prof:
                return "Professional is not registered",'user_id: %s, data: %s, request.url: %s' \
                        % (user_id, str(data), request.url), 400

            if not prof.isEmailVerified:
                return "Professional's email is not verified",'user_id: %s, data: %s, request.url: %s' \
                        % (user_id, str(data), request.url), 400

            if not prof.isPhoneVerified:
                return "Professional's phone is not verified",'user_id: %s, data: %s, request.url: %s' \
                        % (user_id, str(data), request.url), 400

            return sched_appoint(data, my_user, prof, user_tz)

        except Exception as err:
            return 'Error creating appt: %s' % str(err), 'user_id: %s, data: %s, request.url: %s' \
                % (user_id, str(data), request.url), 400

    ''' Get all scheduled appointments '''
    def get(self, user_id):
        try:
            user_id = int(user_id)
            user_tz = timezone_helper(request)
            return get_schedappt(user_id, user_tz)
        except Exception as err:
            return 'Error getting appt details: %s' % str(err), 'user_id: %s, request.url: %s' \
                    % (user_id, request.url), 400

    ''' Get single scheduled appointment '''
    def one(self, user_id, appt_id):    
        try:
            user_id = int(user_id)
            user_tz = timezone_helper(request)
            return get_one_sched_appt(user_id, int(appt_id), user_tz)
        except Exception as err:
            return 'Error reading appt details: %s' % str(err), 'user_id: %s, request.url: %s' \
                % (user_id, request.url), 500

def appt_status(appt):
    if appt.isCancelled:
        return 'Cancelled'
    elif appt.isRejected:
        return 'Rejected'
    elif appt.isRefunded:
        return 'Refunded'

class Confirm(Appointments):
    route_base = 'confirm'
    decorators = [errorhandler,
                  #auth.login_required
                  ]
    
    ''' Confirm Appointment'''
    def post(self, user_id):
        user_tz = timezone_helper(request)
        data = request.get_json(force=True)
        user_id = int(user_id)
        try: 
            # Get appointment
            appt = Appointment.query.filter_by(appointId = data['appointId']).first()
            if not appt:
                return "Appointment not found",'user_id: %s, data: %s, request.url: %s' \
                        % (user_id, str(data), request.url), 400

            if user_id != appt.toUser and user_id != appt.fromUser:
                return "User not same as the one with whom appointment was requested", \
                        'user_id: %s, data: %s, request.url: %s' \
                        % (user_id, str(data), request.url), 400

            prof = User.query.filter_by(userId = appt.toUser).first()
            user = User.query.filter_by(userId = appt.fromUser).first()

            if appt.isRejected or appt.isCancelled or appt.isRefunded:
                return "Appointment is not available for any further action. Status: %s" % \
                        appt_status(appt), 'user_id: %s, data: %s, request.url: %s' \
                        % (user_id, str(data), request.url), 400

            return confirm_appoint(data, appt, user, prof, user_tz)

        except Exception as err:
            return 'Error confirming appt: %s' % str(err), 'user_id: %s, data: %s, request.url: %s' \
                % (user_id, str(data), request.url), 400

    ''' Get confirmed appointments '''
    def get(self, user_id):
        user_tz = timezone_helper(request)
        user_id = int(user_id)
        try:
            return get_confirmedappt(user_id, user_tz)
        except Exception as err:
            return 'Error getting confirmed appts: %s' % str(err), 'user_id: %s, request.url: %s' \
                % (user_id, request.url), 500


class Cancel(Appointments):
    route_base = 'cancel'
    decorators = [errorhandler,
                  #auth.login_required
                  ]
    
    ''' Cancel Appointment'''
    def post(self, user_id):
        user_tz = timezone_helper(request)
        data = request.get_json(force=True)
        user_id = int(user_id)
        try: 
            user_tz = timezone_helper(request)
            # Get appointment
            appt = Appointment.query.filter_by(appointId = data['appointId']).first()
            if not appt:
                return "Appointment not found",'user_id: %s, data: %s, request.url: %s' \
                        % (user_id, str(data), request.url), 400

            if user_id != appt.toUser and user_id != appt.fromUser:
                return "User not same as the one with whom appointment was requested", \
                        'user_id: %s, data: %s, request.url: %s' \
                        % (user_id, str(data), request.url), 400

            prof = User.query.filter_by(userId = appt.toUser).first()
            user = User.query.filter_by(userId = appt.fromUser).first()

            if appt.isRejected or appt.isCancelled or appt.isRefunded:
                return "Appointment is not available for any further action: Status: %s" % \
                        appt_status(appt), 'user_id: %s, data: %s, request.url: %s' \
                        % (user_id, str(data), request.url), 400

            return cancel_appoint(data, appt, user, prof, user_tz)

        except Exception as err:
            return 'Error confirming appt: %s' % str(err), 'user_id: %s, data: %s, request.url: %s' \
                % (user_id, str(data), request.url), 400


class Reject(Appointments):
    route_base = 'reject'
    decorators = [errorhandler,
                  #auth.login_required
                  ]
    
    ''' Reject Appointment'''
    def post(self, user_id):
        user_tz = timezone_helper(request)
        data = request.get_json(force=True)
        user_id = int(user_id)
        try: 
            user_tz = timezone_helper(request)
            # Get appointment
            appt = Appointment.query.filter_by(appointId = data['appointId']).first()
            if not appt:
                return "Appointment not found",'user_id: %s, data: %s, request.url: %s' \
                        % (user_id, str(data), request.url), 400

            if user_id != appt.toUser and user_id != appt.fromUser:
                return "User not same as the one with whom appointment was requested", \
                        'user_id: %s, data: %s, request.url: %s' \
                        % (user_id, str(data), request.url), 400

            prof = User.query.filter_by(userId = appt.toUser).first()
            user = User.query.filter_by(userId = appt.fromUser).first()

            if appt.isRejected or appt.isCancelled or appt.isRefunded:
                return "Appointment is not available for any further action. Status %s " % \
                        appt_status(appt), 'user_id: %s, data: %s, request.url: %s' \
                        % (user_id, str(data), request.url), 400

            return reject_appoint(data, appt, user, prof, user_tz)

        except Exception as err:
            return 'Error confirming appt: %s' % str(err), 'user_id: %s, data: %s, request.url: %s' \
                % (user_id, str(data), request.url), 400



def sched_appoint(data, user, prof, user_tz):
        # Convert time to UTC
        duration = str(data['duration']) + ' minutes'
        
        day1 = datetime.datetime.strptime(data['day1'], "%Y-%m-%d")
        day1_content = 'Day1 :' + data['day1'] + ' ' +  data['starttime1'] + ' . '
        day2_content = ''
        day3_content = ''
        starttime1 = datetime.datetime.strptime(data['starttime1'], "%I:%M %p")
        starttime1  = datetime.datetime.combine( day1.date(), starttime1.time())

        localdt = user_tz.localize(starttime1)
        starttime1 = localdt.astimezone(pytz.UTC)
        endtime1 = starttime1 + datetime.timedelta(minutes=data['duration'])

        ''' Store starttime1 instead of day1 because it contains time and gives appropriate
            representation in UTC. So while converting back to user'z TZ we have the correct 
            timestamp '''
        #day1 = starttime1.date()
        day1 = starttime1

        # Create new appointment
        appoint = Appointment (user.userId, prof.userId, day1, starttime1,
                            endtime1, data['duration'], data['subject'].capitalize(), data['apptType'])
        db.session.add(appoint)
        appoint.update({'stripeCust': data['customer']})
        appoint.update({'price' : data['price']})

        if data.get('day2'):
            day2 = datetime.datetime.strptime(data['day2'], "%Y-%m-%d")
            day2_content= 'Day2 :' + data['day2'] + ' ' + data['starttime2'] + ' . '
            starttime2 = datetime.datetime.strptime(data['starttime2'], "%I:%M %p")
            starttime2  = datetime.datetime.combine( day2.date(), starttime2.time())
        
            localdt = user_tz.localize(starttime2)
            starttime2 = localdt.astimezone(pytz.UTC)
            endtime2 = starttime2 + datetime.timedelta(minutes=data['duration'])
            #day2 = starttime2.date()
            day2 = starttime2
            
            appoint.update({'day2': day2})
            appoint.update({'starttime2': starttime2})
            appoint.update({'endtime2':  endtime2})

        if data.get('day3'): 
            day3 = datetime.datetime.strptime(data['day3'], "%Y-%m-%d")
            day3_content= 'Day3 :' + data['day3'] + ' ' + data['starttime3'] + ' . '
            starttime3 = datetime.datetime.strptime(data['starttime3'], "%I:%M %p")
            starttime3  = datetime.datetime.combine( day3.date(), starttime3.time())

            localdt = user_tz.localize(starttime3)
            starttime3 = localdt.astimezone(pytz.UTC)
            endtime3 = starttime3 + datetime.timedelta(minutes=data['duration'])
            #day3 = starttime3.date()
            day3 = starttime3

            appoint.update({'day3': day3})
            appoint.update({'starttime3': starttime3})
            appoint.update({'endtime3': endtime3})

        # Increment number of appointment count
        attr = UserAttributes.query.filter_by(userId = user.userId).first()
        if data['apptType'] == 'voice':
            attr.noOfVoiceCalls = attr.noOfVoiceCalls + 1
        else:
            attr.noOfVideoCalls = attr.noOfVideoCalls + 1

        db.session.commit()

        send_email("Maze: Appointment schedule request from %s %s " % (user.firstName, user.lastName), 
                    'mazelogging@gmail.com', [prof.emailId], 'msg', render_template("send_sched_appt.html",
                    my_user = user,
                    subject=data['subject'],duration=duration, appttype = data['apptType'], day1=day1_content, 
                    day2=day2_content, day3=day3_content))

        # Send sms to pro when appoint is scheduled
        prof1 = Professionals.query.filter_by(userId=prof.userId).first()
        if prof1.receiveSms and prof.isPhoneVerified:
            twilio_client = TwilioRestClient(app.config['TWILIO_ACCOUNT_SID'], app.config['TWILIO_AUTH_TOKEN'])
	    code = randint(10000,99999)
            body = "Maze appointment request from %s %s . Subject = %s, Duration %s, Type %s . " % \
                    (user.firstName, user.lastName, data['subject'], duration, data['apptType']) 
            body += day1_content
            body = body + day2_content if day2_content else body
            body = body + day3_content if day3_content else body
            message = twilio_client.messages.create(to=user.phoneNumber, from_=app.config['TWILIO_CALLER_ID'],body=body)
        
        resp = Response(response=json.dumps({"Appointment": "Success"}),
                mimetype="application/json",
                status=200 )

        return resp, '' , 200


def get_schedappt(user_id, user_tz):
    date=datetime.datetime.utcnow()

    appt_to_details = Appointment.query.filter(Appointment.toUser == user_id). \
                        filter(Appointment.isScheduled == True). \
                        filter(or_(date <= Appointment.starttime1, date <= Appointment.starttime2, \
                        date <= Appointment.starttime3)).order_by(desc(Appointment.starttime1)).all()

    appt_from_details = Appointment.query.filter(Appointment.fromUser == user_id). \
                        filter(Appointment.isScheduled == True). \
                        filter(or_(date <= Appointment.starttime1, date <= Appointment.starttime2, \
                        date <= Appointment.starttime3)).order_by(desc(Appointment.starttime1)).all()

    appt_details = appt_to_details + appt_from_details
    final_list = []
    for appt in appt_details:
        new_appt = appt.to_dict()
        new_appt['withUser'] = new_appt['toUser'] if user_id != new_appt['toUser'] else new_appt['fromUser']

        new_appt = appt.data_pop(new_appt, user_id)
        new_appt.pop('confirmtime', None)
        new_appt.pop('confirmday', None)
        user = User.query.filter_by(userId= new_appt['withUser']).first()
        if user.isProfessional:
            if user.subprofession:
                new_appt['professionName'] = user.subprofession
            else:
                new_appt['professionName'] = user.profession
        new_appt['firstName'] = user.firstName
        new_appt['lastName'] =  user.lastName
        new_appt['profilePicture'] = user.profilePicture
        final_list.append(new_appt)

    resp = Response(response=json.dumps({'Appointments': final_list}),
                status=200, \
                mimetype="application/json")

    return resp, '', 200
  

def get_one_sched_appt(user_id, appt_id, user_tz):
        appt = Appointment.query.filter_by(appointId = appt_id).first()

        if user_id != appt.toUser and user_id != appt.fromUser:
            return 'Appointment details requested by incorrect user', \
                    'user_id: %s, request.url: %s' \
                    % (user_id, request.url), 400

        new_appt = appt.to_dict()
        day1 = new_appt['day1']
        day2 = new_appt['day2']
        day3 = new_appt['day3']
        starttime1 = new_appt['starttime1']
        endtime1 = new_appt['endtime1']

        starttime1 = pytz.utc.localize(starttime1, is_dst=None).astimezone(user_tz)
        endtime1 = pytz.utc.localize(endtime1, is_dst=None).astimezone(user_tz)
        
        new_appt['day1'] = starttime1.strftime("%Y-%m-%d %Z")
        start = starttime1.strftime("%I:%M %p")
        end = endtime1.strftime("%I:%M %p")
        new_appt['time1'] = {'starttime1' : start, 'endtime1': end}

        if new_appt['day2']:
           new_appt['day2'] = new_appt['day2'].strftime("%Y-%m-%d")
           starttime2 = new_appt['starttime2']
           endtime2 = new_appt['endtime2']

           starttime2 = pytz.utc.localize(starttime2, is_dst=None).astimezone(user_tz)
           endtime2 = pytz.utc.localize(endtime2, is_dst=None).astimezone(user_tz)

           new_appt['day2'] = starttime2.strftime("%Y-%m-%d %Z")
           start = starttime2.strftime("%I:%M %p")
           end = endtime2.strftime("%I:%M %p")
           if new_appt['day2'] == new_appt['day1']:
              new_appt['time1']['starttime2'] = start
              new_appt['time1']['endtime2'] = end
              new_appt.pop('day2', None)
           else:
              new_appt['time2'] = {'starttime1' : start, 'endtime1': end}


        if new_appt['day3']:
           new_appt['day3'] = new_appt['day3'].strftime("%Y-%m-%d")
           starttime3 = new_appt['starttime3']
           endtime3 = new_appt['endtime3']

           starttime3 = pytz.utc.localize(starttime3, is_dst=None).astimezone(user_tz)
           endtime3 = pytz.utc.localize(endtime3, is_dst=None).astimezone(user_tz)

           new_appt['day3'] = starttime3.strftime("%Y-%m-%d %Z")
           start = starttime3.strftime("%I:%M %p")
           end = endtime3.strftime("%I:%M %p")
           if new_appt['day3'] == new_appt['day1']:
              # this means we popped out day2
              if not new_appt.get('day2',''):
                 new_appt['time1']['starttime3'] = start
                 new_appt['time1']['endtime3'] = end
                 new_appt.pop('day3', None)
              else:
                 new_appt['time1']['starttime2'] = start
                 new_appt['time1']['endtime2'] = end
                 new_appt.pop('day3', None)
           elif new_appt['day3'] == new_appt.get('day2',''):
                 new_appt['time2']['starttime2'] = start
                 new_appt['time2']['endtime2'] = end
                 new_appt.pop('day3', None)
           else:
                 new_appt['time3'] = {'starttime1' : start, 'endtime1': end}

        # Add all confirmed appointments for all the days day1, day2, day3
        for day in ['day1', 'day2', 'day3']:
            if new_appt.get(day,''):
                appt_from_details = Appointment.query.filter(Appointment.fromUser == user_id). \
                        filter(Appointment.isConfirmed == True ).\
                        filter(Appointment.confirmday == new_appt[day]). \
                        order_by(desc(Appointment.confirmtime)).all()

                appt_to_details = Appointment.query.filter(Appointment.toUser == user_id). \
                        filter(Appointment.isConfirmed == True ). \
                        filter(Appointment.confirmday == new_appt[day]). \
                        order_by(desc(Appointment.confirmtime)).all()

                #TODO FAHIM: Add check if confirmtime is in future
                appt_details = appt_from_details + appt_to_details
                if appt_details:
                    total_times = []
                    for appt in appt_details:
                        start = appt.confirmtime
                        start = pytz.utc.localize(start, is_dst=None).astimezone(user_tz)
                        end = appt.confirmtime + dt.timedelta(minutes=appt.duration)
                        total_times.append({'start':start.strftime("%I:%M %p"), \
                                'end':end.strftime("%I:%M %p")})
                    new_appt['schedule'+ day] =  \
                            { 'total_appt':len(appt_details), \
                            'times':total_times}

        new_appt['withUser'] = new_appt['toUser'] \
                if user_id != new_appt['toUser'] else new_appt['fromUser']

        user = User.query.filter_by(userId= new_appt['withUser']).first()
        if user.isProfessional:
            if user.subprofession:
                new_appt['professionName'] = user.subprofession
            else:
                new_appt['professionName'] = user.profession
        new_appt['firstName'] = user.firstName
        new_appt['lastName'] =  user.lastName
        new_appt['profilePicture'] = user.profilePicture

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
        new_appt.pop('confirmtime', None)
        new_appt.pop('confirmday', None)
        new_appt.pop('isConfirmed', None)
        new_appt.pop('isRejected', None)
        new_appt.pop('rejectReason', None)
        new_appt.pop('isRejectedWithNewProposedTime', None)

        data = json.dumps(new_appt)

        resp = Response(response=data,
                status=200, \
                mimetype="application/json")

        return resp, '', 200
  


def confirm_appoint(data, appt, user, prof, user_tz):
    conf = data['confirmday'].split(' ')
    confirmday = datetime.datetime.strptime(conf[0], "%Y-%m-%d")
    confirmtime = datetime.datetime.strptime(data['confirmtime'], "%I:%M %p")
    confirmtime = datetime.datetime.combine( confirmday, confirmtime.time())

    localdt = user_tz.localize(confirmtime)
    confirmtime = localdt.astimezone(pytz.UTC)

    confirmtime1 = confirmtime.replace(tzinfo=None)
    confirmday1 = confirmtime.date()

    # Check if appointment already exists for above time
    appt_details = Appointment.query.filter(Appointment.toUser == prof.userId). \
                  filter(Appointment.isConfirmed == True). \
                  filter(Appointment.isRejected == False). \
                  filter(Appointment.isCancelled == False). \
                  filter(Appointment.confirmtime == confirmtime1).all()
    
    if appt_details:
        return 'An appointment exists for this time already ', '', 400

    if appt.apptType == 'video':
	fromendpoint = str(appt.appointId) + 'maze' + str(appt.fromUser) + str(random.random())
	toendpoint = str(appt.appointId) + 'maze' + str(appt.toUser) + str(random.random())
	tcall = Twiliocalls(appt.appointId, fromendpoint, toendpoint, appt.fromUser, appt.toUser)
	db.session.add(tcall)

    content = "Duration : %s Type: %s Day : %s Time : %s" % \
            (appt.duration, appt.apptType,  data['confirmday'], data['confirmtime'])
    extra = "Please use this message for any follow-ups to the appointment "  
    msg_details = {"subject": appt.subject, 'content' : content + extra, 'hasAttachment':None }
    # Send message once appointment is confirmed
    conv_id = msg_handler(appt.fromUser, appt.toUser, msg_details, True)
    # Send email
    send_email("Maze: Appointment Id: %s confirmed with %s %s" % (str(appt.appointId), 
                     prof.firstName,  prof.lastName), 
                    'mazelogging@gmail.com', [user.emailId], 'msg', 
                    render_template("send_confirm_appt.html", my_user = prof,
                    subject=appt.subject,text=content))
    
    appt.convId = conv_id
    appt.isConfirmed = data['isConfirmed']
    appt.confirmtime = confirmtime1
    appt.confirmday = confirmday1
    appt.isScheduled = False
    db.session.commit()

    resp = Response(response=json.dumps({"Appointment": "Confirm Success"}),
                mimetype="application/json",
                status=200)

    return resp, '', 200


def reject_appoint(data, appt, user, prof, user_tz):
    appt.isRejected = data['isRejected']
    if data.get('rejectReason'):
        appt.rejectReason = data['rejectReason']
        appt.confirmtime = datetime.datetime.now()

    subject = "Appointment Id: %s rejected " % (appt.appointId)
    content = "Appointment has been rejected with following reason: %s " % (appt.rejectReason)
    msg_details = {"subject": subject, 'content' : content, 'hasAttachment':None }
    # Send message once appointment is rejected
    conv_id = msg_handler(appt.fromUser, appt.toUser, msg_details, True)
    # Send email
    send_email("Maze: Appointment Id: %s rejected with %s %s" % \
            (str(appt.appointId), prof.firstName,  prof.lastName), 
            'mazelogging@gmail.com', [user.emailId], 'msg', \
            render_template("send_confirm_appt.html", my_user = prof,
            subject=appt.subject,text=content))

    appt.convId = conv_id
    appt.isScheduled = False
    db.session.commit()

    resp = Response(response=json.dumps({"Appointment": "Confirm Success"}),
                mimetype="application/json",
                status=200)

    return resp, '', 200


def cancel_appoint(data, appt, user, prof, user_tz):
    appt.isCancelled = data['isCancelled']
    if data.get('cancelReason'):
        appt.cancelReason = data['cancelReason']
        appt.confirmtime = datetime.datetime.now()
            
    subject = "Appointment Id: %s cancelled " % (appt.appointId)
    content = "Appointment has been cancelled with following reason: %s " % (appt.cancelReason)
    msg_details = {"subject": subject, 'content' : content, 'hasAttachment':None }
    if appt.convId:
        msg_details['convId'] = appt.convId
    # Send message once appointment is cancelled
    conv_id = msg_handler(appt.fromUser, appt.toUser, msg_details, True)
    # Send email
    send_email("Maze: Appointment Id: %s cancelled with %s %s" % \
            (str(appt.appointId), user.firstName, user.lastName), 
            'mazelogging@gmail.com', [prof.emailId], 'msg', \
            render_template("send_confirm_appt.html", my_user = user, 
            subject=appt.subject,text=content))

    appt.convId = conv_id
    appt.isScheduled = False
    db.session.commit()

    resp = Response(response=json.dumps({"Appointment": "Cancel Success"}),
                mimetype="application/json",
                status=200)

    return resp, '', 200
  

def get_confirmedappt(user_id, user_tz):
    cur_date = datetime.datetime.utcnow()
    # subtract 60 min from current time. 
    #Show appointments which should have been started an hour back
    date = cur_date - datetime.timedelta(minutes=60)
    appt_to_details = Appointment.query.filter(Appointment.toUser == user_id).\
            filter(Appointment.isConfirmed == True).\
            filter(Appointment.isRejected == False). \
            filter(Appointment.isCancelled == False). \
            filter(Appointment.confirmtime >= date). \
            order_by(Appointment.confirmtime).all()

    appt_from_details = Appointment.query.filter(Appointment.fromUser == user_id). \
            filter(Appointment.isConfirmed == True). \
            filter(Appointment.isRejected == False). \
            filter(Appointment.isCancelled == False). \
            filter(Appointment.confirmtime >= date). \
            order_by(Appointment.confirmtime).all()
        
    appt_details = appt_to_details + appt_from_details
    final_list = []
    for appoint in appt_details:
        # if appoint is not scheduled skip this iteration and move onto next one
        new_appt = appoint.to_dict()
        confirmtime = pytz.utc.localize(new_appt['confirmtime'], is_dst=None). \
                astimezone(user_tz)
        new_appt['confirmtime24hour'] = confirmtime.strftime("%H:%M")
        new_appt['confirmtime'] = confirmtime.strftime("%I:%M %p")
        new_appt['confirmday'] = confirmtime.strftime("%Y-%m-%d %Z")
        new_appt['withUser'] = new_appt['toUser']  \
                if user_id != new_appt['toUser'] else new_appt['fromUser']

        new_appt = appoint.data_pop(new_appt, user_id)

        user = User.query.filter_by(userId= new_appt['withUser']).first()
        if user.isProfessional:
            if user.subprofession:
                new_appt['professionName'] = user.subprofession
            else:
                new_appt['professionName'] = user.profession
        new_appt['firstName'] = user.firstName
        new_appt['lastName'] =  user.lastName
        new_appt['profilePicture'] = user.profilePicture
        final_list.append(new_appt)

    data = json.dumps({'Appointments': final_list})

    resp = Response(response=data,
                status=200, \
                mimetype="application/json")

    return resp, '', 200


day_tuples = [('monstart', 'monend'), ('tuesstart', 'tuesend'), 
                  ('wedstart', 'wedend'),  ('thursstart', 'thursend'),
                  ('fristart', 'friend'),  ('satstart', 'satend'), 
                  ('sunstart', 'sunend')]

# get all timeslots for user
@app.route('/users/timeslots/<int:user_id>', methods=['POST'])
@errorhandler
#@auth.login_required
def get_timeslots(user_id):
  try:
    data = request.get_json(force=True)
    user_tz = timezone_helper(request)
    profId = int(data['profId'])
    duration = int(data['duration'])
    date = datetime.datetime.strptime(data['day1'], "%Y-%m-%d")

    # Convert current datetime to User's timezone. First localize to UTC and then convert
    cur_date = pytz.utc.localize(datetime.datetime.utcnow(), is_dst=None).astimezone(user_tz)
    cur_date_without_tz = cur_date.replace(tzinfo=None)
    cur_date_no_time = cur_date_without_tz.replace(hour=0, minute=0, second=0, microsecond=0)
    
    if date == cur_date_no_time:
        start = cur_date_without_tz
    else:
        start = datetime.datetime.strptime("12:00 AM", "%I:%M %p")
    end = datetime.datetime.strptime("11:59 PM", "%I:%M %p")

    prof = User.query.filter_by(userId=profId).first()
    prof_tz = pytz.timezone(prof.timezone)

    # convert date to prof time
    date1 = datetime.datetime.combine(date, start.time())
    date1 = user_tz.localize(date1)
    date1 = date1.astimezone(pytz.UTC) # convert to UTC
    date1 = date1.astimezone(prof_tz) # convert to prof_tz

    date2 = datetime.datetime.combine(date, end.time())
    date2 = user_tz.localize(date2)
    date2 = date2.astimezone(pytz.UTC) # convert to UTC
    date2 = date2.astimezone(prof_tz) # convert to prof_tz

    proftime = ProfTimeSlots.query.filter_by(userId=profId).first()
    proftime_dict = proftime.to_dict()

    # Find days from day tuples
    avail_slots = []
    for date in [date1, date2]:
        list_day = []

        # If date2 is same as date1 dont do this block, jump to apptments
        if not (date == date2 and date1.date() == date2.date()):
            day = date.weekday()
            day_tup = day_tuples[day]
            start_times = proftime_dict[day_tup[0]].split(',') # All start times for day
            end_times = proftime_dict[day_tup[1]].split(',') # All end times for day

            if len(start_times) and start_times[0] == '':
                break 

            #list_day = [1:00, 1:15, 2:00, 2:15, 2:30, 2:45, 3:00, 3:15]
            for start,end in zip(start_times,end_times):
                starttime = datetime.datetime.strptime(start, "%I:%M %p")
                starttime = datetime.datetime.combine(date, starttime.time())
                starttime = prof_tz.localize(starttime)

                endtime = datetime.datetime.strptime(end, "%I:%M %p")
                endtime = datetime.datetime.combine(date, endtime.time())  
                endtime = prof_tz.localize(endtime)

                #list_day = [1:00, 1:15, 2:00, 2:15, 2:30, 2:45]
                while starttime < endtime:
                    # if duration exceeds endtime chuck this time
                    if ((starttime + datetime.timedelta(minutes=duration)) > endtime):
                        break
                    if date==date1 and starttime >= date:
                        list_day.append(starttime)
                    elif date==date2 and starttime <= date:
                        list_day.append(starttime)
                    starttime = starttime + datetime.timedelta(minutes=15)

        # remove all slots for appointments
        try:
            date_utc = date.astimezone(pytz.UTC) # convert to UTC
            query = (Appointment.confirmtime >= date_utc.replace(tzinfo=None)) if date==date1 \
                    else (Appointment.confirmtime <= date_utc.replace(tzinfo=None))
            appt_details = Appointment.query.filter(Appointment.toUser == profId).filter(Appointment.isConfirmed == True).filter(Appointment.isRejected == False).filter(Appointment.confirmday == date_utc.date()).filter(query).order_by(desc(Appointment.confirmtime)).all()
        except Exception as err:
            print err

        booked_slots = []
        for appt in appt_details:
            confirmtime = appt.confirmtime
            confirmtime = pytz.utc.localize(confirmtime, is_dst=None).astimezone(prof_tz)
            endtime = confirmtime + datetime.timedelta(minutes=appt.duration)
            while confirmtime < endtime:
                booked_slots.append(confirmtime)
                confirmtime = confirmtime + datetime.timedelta(minutes=15)
        my_list = []
        for x in list_day:
            if x not in booked_slots:
                my_list.append(x)
        if not (date == date2 and date1.date() == date2.date()):
            avail_slots = my_list
        else:
            avail_slots = avail_slots + my_list

    
    user_slots = []
    for slot in avail_slots:
        start_utc = slot.astimezone(pytz.UTC) # convert to UTC
        start_user = start_utc.astimezone(user_tz) # convert to user_tz
        time = start_user.strftime("%I:%M %p")
        user_slots.append(time)

    resp = Response(response=json.dumps({'timeslots':user_slots}),
                status=200, \
                mimetype="application/json")
    return resp, '', 200

  except Exception as err:
    return 'Error retrieving timeslot info for professional: %s' % str(err), \
            'user_id: %s, data: %s, request.url: %s' \
                % (user_id, str(data), request.url), 400
