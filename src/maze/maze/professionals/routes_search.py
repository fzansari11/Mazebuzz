from maze import app, g
from flask import Flask, render_template, request, flash, session, redirect, url_for, jsonify
from flask.ext.mail import Message, Mail
from models import db, Profession, SubProfession, Professionals, ProfessionalRatings, Credentials, ProfHasKeywords, ExactKeywordsProf, ApproxKeywordsProf, ProfTimeSlots
from maze.users.models import User, Appointment, ProfConsulted
from maze.common import errorhandler
import json
import itertools
import pytz
from sqlalchemy import desc

from flask import make_response, request, current_app
from flask import Response

from datetime import datetime
import datetime

def add_day (key):
    if key == 'monstart':
        key = 'tuesstart'
    elif key == 'tuesstart':
        key = 'wedstart'
    elif key == 'wedstart':
        key = 'thursstart'
    elif key == 'thursstart':
        key = 'fristart'
    elif key == 'fristart':
        key = 'satstart'
    elif key == 'satstart':
        key = 'sunstart'
    elif key == 'sunstart':
        key = 'monstart'
    elif key == 'monend':
        key = 'tuesend'
    elif key == 'tuesend':
        key = 'wedend'
    elif key == 'wedend':
        key = 'thursend'
    elif key == 'thursend':
        key = 'friend'
    elif key == 'friend':
        key = 'satend'
    elif key == 'satend':
        key = 'sunend'
    elif key == 'sunend':
        key = 'monend'
    else:
        "error"
    return key

def subtract_day (key):
    if key == 'monstart':
        key = 'sunstart'
    elif key == 'tuesstart':
        key = 'monstart'
    elif key == 'wedstart':
        key = 'tuesstart'
    elif key == 'thursstart':
        key = 'wedstart'
    elif key == 'fristart':
        key = 'thursstart'
    elif key == 'satstart':
        key = 'fristart'
    elif key == 'sunstart':
        key = 'satstart'
    
    elif key == 'monend':
        key = 'sunend'
    elif key == 'tuesend':
        key = 'monend'
    elif key == 'wedend':
        key = 'tuesend'
    elif key == 'thursend':
        key = 'wedend'
    elif key == 'friend':
        key = 'thursend'
    elif key == 'satend':
        key = 'friend'
    elif key == 'sunend':
        key = 'satend'
    else:
        return 'Error'

    return key


def proftime_convert_tz(proftime_dict, user_tz, user_id):
    days = {'satstart': [], 'thursstart': [], 'thursend': [], 'wedstart': [], 'tuesstart': [], 'fristart': [], 'sunstart': [], 'monend': [], 'satend': [], 'monstart': [], 'tuesend': [], 'wedend': [], 'friend': [], 'sunend': []}
    # prof_tz
    prof = User.query.filter_by(userId=user_id).first()

    # Get timezone you need string like 'New York, NY or 'Newark, CA'
    city = prof.city
    state = prof.state
    if not prof.city:
        city ='San Jose'
    if not prof.state:
        state = 'California'
    city_str = city + ',' + state
    prof_tz = g.timezone(g.geocode(city_str).point)

    day_tuples = [('monstart', 'monend'), ('tuesstart', 'tuesend'),  ('wedstart', 'wedend'),  ('thursstart', 'thursend'),
             ('fristart', 'friend'),  ('satstart', 'satend'), ('sunstart', 'sunend')]

    for day in day_tuples:
        start_times = None
        if proftime_dict[day[0]]:
            start_times = proftime_dict[day[0]].split(',') # All start times for day
        if proftime_dict[day[1]]:
            end_times = proftime_dict[day[1]].split(',') # All end times for day
        if not start_times:
            continue

        for start,end in zip(start_times,end_times): # One start, end for this day
            starttime = datetime.datetime.strptime(start, "%I:%M %p")
            starttime = datetime.datetime.combine(datetime.datetime.now().date(), starttime.time())

            start_prof = prof_tz.localize(starttime) #localize based on prof_tz
            start_utc = start_prof.astimezone(pytz.UTC) # convert to UTC
            start_user = start_utc.astimezone(user_tz) # convert to user_tz

            endtime = datetime.datetime.strptime(end, "%I:%M %p")
            endtime = datetime.datetime.combine(datetime.datetime.now().date(), endtime.time())

            end_prof = prof_tz.localize(endtime) #localize based on prof_tz
            end_utc = end_prof.astimezone(pytz.UTC) # convert to UTC
            end_user = end_utc.astimezone(user_tz) # convert to user_tz

            # Prof -> PST 11pm  , User -> EST 2am
            if start_user.date() > start_prof.date():
                key1 = add_day(day[0])
                key2 = add_day(day[1])
                start_user = start_user.strftime("%I:%M %p")
                end_user = end_user.strftime("%I:%M %p")
                days[key1].append(start_user)
                days[key2].append(end_user)
            # Prof -> EST 1am , User -> PST 10pm
            elif start_user.date() < start_prof.date():
                key1 = subtract_day(day[0])
                key2 = subtract_day(day[1])
                start_user = start_user.strftime("%I:%M %p")
                days[key1].append(start_user)
                # Add overlap if start on previous day, end on next day
                if end_user.date() == end_prof.date():
                    end_user1 = end_user.strftime("%I:%M %p")
                    days[day[0]].append("12:00 AM")
                    days[day[1]].append(end_user1)
                end_user = end_user.strftime("%I:%M %p")
                days[key2].append(end_user)
            else: 
                start_user = start_user.strftime("%I:%M %p")
                if end_user.date() > end_prof.date():
                    end_user1 = end_user.strftime("%I:%M %p")
                    key1 = add_day(day[0])
                    key2 = add_day(day[1])
                    days[key1].append("12:00 am")
                    days[key2].append(end_user1)
                end_user = end_user.strftime("%I:%M %p")
                days[day[0]].append(start_user)
                days[day[1]].append(end_user)

    for k,v in days.items():
        proftime_dict[k] = (',').join(days[k])

    return proftime_dict




