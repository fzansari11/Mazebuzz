from maze import app
from flask import Flask, render_template, request, flash, session, redirect, url_for, jsonify
from flask.ext.mail import Message, Mail
from models import db, User, UserAttributes 
import json

@app.route('/attributes', methods=['POST'])
def create_attributes():
    ###import pdb; pdb.set_trace()
    data = request.get_json(force=True)
    try: 
        newattr = UserAttributes (data['userId'],
                    data['noOfQuestAsked'],
                    data['noOfVoiceCalls'],
                    data['noOfVideoCalls'],
                    data['noOfTimesPaid'],
                    data['noOfReviewsReqs'],
                    data['useAttributescol'])
    
        db.session.add(newuser)
        db.session.commit()
        userattr = UserAttributes.query.filter_by(userId=data['userId']).first()

        # Add user entry to attribute and Inbox table

    except Exception as err:
            #log.error('User %s could not be created: %' %(data[userid], err))  
            return 'Error creating user: %s' %err
    return json.dumps(userattr.to_dict()) 


@app.route('/attributes/<int:user_id>', methods=['GET'])
def show_attr(user_id):
    ###import pdb; pdb.set_trace()
    try: 
            attr = UserAttributes.query.filter_by(userId=user_id).first()
            if attr:
                return json.dumps(attr.to_dict())
            else:
                return 'User %s not found' %user_id

    except Exception as err:
            #log.error('User could not be found: %', err) 
            if err.code != 200:
                return  'Error :%s' %err.description


@app.route('/attributes/<int:user_id>', methods=['PUT'])
def update_attributes(user_id):
    ###import pdb; pdb.set_trace()
    data = request.get_json(force=True)
    try: 
            attr = UserAttributes.query.filter_by(userId=user_id).first()
            if attr:
                attr.update(data)
                db.session.commit()
                return json.dumps(attr.to_dict())
            else:
                return 'User %s not found' %user_id

    except Exception as err:
            #log.error('User could not be found: %', err) 
            if err.code != 200:
                return  'Error :%s' %err.description


@app.route('/attributes/<int:attribute_id>', methods=['DELETE'])
def delete_attributes(user_id):
    ###import pdb; pdb.set_trace()
    try: 
            attr = UserAttributes.query.filter_by(userId=user_id).first()
            if attr:
                db.session.delete(attribute)
                db.session.commit()
                return json.dumps(attr.to_dict())
            else:
                return 'User %s not found' %user_id

    except Exception as err:
            #log.error('User could not be found: %', err) 
            if err.code != 200:
                return  'Error :%s' %err.description

