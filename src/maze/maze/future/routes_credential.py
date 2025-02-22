from maze import app
from flask import Flask, render_template, request, flash, session, redirect, url_for, jsonify
from flask.ext.mail import Message, Mail
from models import db, Profession, Professionals, Credentials 
import json


@app.route('/credentials', methods=['POST'])
def create_credentials():
    ###import pdb; pdb.set_trace()
    data = request.get_json(force=True)
    try: 
        newcred = Credentials (data['credentialId'],
                    data['backgroundCheck'],
                    data['businessCheck'],
                    data['businessNameimage'],
                    data['employerNameimage'],
                    data['schoolAttended'],
                    data['highestDegree'],
                    data['degreeSubject'],
                    data['addtionalInfo'])
    
        db.session.add(newcred)
        db.session.commit()
        cred = credentials.query.filter_by(credentialsId=data['credentialsId']).first()

    except Exception as err:
            #log.error('User %s could not be created: %' %(data[userid], err))  
            return 'Error creating user: %s' %err
    return json.dumps(cred.to_dict()) 

@app.route('/credentials/<int:credentials_id>', methods=['GET'])
def get_credentials(credentials_id):
    ###import pdb; pdb.set_trace()
    try: 
            port = Credentials.query.filter_by(credentialsId=credentials_id).first()
            if port:
                return json.dumps(port.to_dict())
            else:
                return 'User %s not found' %user_id

    except Exception as err:
            #log.error('User could not be found: %', err) 
            if err.code != 200:
                return  'Error :%s' %err.description


@app.route('/credentials/<int:credentials_id>', methods=['PUT'])
def update_credentials(credentials_id):
    ###import pdb; pdb.set_trace()
    data = request.get_json(force=True)
    try: 
            port = Credentials.query.filter_by(credentialsId=credentials_id).first()
            if port:
                port.update(data)
                db.session.commit()
                return json.dumps(port.to_dict())
            else:
                return 'User %s not found' %credentials_id

    except Exception as err:
            #log.error('User could not be found: %', err) 
            if err.code != 200:
                return  'Error :%s' %err.description


@app.route('/credentials/<int:credentials_id>', methods=['DELETE'])
def delete_credentials(credentials_id):
    ###import pdb; pdb.set_trace()
    try: 
            port = Credentials.query.filter_by(credentialsId=credentials_id).first()
            if port:
                db.session.delete(port)
                db.session.commit()
                return json.dumps(port.to_dict())
            else:
                return 'User %s not found' %credentials_id

    except Exception as err:
            #log.error('User could not be found: %', err) 
            if err.code != 200:
                return  'Error :%s' %err.description