# Show one professional
@app.route('/professionals/own/<int:user_id>', methods=['GET'])
@errorhandler
def show_own_professional(user_id):
    try: 
            #user_tz = pytz.timezone(my_tz)
            user = User.query.filter_by(userId=user_id).first()
            if not user:
                return 'User not found', 'user_id: %s, request.url: %s' \
                    % (user_id, request.url), 400
            if not user.isEmailVerified:
                return "Professional not found", 'user_id: %s, request.url: %s' \
                    % (user_id, request.url), 400
            user_dict =  user.to_dict()
            user_dict = user.data_pop(user_dict)

            prof = Professionals.query.filter_by(userId=user_id).first()
            if not prof:
                return 'Professional not found', 'user_id: %s, request.url: %s' \
                    % (user_id, request.url), 400
            #if not prof.isVerified:
            #    return 'Professional not verified', 'user_id: %s, request.url: %s' \
            #        % (user_id, request.url), 400

            prof_dict =  prof.to_dict()

            cred = Credentials.query.filter_by(userId=user_id).first()
            if not cred:
                return 'Professional cred not found', 'user_id: %s, request.url: %s' \
                    % (user_id, request.url), 400
            cred_dict =  cred.to_dict()
            cred_dict.pop('userId')
            for k,v in cred_dict.iteritems():
                cred_dict[k] = v.split(",")

            rating = ProfessionalRatings.query.filter_by(userId=user_id).first()
            if not rating:
                return 'Professional Rating not found', 'user_id: %s, request.url: %s' \
                    % (user_id, request.url), 400

            proftime = ProfTimeSlots.query.filter_by(userId=user_id).first()
            proftime_dict = proftime.to_dict()
            proftime_dict.pop('userId')
            #if my_id and my_id != user_id:
            #proftime_dict = proftime_convert_tz(proftime_dict, user_tz, user_id)
            for k,v in proftime_dict.iteritems():
                if v and ',' in v:
                    proftime_dict[k] = v.split(",")
                elif v:
                    proftime_dict[k] = [v]
                else:
                    proftime_dict[k] = []

            keywords = ProfHasKeywords.query.filter_by(userId=user_id).all()
            kw_list = []
            kw = {}
            if keywords:
                for keyword in keywords:
                    kw_list.append(keyword.keyword)
            kw = {'keywords':kw_list}

            result = dict(user_dict.items() + prof_dict.items() + cred_dict.items() + rating.to_dict().items() + kw.items() + proftime_dict.items())

            resp = Response(response=json.dumps(result),
                        status=200, \
                        mimetype="application/json")

            return resp, '' , 200

    except Exception as err:
            #log.error('User could not be found: %', err) 
            return  'Error retrieving professional %s' % str(err), 'user_id: %s, request.url: %s' \
                    % (user_id, request.url), 400



