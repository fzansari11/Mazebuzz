from maze import app
from flask import Flask, render_template, request, flash, session, redirect, url_for, jsonify
from flask.ext.mail import Message, Mail
from models import db, Profession, Professionals, Credentials, ProfessionalRatings, SubProfession, Keywords 
from models import prof_table, cred_table, rating_table
import json

from datetime import timedelta
from flask import make_response, request, current_app
from flask import Response
from maze.common import errorhandler

# ------------------------
# PROFESSION APIS
# ----------------------

@app.route('/professions', methods=['POST'])
@errorhandler
def create_profession():
    data = request.get_json(force=True)
    try: 
        prof = Profession.query.filter_by(professionName = data['professionName']).first()
        if prof:
            return 'Profession exists', 'request.url: %s' \
                    % (request.url), 400
        newprof = Profession(data['professionName'].title())
        db.session.add(newprof)

        # Add profession to keyword table
        kw = Keywords.query.filter_by(keyword = data['professionName']).first()
        if not kw:
            kw = Keywords(data['professionName'].lower(), True)
            db.session.add(kw)

        db.session.commit()

        resp = Response(response="Success",
                status=200)

        return resp, '', 200

    except Exception as err:
            return 'Error creating user: %s' %str(err), 'request.url: %s' \
                    % (request.url), 400

@app.route('/professions/sub', methods=['POST'])
@errorhandler
def create_subprofession():
    data = request.get_json(force=True)
    try: 
        parentprof = Profession.query.filter_by(professionName=data['parentProfessionName']).first()
        if not parentprof:
            return 'No such Parent Profession exists', 'data: %s, request.url: %s' \
                    % (str(data), request.url), 400

        prof = SubProfession.query.filter_by(professionName = data['professionName']).first()
        if prof:
            return 'Profession exists', 'request.url: %s' \
                    % (request.url), 400
        newprof = SubProfession (data['professionName'].title())
        db.session.add(newprof)

        # Add subprofession to keyword table
        kw = Keywords.query.filter_by(keyword = data['professionName']).first()
        if not kw:
            kw = Keywords(data['professionName'].lower(), True)
            db.session.add(kw)

        subp = parentprof.subprofessions
        if not subp:
            subp = str(newprof.professionId)
        else:   
            subp_list = subp.split(',')
            subp_list.append(str(newprof.professionId))
            subp = (',').join(subp_list)
            
        parentprof.update({'subprofessions' : subp})
        db.session.commit()
        resp = Response(response="Success",
                status=200)

        return resp, '', 200
        
    except Exception as err:
            return 'Error creating SubProfession: %s' %str(err), 'request.url: %s' \
                    % (request.url), 400

import collections
@app.route('/professions', methods=['GET'])
@errorhandler
def show_professions():
    result = []
    professions = Profession.query.all()
    prof_dict = {}
    for profession in professions:
        subprof_list = []
        if profession.subprofessions:
            subprofessions = profession.subprofessions.split(',')
            for subprofession in subprofessions:
                subprof = SubProfession.query.filter_by(professionId=int(subprofession)).first()
                #subprof_list.append({subprof.professionName: subprof.professionId})
                subprof_list.append(subprof.professionName)
                subprof_list = sorted(subprof_list)
        #subprof_list.append({"All": profession.professionId})
        subprof_list.append("All")
        prof_dict[profession.professionName] = subprof_list
            
    prof1_dict = collections.OrderedDict()
    for key, value in sorted(prof_dict.items()):
        prof1_dict[key] = value
    data = json.dumps(prof1_dict)
    resp = Response(response=data,
                status=200, \
                mimetype="application/json")

    return resp, '' , 200
'''
@app.route('/professions/get_professionid/<profession>', methods=['GET'])
def get_professionid(profession):
    ###import pdb; pdb.set_trace()
    try: 
            prof = Profession.query.filter_by(professionName=profession).first()
            if prof:
                return json.dumps({"professionId": prof.professionId})
            else:
                return 'Profession %s not found' %profession

    except Exception as err:
            #log.error('User could not be found: %', err) 
            if err.code != 200:
                return  'Error :%s' %err.description'''
