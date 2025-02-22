from maze import app, g
from flask import Flask, render_template, request, flash, session, redirect, url_for, jsonify
from flask.ext.mail import Message, Mail
from models import db, Profession, SubProfession, Professionals, ProfessionalRatings, Credentials, ProfHasKeywords, ExactKeywordsProf, ApproxKeywordsProf, ProfTimeSlots, Keywords
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

def add_keywords(user_id, keywords, profession, subprofession=None):
    # Add all keywords for this offer
    #keywords = keywords.split(',')
    for keyword in keywords:
        keyword = keyword.strip().lower()
        # Add keyword to prof DB
        exist_kw = ProfHasKeywords.query.filter_by(userId = user_id).filter_by(keyword = keyword).first()
        if exist_kw:
            continue
        prof = ProfHasKeywords(user_id, keyword)
        db.session.add(prof)
        
        # Add keyword to keyword DB
        ekw = ExactKeywordsProf.query.filter_by(keyword = keyword).filter_by(userId = user_id).first()
        if not ekw:
            newkw = ExactKeywordsProf(keyword, user_id, profession)
            db.session.add(newkw)
        
        # Add keyword to keyword table
        keyw = Keywords.query.filter_by(keyword = keyword).first()
        if not keyw:
            mykw = Keywords(keyword)
            db.session.add(mykw)

        if ' ' in keyword:
           kw = keyword.split(' ')
           for k in kw:
               k = k.strip().lower()
               user = ExactKeywordsProf.query.filter_by(keyword = k).filter_by(userId = user_id).first()
               if user:
                   continue
               apkw = ApproxKeywordsProf.query.filter_by(keyword = k).filter_by(userId = user_id).first()
               if not apkw:
                    newkw = ApproxKeywordsProf(k, user_id, profession)
                    db.session.add(newkw)
        #db.session.commit()

# Get all professionals for keywords
@app.route('/professionals/keyword/<profession>/<keyword>', methods=['GET'])
@errorhandler
def show_professionals_keywords(profession, keyword):
    response_data = []
    # Remove all leading and trailing spaces
    keyword = keyword.lower().strip()

    ###### Extract all profs from exact keywords
    prof_list = []
    if profession.lower().strip() == 'all':
            profs = ExactKeywordsProf.query.filter_by(keyword = keyword).\
                    with_entities(ExactKeywordsProf.userId).all()
    else:
        profs = ExactKeywordsProf.query.filter_by(profession=profession).filter_by(keyword = keyword).\
                                    with_entities(ExactKeywordsProf.userId).all()
        #if not profs:
        #    profs = ExactKeywordsProf.query.filter_by(keyword = keyword).\
        #            with_entities(ExactKeywordsProf.userId).all()

    if profs:
        prof_list = [i[0] for i in profs]

    ###### Extract all profs from approximate keywords
    ap_prof_list = []
    if profession.lower().strip() == 'all':
        ap_profs = ApproxKeywordsProf.query.filter_by(keyword = keyword).\
                            with_entities(ApproxKeywordsProf.userId).all()
    else:
        ap_profs = ApproxKeywordsProf.query.filter_by(profession=profession).filter_by(keyword = keyword).\
                            with_entities(ApproxKeywordsProf.userId).all()
        #if not ap_profs:
        #    ap_profs = ApproxKeywordsProf.query.filter_by(keyword = keyword).\
        #                    with_entities(ApproxKeywordsProf.userId).all()

    if ap_profs:
        ap_prof_list = [i[0] for i in ap_profs]

    ## Split the keyword based on spaces
    split_prof_list = []
    if ' ' in keyword:
        kws = keyword.split(' ')
        for kw in kws:
            splitkw_profs = ExactKeywordsProf.query.filter_by(profession=profession).filter_by(keyword = kw).with_entities(ExactKeywordsProf.userId).all()
            if not splitkw_profs:
                splitkw_profs = ApproxKeywordsProf.query.filter_by(profession=profession).filter_by(keyword = kw).with_entities(ApproxKeywordsProf.userId).all()
            if splitkw_profs:
                split_prof_list = [i[0] for i in splitkw_profs]

    # Take only unique values
    final_profs = []
    for x in itertools.chain.from_iterable((prof_list, ap_prof_list, split_prof_list)):
        if x not in final_profs:
            final_profs.append(x)

    if final_profs:
        total_count = Professionals.query.filter(Professionals.userId.in_(final_profs)).count()
        profs = Professionals.query.filter(Professionals.userId.in_(final_profs)).all()
        ratings = ProfessionalRatings.query.filter(ProfessionalRatings.userId.in_(final_profs)).all()
        cred = Credentials.query.filter(Credentials.userId.in_(final_profs)).all()
        users = User.query.filter(User.userId.in_(final_profs)).all()

    result_list = [] 
    for i in xrange(len(profs)):
        if not users[i].isEmailVerified or not users[i].isPhoneVerified or not profs[i].isVerified \
        or not profs[i].readyServe:
            continue
        result = dict(profs[i].to_dict().items() 
                         + ratings[i].to_dict().items()
                         + users[i].to_dict().items() + cred[i].to_dict().items())
        result['lastOnline'] = str(result['lastOnline'])
        result.pop('pwdhash',None)
        result_list.append(result)

    if len(result_list) < 1:
        return "No Professionals", 'request.url: %s' % (request.url),  400

    total_pages = (total_count / 10) if total_count > 10 else 1
            
    response_data = {'Total entries' : total_count, "entries per page": "10", "Total pages": total_pages,'userdata' : result_list}
       
    resp = Response(response=json.dumps(response_data),
                status=200, \
                mimetype="application/json")
    return resp, '', 200

@app.route('/users/search', methods=['GET'])
@errorhandler
def search_keywords():
    search = request.args.get('term')
    results = []
    results_list = []

    ''' Commenting this out to increase performance
    if profession.lower().strip() == 'all':
            results = ExactKeywordsProf.query.filter(ExactKeywordsProf.keyword.like('%' + search + '%')).\
                        with_entities(ExactKeywordsProf.keyword).all()
    else:
        results = ExactKeywordsProf.query.filter_by(profession = profession).filter(ExactKeywordsProf.keyword.\
                    like('%' + search + '%')).with_entities(ExactKeywordsProf.keyword).all()
        if not results:
            results = ExactKeywordsProf.query.filter(ExactKeywordsProf.keyword.like('%' + search + '%')).\
                        with_entities(ExactKeywordsProf.keyword).all()
    '''
    results = Keywords.query.filter(Keywords.keyword.like('%' + search + '%')).\
                        with_entities(Keywords.keyword).all()

    #import pdb; pdb.set_trace()
    if results:
        results_list = [i[0] for i in results]
    resp = Response(response=json.dumps(results_list),
                status=200, \
                mimetype="application/json")
    return resp, '', 200



@app.route('/professionals/search/profession/<profession>', methods=['GET'])
@errorhandler
def isProfession(profession):
    result = Keywords.query.filter_by(keyword = profession).first()
    
    if result:
        response = {'isProfession':result.prof}
    else:
        response = {'isProfession':False}

    resp = Response(response=json.dumps(response),
                status=200, \
                mimetype="application/json")
    return resp, '', 200