'''
    for key, value in proftime_dict.items():
        if value:
            subp = value.split(',')
            for obj in subp:
                starttime1 = datetime.strptime(obj, "%I:%M %p")
                starttime1 = datetime.combine(datetime.now().date(), starttime1.time())
                localdt = prof_tz.localize(starttime1) #localize based on prof_tz
                starttime1 = localdt.astimezone(pytz.UTC) # convert to UTC
                starttime1 = starttime1.astimezone(user_tz) # convert to user_tz
                if localdt.date() < starttime1.date():
                    key1 = add_day(key)
                    starttime1 = starttime1.strftime("%I:%M %p")
                    days[key1].append(starttime1)
                elif localdt.date() > starttime1.date():
                    key1 = subtract_day(key)
                    starttime1 = starttime1.strftime("%I:%M %p")
                    days[key1].append(starttime1)
                else: 
                    starttime1 = starttime1.strftime("%I:%M %p")
                    days[key].append(starttime1)
    for k,v in days.items():
        proftime_dict[k] = (',').join(days[k])


    return proftime_dict
'''


# Show one professional
@app.route('/professionals/<int:user_id>', methods=['GET'])
@app.route('/professionals/<int:user_id>/<int:my_id>', methods=['GET'])
@errorhandler
def show_professional(user_id, my_id=0):
    try: 
            my_tz = None
            req = request.query_string.split('=')
            if len(req) > 1:
                my_tz = req[1]
            if not my_tz:
                my_tz = 'America/Los_Angeles'
                                                      
            user_tz = pytz.timezone(my_tz)
            user = User.query.filter_by(userId=user_id).first()
            if not user:
                return 'User not found', 'user_id: %s, request.url: %s' \
                    % (user_id, request.url), 400
            if not user.isEmailVerified or not user.isPhoneVerified:
                return "Professional was not found", 'user_id: %s, request.url: %s' \
                    % (user_id, request.url), 400
            user_dict =  user.to_dict()
            user_dict = user.data_pop(user_dict)

            prof = Professionals.query.filter_by(userId=user_id).first()
            if not prof:
                return 'Professional not found', 'user_id: %s, request.url: %s' \
                    % (user_id, request.url), 400
            if not prof.isVerified and my_id !=user_id:
                return 'Professional is not verified', 'user_id: %s, request.url: %s' \
                    % (user_id, request.url), 400

            if not prof.readyServe and my_id !=user_id:
                return 'Professional profile is under review', 'user_id: %s, request.url: %s' \
                    % (user_id, request.url), 400

            prof_dict =  prof.to_dict()
            if not prof_dict['business']:
                prof_dict['individual'] = True

            cred = Credentials.query.filter_by(userId=user_id).first()
            if not cred:
                return 'Professional cred not found', 'user_id: %s, request.url: %s' \
                    % (user_id, request.url), 400
            cred_dict =  cred.to_dict()
            cred_dict.pop('userId')
            for k,v in cred_dict.iteritems():
                if v:
                    cred_dict[k] = v.split(",") 
                

            rating = ProfessionalRatings.query.filter_by(userId=user_id).first()
            if not rating:
                return 'Professional Rating not found', 'user_id: %s, request.url: %s' \
                    % (user_id, request.url), 400

            proftime = ProfTimeSlots.query.filter_by(userId=user_id).first()
            proftime_dict = proftime.to_dict()
            proftime_dict.pop('userId')
            #if my_id and my_id != user_id:
            proftime_dict = proftime_convert_tz(proftime_dict, user_tz, user_id)
            for k,v in proftime_dict.iteritems():
                if v and ',' in v:
                    proftime_dict[k] = v.split(",")
                elif v:
                    proftime_dict[k] = [v]
                else:
                    proftime_dict[k] = []

            keywords = ProfHasKeywords.query.filter_by(userId=user_id).all()
            kw_list = []
            kw = {}
            if keywords:
                for keyword in keywords:
                    kw_list.append(keyword.keyword)
            kw = {'keywords':kw_list}

            result = dict(user_dict.items() + prof_dict.items() + cred_dict.items() + rating.to_dict().items() + kw.items() + proftime_dict.items())

            if my_id:
                my_user = User.query.filter_by(userId=my_id).first()
                if my_user:
                    #my_user_dict = { 'myEmailVerified' : my_user.isEmailVerified, 'myPhoneVerified' : my_user.isPhoneVerified}
                    result['myEmailVerified'] = my_user.isEmailVerified
                    result['myPhoneVerified'] = my_user.isPhoneVerified
            
                consult_dict = {}
                consult = ProfConsulted.query.filter(ProfConsulted.userid==my_id).filter(ProfConsulted.profid==user_id).first()
                if consult:
                    result['profConsulted'] = True
                    result['reviewed'] = consult.reviewed

            resp = Response(response=json.dumps(result),
                        status=200, \
                        mimetype="application/json")

            return resp, '' , 200

    except Exception as err:
            #log.error('User could not be found: %', err) 
            return  'Error retrieving professional %s ' % str(err), 'user_id: %s, request.url: %s' \
                    % (user_id, request.url), 400


