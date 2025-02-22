from maze import app
from flask import Flask, render_template, request, flash, session, redirect, url_for, jsonify
from flask.ext.mail import Message, Mail
from models import db, Service, ProfessionHasService, Offer, ProfessionalHasOffer, ServiceHasOffer
from models import ExactKeywords, ApproxKeywords, ExactKeywordsProf, ApproxKeywordsProf
import json
from maze.common import crossdomain, email

from datetime import timedelta
from flask import make_response, request, current_app
from flask import Response
import itertools

# ------------------------
# PROFESSION APIS
# ----------------------

@app.route('/service', methods=['POST'])
#@crossdomain
def create_service():
    ##import pdb; pdb.set_trace()
    data = request.get_json(force=True)
    try: 
        newservice = Service(data['serviceName'])
    
        db.session.add(newservice)
        service = Service.query.filter_by(serviceName=data['serviceName']).first()

        prof = ProfessionHasService(data['professionId'], service.serviceId)
        db.session.add(prof)
        db.session.commit()

        resp = Response(response="Success",
                status=200)

        return resp

    except Exception as err:
            #log.error('User %s could not be created: %' %(data[userid], err))  
            return 'Error creating service: %s' %err, 500

@app.route('/service/<int:profession_id>', methods=['GET'])
def show_services(profession_id):
    ##import pdb; pdb.set_trace()
    result = []
    services = ProfessionHasService.query.filter_by(professionId=profession_id).all()

    if not services:
        return "No services for this profession", 500
    #take all service Ids
    service_list = []
    for service in services:
        service_list.append(service.serviceId)

    service_details = Service.query.filter(Service.serviceId.in_(service_list)).all()
    result = []
    for i in xrange(len(service_details)):
        result.append(service_details[i].to_dict())

    response_data = result
    resp = Response(response=json.dumps(response_data),
                status=200, \
                mimetype="application/json")
    return resp


@app.route('/offer/<int:user_id>', methods=['POST'])
#@crossdomain
def create_offer(user_id):
    ##import pdb; pdb.set_trace()
    data = request.get_json(force=True)
    try: 
        image1 = data['image1'] if data.get('image1') else ''
        image2 = data['image2'] if data.get('image2') else ''
        image3 = data['image3'] if data.get('image3') else ''
        video = data['video'] if data.get('video') else ''

        newoffer = Offer(data['title'],data['price'],data['details'],image1, image2, image3, video)
        db.session.add(newoffer)
        db.session.commit()

        prof = ProfessionalHasOffer(user_id, newoffer.offerId)
        db.session.add(prof)
        serv = ServiceHasOffer(data['serviceId'], newoffer.offerId)
        db.session.add(serv)

        # Add all keywords for this offer
        keywords = data.get('keywords','')
        keywords = keywords.split(',')
        for keyword in keywords:
            keyword = keyword.strip().lower()
            newkw = ExactKeywords(keyword, newoffer.offerId)
            db.session.add(newkw)
            if ' ' in keyword:
                kw = keyword.split(' ')
                for k in kw:
                    k = k.strip().lower()
                    offer = ExactKeywords.query.filter_by(keyword = k).first()
                    if offer:
                        continue
                    newkw = ApproxKeywords(k, newoffer.offerId)
                    db.session.add(newkw)

        db.session.commit()

        resp = Response(response="Success",
                status=200)

        return resp

    except Exception as err:
            #log.error('User %s could not be created: %' %(data[userid], err))  
            return 'Error creating offer: %s' %err, 500


@app.route('/offers/service/<int:service_id>', methods=['GET'])
def show_offers_service(service_id):
    ##import pdb; pdb.set_trace()
    result = []
    services = ServiceHasOffer.query.filter_by(serviceId=service_id).with_entities(ServiceHasOffer.offerId).all()

    if not services:
        return "No offers for this service", 500
    #take all service Ids
    offer_list = [i[0] for i in services]

    offer_details = Offer.query.filter(Offer.offerId.in_(offer_list)).all()
    response_data = [offer_details[i].to_dict() for i in xrange(len(offer_details))] if offer_details else []

    resp = Response(response=json.dumps(response_data),
                status=200, \
                mimetype="application/json")
    return resp

@app.route('/offers/professional/<int:user_id>', methods=['GET'])
def show_offers_professional(user_id):
    ##import pdb; pdb.set_trace()
    result = []
    services = ProfessionalHasOffer.query.filter_by(userId=user_id).with_entities(ProfessionalHasOffer.offerId).all()

    if not services:
        return "No offers for this professional", 500
    #take all service Ids
    offer_list = [i[0] for i in services]

    offer_details = Offer.query.filter(Offer.offerId.in_(offer_list)).all()
    response_data = [offer_details[i].to_dict() for i in xrange(len(offer_details))] if offer_details else []

    resp = Response(response=json.dumps(response_data),
                status=200, \
                mimetype="application/json")
    return resp


@app.route('/offer/<int:offer_id>', methods=['GET'])
def show_offer(offer_id):
    ##import pdb; pdb.set_trace()
    result = []
    offer = Offer.query.filter_by(offerId=offer_id).first()

    response_data = offer.to_dict()
    resp = Response(response=json.dumps(response_data),
                status=200, \
                mimetype="application/json")
    return resp


# Get all offers for keywords
@app.route('/offers/keyword/<keyword>', methods=['GET'])
def show_offers_keywords(keyword):
    ##import pdb; pdb.set_trace()
    response_data = []
    # Remove all leading and trailing spaces
    keyword = keyword.lower().strip()

    ###### Extract all offers from exact keywords
    offer_list = []
    offers = ExactKeywords.query.filter_by(keyword = keyword).with_entities(ExactKeywords.offerId).all()
    if offers:
        offer_list = [i[0] for i in offers]

    ###### Extract all offers from approximate keywords
    ap_offer_list = []
    ap_offers = ApproxKeywords.query.filter_by(keyword = keyword).with_entities(ApproxKeywords.offerId).all()
    if ap_offers:
        ap_offer_list = [i[0] for i in ap_offers]

    ## Split the keyword based on spaces
    split_offer_list = []
    if ' ' in keyword:
        kws = keyword.split(' ')
        for kw in kws:
            splitkw_offers = ExactKeywords.query.filter_by(keyword = kw).with_entities(ExactKeywords.offerId).all()
            if not splitkw_offers:
                splitkw_offers = ApproxKeywords.query.filter_by(keyword = kw).with_entities(ApproxKeywords.offerId).all()
            if splitkw_offers:
                split_offer_list += [i[0] for i in splitkw_offers]

    # Take only unique values
    final_offers = []
    for x in itertools.chain.from_iterable((offer_list, ap_offer_list, split_offer_list)):
        if x not in final_offers:
            final_offers.append(x)

    offer_details = Offer.query.filter(Offer.offerId.in_(final_offers)).all()
    response_data = [offer_details[i].to_dict() for i in xrange(len(offer_details))] if offer_details else []

    resp = Response(response=json.dumps(response_data),
                status=200, \
                mimetype="application/json")
    return resp

    
