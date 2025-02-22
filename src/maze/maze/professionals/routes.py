from maze import app, g
from flask import Flask, request, flash, session, redirect, url_for, jsonify
from flask.ext.mail import Message, Mail
from models import db, Profession, Professionals, Credentials, ProfessionalRatings, SubProfession, ProfHasKeywords, ExactKeywordsProf, ApproxKeywordsProf, ProfTimeSlots
from models import prof_table,cred_table, rating_table, timeslot_table
import json
from maze.users.models import User
from flask import make_response, request, current_app
from flask import Response
import re
from maze.common import errorhandler
from datetime import datetime

import pytz
from routes_keyword import add_keywords

#--------------------------------------------------
# PROFESSIONALS APIS
#-------------------------------------------------

@app.route('/professionals', methods=['POST'])
@errorhandler
#@crossdomain
def create_professional():
    data = request.get_json(force=True)
    try: 
        profession = data['profession']
        prof = Profession.query.filter_by(professionName = profession)
        if not prof:
            return "Invalid Profession", 'user_id: %s, data: %s, request.url: %s' \
                    % (data['userId'], str(data), request.url),  400
        subprofession = data.get('subprofession',None)
        subprofession2 = data.get('subprofession2',None)
        subprofession3 = data.get('subprofession3',None)
        if subprofession:
            subprof = SubProfession.query.filter_by(professionName = subprofession)
            if not subprof:
                return "Invalid SubProfession", 'user_id: %s, data: %s, request.url: %s' \
                    % (data['userId'], str(data), request.url), 400
        
        if subprofession2:
            subprof = SubProfession.query.filter_by(professionName = subprofession2)
            if not subprof:
                return "Invalid SubProfession", 'user_id: %s, data: %s, request.url: %s' \
                    % (data['userId'], str(data), request.url), 400

        if subprofession3:
            subprof = SubProfession.query.filter_by(professionName = subprofession3)
            if not subprof:
                return "Invalid SubProfession", 'user_id: %s, data: %s, request.url: %s' \
                    % (data['userId'], str(data), request.url), 400

        business = data.get('business', None)
        if not business:
            business = False

        newprof = Professionals (data['userId'], profession, subprofession, \
                    subprofession2, subprofession3, business)
        db.session.add(newprof)

        newrating = ProfessionalRatings (data['userId'], profession, subprofession)
        db.session.add(newrating)

        newcred = Credentials (data['userId'])
        db.session.add(newcred)

        newtime = ProfTimeSlots (data['userId'])
        db.session.add(newtime)

        user = User.query.filter_by(userId=data['userId']).first()
        if not user:
            return 'User not found', 'user_id: %s, data: %s, request.url: %s' \
                    % (data['userId'], str(data), request.url), 400

        user.update({'isProfessional':True})
        user.update({'profession':profession})
        user.update({'subprofession':subprofession})

        db.session.commit()

        data = json.dumps({'Professional':'Success'})
        resp = Response(response=data,
                status=200, \
                mimetype="application/json")

        return resp, '', 200

    except Exception as err:
            return 'Error creating user: %s' % str(err), 'data: %s, request.url: %s' \
                    % (str(data), request.url), 500


#tables = [{'Professionals',},{'Credentials',''},{'Portfolio',''},{'Campaign',''}]
table_names = [Professionals,Credentials,ProfTimeSlots]
attr_table = {'Rating':ProfessionalRatings}
#,'Campaign':Campaign}

def update_tables(tables, user_id):
    ##import pdb; pdb.set_trace()
    for table,value in tables.iteritems():
        #Time Slots#
        '''
        if table == ProfTimeSlots:
            #import pdb; pdb.set_trace()
            user = User.query.filter_by(userId=user_id).first()
            user_tz = g.timezone(g.geocode(user.city).point)
            if value:
                user = table.query.filter_by(userId=user_id).first()
                if user:
                    for val in value:
                        for k,v in val.items():
                            new_list = []
                            for obj in v:
                                 starttime1 = datetime.strptime(obj, "%I:%M %p")
                                 localdt = user_tz.localize(starttime1)
                                 starttime1 = localdt.astimezone(pytz.UTC)
                                 starttime1 = starttime1.strftime("%I:%M %p")
                                 new_list.append(starttime1)
                            subp = (',').join(new_list)
                            user.update({k:subp})
        '''
        # Everything Else#
        if value:
            user = table.query.filter_by(userId=user_id).first()
            if user:
                for val in value:
                    for k,v in val.items():
                        if type(v) is list:
                            subp = (',').join(v)
                            user.update({k:subp})
                        else:
                            user.update(val)

def increment_attributes(table, attrs, user_id):
    user = table.query.filter_by(userId=user_id).first()
    for attr in attrs:
        user.increment(attr)
        #user.increment("totalReviews")
        if attr in ['num1star','num2star','num3star','num4star','num5star']:
            avgRating = (user.num1star*1 + user.num2star*2 + user.num3star*3
                     +  user.num4star*4 + user.num5star*5 ) / (user.num1star + user.num2star + user.num3star
                     +  user.num4star + user.num5star)
            user.update({'avgRating':avgRating})         