# Highest Rating

@app.route('/professionals/search/<int:profession_id>/rating', methods=['GET'])
@app.route('/professionals/search/<int:profession_id>/rating/<int:page>', methods=['GET'])
@errorhandler
def search_professionals_rating(profession_id, page =1):
    ###import pdb; pdb.set_trace()
    try: 
       # query ratings table / paginate this
       ratings = ProfessionalRatings.query.filter_by(professionId=profession_id).order_by(ProfessionalRatings.avgRating).paginate(page, 1, False).items
            
       #take top 10 professionals
       profs_list = []
       for prof in ratings:
           profs_list.append(prof.userId)

       #use User id to reference all tables
       profs = Professionals.query.filter(Professionals.userId.in_(profs_list)).all()
       #campaign = Campaign.query.filter(Campaign.userId.in_(profs_list)).all()
       cred = Credentials.query.filter(Credentials.userId.in_(profs_list)).all()
       port = Portfolio.query.filter(Portfolio.userId.in_(profs_list)).all()
       users = User.query.filter(User.userId.in_(profs_list)).all()

       result_list = [] 
       for i in xrange(len(profs)):
            result = dict(profs[i].to_dict().items() 
                         #+ campaign[i].to_dict().items() 
                         + port[i].to_dict().items() + ratings[i].to_dict().items()
                         + users[i].to_dict().items() + cred[i].to_dict().items())
            result['lastOnline'] = str(result['lastOnline'])
            result_list.append(result)
       return json.dumps(result_list) 
        
    except Exception as err:
            #log.error('User %s could not be created: %' %(data[userid], err))  
            return 'Error creating user: %s' %err


# Soonest ending campaign
    
'''@app.route('/professionals/search/<int:profession_id>/campaign', methods=['GET'])
@app.route('/professionals/search/<int:profession_id>/campaign/<int:page>', methods=['GET'])
def search_professionals_campaign(profession_id, page =1):
    ###import pdb; pdb.set_trace()
    try: 
       # query ratings table / paginate this
       ratings = Campaign.query.filter_by(professionId=profession_id).order_by(Campaign.endDate).paginate(page, 1, False).items
            
       #take top 10 professionals
       profs_list = []
       for prof in ratings:
           profs_list.append(prof.userId)

       #use User id to reference all tables
       profs = Professionals.query.filter(Professionals.userId.in_(profs_list)).all()
       campaign = ProfessionalRatings.query.filter(Campaign.userId.in_(profs_list)).all()
       cred = Credentials.query.filter(Credentials.userId.in_(profs_list)).all()
       port = Portfolio.query.filter(Portfolio.userId.in_(profs_list)).all()
       users = User.query.filter(User.userId.in_(profs_list)).all()

       result_list = [] 
       for i in xrange(len(profs)):
            result = dict(profs[i].to_dict().items() + campaign[i].to_dict().items() 
                         + port[i].to_dict().items() + ratings[i].to_dict().items()
                         + users[i].to_dict().items() + cred[i].to_dict().items())
            result['startDate'] = str(result['startDate']) 
            result['endDate'] = str(result['endDate']) 
            result['lastOnline'] = str(result['lastOnline'])
            result_list.append(result)
       return json.dumps(result_list) 
        
    except Exception as err:
            #log.error('User %s could not be created: %' %(data[userid], err))  
            return 'Error creating user: %s' %err'''


# Search all professionals with professionId=x
    
