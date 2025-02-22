from maze import app
from flask import Flask, render_template, request, flash, session, redirect, url_for, jsonify
from flask.ext.mail import Message, Mail
from models import db, User, Inbox 
import json

@app.route('/inbox', methods=['POST'])
def create_inbox():
    ###import pdb; pdb.set_trace()
    data = request.get_json(force=True)
    try: 
        newinbox = Inbox (data['userId'],
                    data['totalMessages'])
    
        db.session.add(newinbox)
        db.session.commit()
        inbox = Inbox.query.filter_by(userId=data['userId']).first()

        # Add user entry to attribute and Inbox table

    except Exception as err:
            #log.error('User %s could not be created: %' %(data[userid], err))  
            return 'Error creating inbox: %s' %err
    return json.dumps(inbox.to_dict()) 


@app.route('/inbox/<int:inbox_id>', methods=['GET'])
def show_inbox(inbox_id):
    ###import pdb; pdb.set_trace()
    try: 
            inbox = Inbox.query.filter_by(userId=user_id).first()
            if inbox:
                return json.dumps(inbox.to_dict())
            else:
                return 'Inbox %s not found' %inbox_id

    except Exception as err:
            #log.error('inbox could not be found: %', err) 
            if err.code != 200:
                return  'Error :%s' %err.description


@app.route('/inboxs/<int:user_id>', methods=['PUT'])
def update_inbox(user_id):
    ###import pdb; pdb.set_trace()
    data = request.get_json(force=True)
    try: 
            inbox = Inbox.query.filter_by(userId=user_id).first()
            if inbox:
                inbox.update(data)
                db.session.commit()
                return json.dumps(inbox.to_dict())
            else:
                return 'inbox %s not found' %inbox_id

    except Exception as err:
            #log.error('inbox could not be found: %', err) 
            if err.code != 200:
                return  'Error :%s' %err.description


@app.route('/inboxs/<int:inbox_id>', methods=['DELETE'])
def delete_inbox(user_id):
    ###import pdb; pdb.set_trace()
    try: 
            inbox = Inbox.query.filter_by(userId=user_id).first()
            if inbox:
                db.session.delete(inbox)
                db.session.commit()
                return json.dumps(inbox.to_dict())
            else:
                return 'inbox %s not found' %user_id

    except Exception as err:
            #log.error('inbox could not be found: %', err) 
            if err.code != 200:
                return  'Error :%s' %err.description