@app.route('/professionals/<int:user_id>', methods=['PUT'])
@errorhandler
def update_professional(user_id):
    data = request.get_json(force=True)
    tables = {k: [] for k in table_names}
    kw_list = []
    try: 
        user = Professionals.query.filter_by(userId=user_id).first()
        if user:

            for key in data.keys():
                if key in ['worksAt', 'degrees', 'schools', 'courses', 'jobtitle']:
                    kw_list.append({key:data[key]})

                if key in attr_table.keys():
                    increment_attributes(attr_table[key], data[key], user_id)
                elif key in prof_table:
                    tables[Professionals].append({key:data[key]})
                elif key in cred_table:
                    tables[Credentials].append({key:data[key]})
                elif key in timeslot_table:
                    tables[ProfTimeSlots].append({key:data[key]})
                elif key == 'keywords':
                    add_keywords(user_id, data['keywords'], user.profession)
                else:
                    return 'No such entry in professional DB', 400
    
            update_tables(tables, user_id) 
            # Add these keywords as well
            for kw in kw_list:
                add_keywords(user_id, kw.values()[0], user.profession)
            db.session.commit()
            userdata = User.query.filter_by(userId=user_id).first()

            user_info = userdata.to_dict()
            user_info = userdata.data_pop(user_info)
            
            data = json.dumps(user_info)
            resp = Response(response=data,
                status=200, \
                mimetype="application/json")

            return resp, '' , 200
        else:
            return 'User not found', 'user_id: %s, data: %s, request.url: %s' \
                    % (user_id, str(data), request.url), 400 

    except Exception as err:
            #log.error('User could not be found: %', err) 
            return  'Error updating Professionals data:%s' % str(err), 'user_id: %s, data: %s, request.url: %s' \
                    % (user_id, str(data), request.url), 500

@app.route('/professionals/maze/<string:maze_id>', methods=['GET'])
@errorhandler
def get_prof_from_mazeid(maze_id):
    #import pdb; pdb.set_trace()
    try:
        prof = Professionals.query.filter_by(mazeId = maze_id).first()
        if not prof:
            return 'Maze id not found', '', 400
        resp = Response(response=json.dumps({'profId' : prof.userId}),
                status=200, \
                mimetype="application/json")

        return resp, '', 200

    except Exception as err:
        if err.code != 200:
            return  'Error while retreiving prof from maze id:%s' % str(err), 'maze_id: %s, request.url: %s' \
                    % (maze_id, request.url), 400

@app.route('/professionals/mazeavail/<string:maze_id>', methods=['GET'])
@errorhandler
def mazeid_avail(maze_id):
    #import pdb; pdb.set_trace()
    try:
        prof = Professionals.query.filter_by(mazeId = maze_id).first()
        if not prof:
            return 'Maze id available', '', 200
        else:
            return 'Maze id not available', '', 400


    except Exception as err:
        if err.code != 200:
            return  'Error while retreiving prof from maze id:%s' % str(err), 'maze_id: %s, request.url: %s' \
                    % (maze_id, request.url), 400

@app.route('/professionals/maze/<int:user_id>', methods=['POST'])
@errorhandler
def create_mazeid(user_id):
    #import pdb; pdb.set_trace()
    try:
        data = request.get_json(force=True)
        maze_id = data['mazeId']
        prof = Professionals.query.filter_by(mazeId = maze_id).first()
        if prof:
            return 'Maze id exists', '' , 400

        prof = Professionals.query.filter_by(userId = user_id).first()
        prof.update({'mazeId': maze_id})
        db.session.commit()

        resp = Response(response=json.dumps(prof.to_dict()),
                status=200, \
                mimetype="application/json")

        return resp, '', 200

    except Exception as err:
        if err.code != 200:
            return  'Error while retreiving prof from maze id:%s' % str(err), 'maze_id: %s, request.url: %s' \
                    % (maze_id, request.url), 400


'''
@app.route('/professionals/<int:user_id>', methods=['DELETE'])
def delete_professional(user_id):
    ###import pdb; pdb.set_trace()
    try: 
            prof = Professionals.query.filter_by(userid=user_id).first()
            if prof:
                db.session.delete(prof)
                db.session.commit()
                return json.dumps(prof.to_dict())
            else:
                return 'User %s not found' %user_id

    except Exception as err:
            #log.error('User could not be found: %', err) 
            if err.code != 200:
                return  'Error :%s' %err.description


@app.route('/professionals/acceptsqanda', methods=['GET'])
def get_prof_qanda():
    result = []
    ###import pdb; pdb.set_trace()
    try: 
            profs = Professionals.query.filter_by(acceptsQandA=True)
            for prof in profs:
                result.append(prof.to_dict())
            return json.dumps(result)

    except Exception as err:
            #log.error('User could not be found: %', err) 
            if err.code != 200:
                return  'Error :%s' %err.description

@app.route('/professionals/acceptsvideo', methods=['GET'])
def get_prof_video():
    ###import pdb; pdb.set_trace()
    result = []
    try: 
            profs = Professionals.query.filter_by(acceptsVideo=True)
            for prof in profs:
                result.append(prof.to_dict())
            return json.dumps(result)

    except Exception as err:
            #log.error('User could not be found: %', err) 
            if err.code != 200:
                return  'Error :%s' %err.description



@app.route('/professionals/', methods=['GET'])
def show_professionals():
    ###import pdb; pdb.set_trace()
    result = []
    profs = Professionals.query.all()
    for prof in profs:
        result.append(prof.to_dict())
    return json.dumps(result)
'''


