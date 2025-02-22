from maze import app, ADMINS
from flask import Flask, request, session, current_app
from flask.ext.mail import Message, Mail
from models import db, User, UserAttributes, Inbox, ProfConsulted 
import json
from maze.common import auth, confirm_token, errorhandler
from maze.handlers import generate_confirmation_token, send_email
from models import db, User, UserAttributes, Inbox, Conversations, ConversationHasMessages, OneMessage, Appointment
from datetime import timedelta
from maze.professionals.models import Professionals
from flask import Response
import re
from random import randint
import uuid
import stripe 
from flask import render_template

@app.route('/users/payment/<int:user_id>', methods=['POST'])
@errorhandler
def buy(user_id):
    data = request.get_json(force=True)
    stripe_token = data['token']
    profId = data['profId']
    metadata = {'profId' : profId, 'userId' : user_id}
    
    user = User.query.filter_by(userId = user_id).first()
    if not user:    
        return "User invalid", 400
    
    try:
        customer = stripe.Customer.create(
                description="Customer for test@example.com",
                source=stripe_token,
                metadata=metadata,
                email= user.emailId)
    except Exception as e:
        return 'Error charging user: %s' % str(err), 'user_id: %s, data: %s, request.url: %s' \
                    % (user_id, str(data), request.url), 500
  
    response = json.dumps({'customer' : customer.to_dict()['id']})
    # Send email confirmation
    #send_email("Maze Consultation charge for %s %s " % (user.firstName, user.lastName), 
    #            'mazelogging@gmail.com', [user.emailId], 'msg', render_template("send_message.html", my_user = user,
    #            subject="Credit card charged", text='charge'))
    resp = Response(response,
                mimetype="application/json",
                status=200)
    return resp, '', 200

