from maze import app
from flask import Flask, render_template, request, flash, session, redirect, url_for, jsonify
from flask.ext.mail import Message, Mail
from models import db, Profession, Professionals, Portfolio, Campaign 
import json


@app.route('/campaign', methods=['POST'])
def create_campaign():
    ###import pdb; pdb.set_trace()
    data = request.get_json(force=True)
    try: 
        newcampaign = Campaign (data['campaignId'],
                    data['startDate'],
                    data['endDate'],
                    data['offeredPrice'],
                    data['noOfRequestsPerDay'],
                    data['availableMonday'],
                    data['availableTuesday'],
                    data['availableWednesday'],
                    data['availableThursday'],
                    data['availableFriday'],
                    data['availableSaturday'],
                    data['availableSunday'],
                    data['totalOccupiedMon'],
                    data['totalOccupiedTue'],
                    data['totalOccupiedWed'],
                    data['totalOccupiedThur'],
                    data['totalOccupiedFri'],
                    data['totalOccupiedSat'],
                    data['totalOccupiedSun'])
    
        db.session.add(newcampaign)
        db.session.commit()
        campaign = Campaign.query.filter_by(campaignId=data['campaignId']).first()

    except Exception as err:
            #log.error('User %s could not be created: %' %(data[userid], err))  
            return 'Error creating user: %s' %err
    return json.dumps(campaign.to_dict()) 

@app.route('/campaign/<int:campaign_id>', methods=['GET'])
def get_campaign(campaign_id):
    ###import pdb; pdb.set_trace()
    try: 
            campaign = Campaign.query.filter_by(campaignId=campaign_id).first()
            if campaign:
                return json.dumps(campaign.to_dict())
            else:
                return 'User %s not found' %campaign_id

    except Exception as err:
            #log.error('User could not be found: %', err) 
            if err.code != 200:
                return  'Error :%s' %err.description


@app.route('/campaignportfolio/<int:campaign_id>', methods=['PUT'])
def update_campaign(campaign_id):
    ###import pdb; pdb.set_trace()
    data = request.get_json(force=True)
    try: 
            campaign = Campaign.query.filter_by(campaignId=campaign_id).first()
            if campaign:
                campaign.update(data)
                db.session.commit()
                return json.dumps(campaign.to_dict())
            else:
                return 'User %s not found' %campaign_id

    except Exception as err:
            #log.error('User could not be found: %', err) 
            if err.code != 200:
                return  'Error :%s' %err.description


@app.route('/campaign/<int:campaign_id>', methods=['DELETE'])
def delete_campaign(campaign_id):
    ###import pdb; pdb.set_trace()
    try: 
            campaign = Campaign.query.filter_by(campaignId=campaign_id).first()
            if port:
                db.session.delete(campaign)
                db.session.commit()
                return json.dumps(port.to_dict())
            else:
                return 'User %s not found' %campaign_id

    except Exception as err:
            #log.error('User could not be found: %', err) 
            if err.code != 200:
                return  'Error :%s' %err.description

