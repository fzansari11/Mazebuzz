from maze import app
from models import db, User, Reviews, ProfConsulted
import json
from flask import Response, request
from sqlalchemy import desc
from maze.professionals.models import db, ProfessionalRatings
from maze.common import errorhandler

# Write a review
@app.route('/users/reviews/<int:user_id>', methods=['POST'])
@errorhandler
#@auth.login_required
def add_review(user_id):
    ###import pdb; pdb.set_trace()
    data = request.get_json(force=True)

    try: 
        # Make sure receiving user is valid.
        user1 = data['fromUser']
        user2 = data['toUser']
        user = User.query.filter_by(userId = user2).first()
        if not user:
            return "User invalid for review", 'user_id: %s, data: %s, request.url: %s' \
                    % (user_id, str(data), request.url), 400

        # Check if Review already exists
        review = Reviews.query.filter_by(fromUser = user1).filter_by(toUser = user2).first()
        if review:
            review.reviewTitle =  data['reviewTitle'].capitalize()
            review.stars = data['stars']
            review.reviewText = data['reviewText']
        else:
            # Create new review
            review = Reviews (user1, user2, data['reviewTitle'].capitalize(), data['stars'], data['reviewText'])
        db.session.add(review)

        # Update professionals average rating
        user = ProfessionalRatings.query.filter_by(userId=user2).first()
        if not user:
            return "Professionals reviews not found", 'user_id: %s, data: %s, request.url: %s' \
                    % (user_id, str(data), request.url), 400
        if data['stars'] == '1':
            user.increment('num1star')
        if data['stars'] == '2':
            user.increment('num2star')
        if data['stars'] == '3':
            user.increment('num3star')
        if data['stars'] == '4':
            user.increment('num4star')
        if data['stars'] == '5':
            user.increment('num5star')
        user.increment('totalReviews')

        # make prof consulted False
        cons = ProfConsulted.query.filter_by(userid = user1). \
                    filter_by(profid=user2).first()
        if not cons:
            return "Cannot add review without taking consultation",'user_id: %s, data: %s, request.url: %s' \
                    % (user_id, str(data), request.url), 400
 
        cons.reviewed = True
        db.session.commit()

        user = ProfessionalRatings.query.filter_by(userId=user2).first()

        avgRating = (user.num1star*1 + user.num2star*2 + user.num3star*3
                     +  user.num4star*4 + user.num5star*5 ) / (user.num1star + user.num2star + user.num3star
                     +  user.num4star + user.num5star)
        user.update({'avgRating':avgRating})
        db.session.commit()
        data = json.dumps({'Review': "Review added"})
        resp = Response(response=data,
                status=200,
                mimetype="application/json")

        return resp, '' , 200

    except Exception as err:
        #log.error('User %s could not be created: %' %(data[userid], err))  
        return 'Error creating review: %s' %str(err),  'user_id: %s, data: %s, request.url: %s' \
                    % (user_id, str(data), request.url), 500

# Get all reviews for user
@app.route('/users/reviews/<int:user_id>', methods=['GET'])
#@auth.login_required
@errorhandler
def get_reviews(user_id):
    ###import pdb; pdb.set_trace()
    try: 
        review_details = Reviews.query.filter_by(toUser = user_id).order_by(desc(Reviews.timeOfReview)).all()
        
        final_list = []
        for review in review_details:
            new_review = review.to_dict()
            user = User.query.filter_by(userId= new_review['fromUser']).first()
            new_review['firstName'] = user.firstName
            new_review['lastName'] =  user.lastName
            new_review['timeOfReview'] = str(new_review['timeOfReview'])
            final_list.append(new_review)

        data = json.dumps({'Reviews': final_list})

        resp = Response(response=data,
                status=200, \
                mimetype="application/json")

        return resp, '', 200
  
    except Exception as err:
        #log.error('User %s could not be created: %' %(data[userid], err))  
        return 'Error retreiving reviews : %s' %str(err), 'user_id: %s, data: %s, request.url: %s' \
                    % (user_id, str(data), request.url), 500