@app.route('/users/payment/<int:user_id>', methods=['GET'])
@errorhandler
def pay_history(user_id):
    try:
        user = User.query.filter_by(userId = user_id).first()
        if not user:    
            return "User invalid", 400

        pay_receive = []
        pay_made = []

        # payment received
        if user.isProfessional:
            appt_details = Appointment.query.filter(Appointment.toUser == user_id).all()
            if appt_details:
                for appt in appt_details:
                   rx_dict = { 'appt_type' : appt.apptType,
                      'paid' : appt.paid,
                      'price' : appt.price,
                      'withUser' : appt.fromUser}
                   with_user = User.query.filter_by(userId= appt.fromUser).first()
                   rx_dict['firstName'] = with_user.firstName
                   rx_dict['lastName'] =  with_user.lastName
                   if appt.isConfirmed:
                        rx_dict['result'] = 'Confirmed'
                        rx_dict['time'] = str(appt.confirmtime)
                   elif appt.isRejected:
                        rx_dict['result'] = 'Rejected'
                        rx_dict['time'] = str(appt.confirmtime)
                   elif appt.isCancelled:
                        rx_dict['result'] = 'Cancelled'
                        rx_dict['time'] = str(appt.confirmtime)
                   elif appt.isRefunded:
                        rx_dict['result'] = 'Refunded'
                        rx_dict['time'] = str(appt.confirmtime)
                   elif appt.isScheduled:
                        rx_dict['result'] = 'Scheduled'
                        rx_dict['time'] = str(appt.starttime1) 
                   else:
                        rx_dict['result'] = 'Complete'
                        rx_dict['time'] = str(appt.confirmtime)
                   pay_receive.append(rx_dict)
            
            conv_details = Conversations.query.filter(Conversations.user2 == user_id).filter(Conversations.systemMessage == False).all()  
            if conv_details:
                for conv in conv_details:
                    rx_dict = { 'appt_type' : 'Message',
                      'paid' : conv.paid,
                      'price' : conv.price,
                      'withUser' : conv.user1,
                      'time' : str(conv.timestamp),
                      'result' : 'Complete'}
                    with_user = User.query.filter_by(userId= conv.user1).first()
                    rx_dict['firstName'] = with_user.firstName
                    rx_dict['lastName'] =  with_user.lastName
                    pay_receive.append(rx_dict)

            prof = Professionals.query.filter_by(userId = user_id).first()
            if not prof:
                return "Professional not found",'user_id: %s, request.url: %s' \
                % (user_id, request.url), 400
            pay_balance = prof.balance


        # payment made
        appt_details = Appointment.query.filter(Appointment.fromUser == user_id).all()
        if appt_details:
            for appt in appt_details:
                tx_dict = { 'appt_type' : appt.apptType,
                      'paid' : appt.paid,
                      'price' : appt.price,
                      'withUser' : appt.toUser}
                with_user = User.query.filter_by(userId= appt.toUser).first()
                tx_dict['firstName'] = with_user.firstName
                tx_dict['lastName'] =  with_user.lastName
                if appt.isConfirmed:
                    tx_dict['result'] = 'Confirmed'
                    tx_dict['time'] = str(appt.confirmtime)
                elif appt.isRejected:
                    tx_dict['result'] = 'Rejected'
                    tx_dict['time'] = str(appt.confirmtime)
                elif appt.isCancelled:
                    tx_dict['result'] = 'Cancelled'
                    tx_dict['time'] = str(appt.confirmtime)
                elif appt.isRefunded:
                    tx_dict['result'] = 'Refunded'
                    tx_dict['time'] = str(appt.confirmtime)
                elif appt.isScheduled:
                    tx_dict['result'] = 'Scheduled'
                    tx_dict['time'] = str(appt.starttime1)
                else:
                    tx_dict['result'] = 'Complete'
                    tx_dict['time'] = str(appt.confirmtime)
                pay_made.append(tx_dict)
          
        conv_details = Conversations.query.filter(Conversations.user1 == user_id).filter(Conversations.systemMessage == False).all()  
        if conv_details:
            for conv in conv_details:
                tx_dict = { 'appt_type' : 'Message',
                      'paid' : conv.paid,
                      'price' : conv.price,
                      'withUser' : conv.user1,
                      'time' : str(conv.timestamp),
                      'result' : 'Complete'}
                with_user = User.query.filter_by(userId= conv.user2).first()
                tx_dict['firstName'] = with_user.firstName
                tx_dict['lastName'] =  with_user.lastName
                pay_made.append(tx_dict)

        data = {'isProfessional' : user.isProfessional, 'pay_receive': pay_receive, 'pay_made':pay_made}
    
        if user.isProfessional:
            data['payBalance'] = pay_balance

        resp = Response(response=json.dumps(data),
                status=200, \
                mimetype="application/json")

        return resp, '', 200
  
    except Exception as err:
        return 'Error getting payment details: %s' % str(err), 'user_id: %s, request.url: %s' \
                % (user_id, request.url), 400


@app.route('/users/price/<int:user_id>/<int:prof_id>/<appt_type>', methods=['GET'])
@errorhandler
def get_price(user_id, prof_id, appt_type):
    try:
        user = User.query.filter_by(userId = user_id).first()
        if not user:    
            return "User invalid",'user_id: %s, request.url: %s' \
                % (user_id, request.url), 400

        prof = Professionals.query.filter_by(userId = prof_id).first()
        if not prof:    
            return "Professional invalid", 'user_id: %s, request.url: %s' \
                % (user_id, request.url), 400
        
        discount = None
        if prof.firstFree:
            profconsulted = ProfConsulted.query.filter_by(userid = user_id).filter_by(profid = prof_id).first()
            if not profconsulted:
                # apply discount
                discount = 'First Free'
        
        if appt_type == 'message':
            price =  prof.questionRate
        elif appt_type == 'voice':
            price =  prof.voiceRate
        elif appt_type == 'video':
            price = prof.videoRate
        else:
            return "Appt type invalid", 'user_id: %s, request.url: %s' % (user_id, request.url), 400
            
        # Final price
        if discount:
            final_price = 0
        else:
            final_price = price

        response = {'price':price, 'discount':discount, 'final_price':final_price}

        resp = Response(response=json.dumps(response),
                status=200, \
                mimetype="application/json")

        return resp, '', 200


    except Exception as err:
        return 'Error getting price details: %s' % str(err), 'user_id: %s, request.url: %s' \
                % (user_id, request.url), 400
