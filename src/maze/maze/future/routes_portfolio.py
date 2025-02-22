from maze import app
from flask import Flask, render_template, request, flash, session, redirect, url_for, jsonify
from flask.ext.mail import Message, Mail
from models import db, Profession, Professionals, Portfolio 
import json


@app.route('/portfolio', methods=['POST'])
def create_portfolio():
    ###import pdb; pdb.set_trace()
    data = request.get_json(force=True)
    try: 
        newport = Portfolio (data['portfolioId'],
                    data['aboutMe'],
                    data['websiteUrl'],
                    data['imageUrl1'],
                    data['imageUrl2'],
                    data['imageUrl3'],
                    data['imageUrl4'],
                    data['imageUrl5'],
                    data['videoUrl'],
                    data['linkedinUrl'])
    
        db.session.add(newport)
        db.session.commit()
        port = Portfolio.query.filter_by(portfolioId=data['portfolioId']).first()

    except Exception as err:
            #log.error('User %s could not be created: %' %(data[userid], err))  
            return 'Error creating user: %s' %err
    return json.dumps(port.to_dict()) 

@app.route('/portfolio/<int:portfolio_id>', methods=['GET'])
def get_portfolio(portfolio_id):
    ###import pdb; pdb.set_trace()
    try: 
            port = Portfolio.query.filter_by(portfolioId=portfolio_id).first()
            if port:
                return json.dumps(port.to_dict())
            else:
                return 'User %s not found' %user_id

    except Exception as err:
            #log.error('User could not be found: %', err) 
            if err.code != 200:
                return  'Error :%s' %err.description


@app.route('/portfolio/<int:portfolio_id>', methods=['PUT'])
def update_portfolio(portfolio_id):
    ###import pdb; pdb.set_trace()
    data = request.get_json(force=True)
    try: 
            port = Portfolio.query.filter_by(portfolioId=portfolio_id).first()
            if port:
                port.update(data)
                db.session.commit()
                return json.dumps(port.to_dict())
            else:
                return 'User %s not found' %portfolio_id

    except Exception as err:
            #log.error('User could not be found: %', err) 
            if err.code != 200:
                return  'Error :%s' %err.description


@app.route('/portfolio/<int:portfolio_id>', methods=['DELETE'])
def delete_portfolio(portfolio_id):
    ###import pdb; pdb.set_trace()
    try: 
            port = Portfolio.query.filter_by(portfolioId=portfolio_id).first()
            if port:
                db.session.delete(port)
                db.session.commit()
                return json.dumps(port.to_dict())
            else:
                return 'User %s not found' %portfolio_id

    except Exception as err:
            #log.error('User could not be found: %', err) 
            if err.code != 200:
                return  'Error :%s' %err.description