@app.route('/professionals/search/<profession>', methods=['GET'])
@app.route('/professionals/search/<profession>/<int:page>', methods=['GET'])
@errorhandler
def search_professionals(profession, page =1):
    try: 
        # First find if profession passed is profession or subprofession
        is_profession = Profession.query.filter_by(professionName = profession).first()
        is_subprofession = SubProfession.query.filter_by(professionName = profession).first()

        if not is_subprofession and not is_profession:
            return "Invalid profession passed", 'request.url: %s' \
                    % (request.url),  400

        ''' Search all professionals with this subprofession '''
        if is_subprofession:
            total_count = Professionals.query.filter_by(subprofession=profession).count()
            # query professionals table / paginate this
            profs = Professionals.query.filter_by(subprofession=profession).paginate(page, 5, False).items

            if not profs:
                return "No professionals for this search", 'request.url: %s' \
                        % (request.url),  400
            
            #take top 10 professionals
            profs_list = [prof.userId for prof in profs]
            ''' Search all professionals with this profession '''
        else:
            total_count = Professionals.query.filter_by(profession=profession).count()
            # query professionals table / paginate this
            profs = Professionals.query.filter_by(profession=profession).paginate(page, 5, False).items

            if not profs:
                return "No professionals for this search", 'request.url: %s' \
                        % (request.url),  400
            
            #take top 10 professionals
            profs_list = [prof.userId for prof in profs]

        #use User id to reference all tables
        ratings = ProfessionalRatings.query.filter(ProfessionalRatings.userId.in_(profs_list)).all()
        cred = Credentials.query.filter(Credentials.userId.in_(profs_list)).all()
        users = User.query.filter(User.userId.in_(profs_list)).all()

        result_list = [] 
        for i in xrange(len(profs)):
            if not users[i].isEmailVerified or not users[i].isPhoneVerified or not profs[i].isVerified \
            or not profs[i].readyServe :
               continue
            result = dict(profs[i].to_dict().items() 
                         + ratings[i].to_dict().items()
                         + users[i].to_dict().items() + cred[i].to_dict().items())
            result['lastOnline'] = str(result['lastOnline'])
            result.pop('pwdhash',None)
            result_list.append(result)
        if len(result_list) < 1:
            return "No Professionals", 'request.url: %s' \
                    % (request.url),  400

        total_pages = (total_count / 10) if total_count > 10 else 1
            
        response_data = {'Total entries' : total_count, "entries per page": "10", "Total pages": total_pages,'userdata' : result_list}
       
        resp = Response(response=json.dumps(response_data),
                status=200, \
                mimetype="application/json")
        return resp, '', 200
        
    except Exception as err:
        return 'Could not find all professionals: %s' %str(err), 'request.url: %s' \
                    % (request.url), 500


@app.route('/professionals/search/all/<profession_id>', methods=['GET'])
@app.route('/professionals/search/all/<profession_id>/<int:page>', methods=['GET'])
@errorhandler
def search_all_professionals(profession_id, page =1):
    ##import pdb; pdb.set_trace()
    try: 
       profession = Profession.query.filter_by(professionName=profession_id).first()
       if not profession:
            return "No profession", 'request.url: %s' \
                    % (request.url),  400
       profs_list = []
       if profession.subprofessions:
            subprofessions = profession.subprofessions.split(',')
            for subprofession in subprofessions:
                subprof = SubProfession.query.filter_by(professionId=int(subprofession)).first()
                profs_list.append(subprof.professionName)

       # query ratings table / paginate this
       total_count = Professionals.query.filter(Professionals.profession.in_(profs_list)).count()
       profs = Professionals.query.filter(Professionals.profession.in_(profs_list)).all()
       ratings = ProfessionalRatings.query.filter(ProfessionalRatings.profession.in_(profs_list)).all()
       #take top 10 professionals
       users_list = [prof.userId for prof in ratings]
       cred = Credentials.query.filter(Credentials.userId.in_(users_list)).all()
       users = User.query.filter(User.professionName.in_(profs_list)).all()

       if not ratings:
            return "No professionals for this search", 'request.url: %s' \
                    % (request.url),  400
            
       #take top 10 professionals
       profs_list = [prof.userId for prof in ratings]

       result_list = [] 
       for i in xrange(len(profs)):
            if not users[i].isEmailVerified:
               continue
            if not users[i].isPhoneVerified:
               continue
            result = dict(profs[i].to_dict().items() 
                         + ratings[i].to_dict().items()
                         + users[i].to_dict().items() + cred[i].to_dict().items())
            result['lastOnline'] = str(result['lastOnline'])
            result.pop('pwdhash',None)
            result_list.append(result)
       if len(result_list) < 1:
            return "No Professionals", 'request.url: %s' \
                    % (request.url),  400

       total_pages = (total_count / 10) if total_count > 10 else 1
            
       response_data = {'Total entries' : total_count, "entries per page": "10", "Total pages": total_pages,'userdata' : result_list}
       
       resp = Response(response=json.dumps(response_data),
                status=200, \
                mimetype="application/json")
       return resp, '', 200
        
    except Exception as err:
            return 'Could not find all professionals: %s' %str(err), 'request.url: %s' \
                    % (request.url), 500
