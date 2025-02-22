from flask import Flask

from redis import Redis
import json
from flask import make_response, request, current_app
from flask import Response
#from flask.ext.redis import Redis

import logging

app = Flask(__name__)
 
# REDIS
redisnotify = Redis(host='127.0.0.1', port=6379, db = 1)
#redisappoint = Redis(host='127.0.0.1', port=6379, db = 2)
#redisapptsched = Redis(host='127.0.0.1', port=6379, db = 3)

#logging.basicConfig(filename='/var/log/maze.log', level=logging.DEBUG)
#log = logging.getLogger('maze')
@app.route('/notify/<int:user_id>', methods=['GET'])
def notify_inbox(user_id):
    #import pdb; pdb.set_trace()
    email_notif = redisnotify.get(user_id)
    if not email_notif:
        email_notif = 0
    
    #req_notif = redisappoint.get(user_id)
    #if not req_notif:
    #    req_notif = 0

    #confirm_notif = redisapptsched.get(user_id)
    #if not confirm_notif:
    #    confirm_notif = 0
    
    data = json.dumps({'inboxNotif': email_notif})
    #, 'requestedAppoint': req_notif, 'confirmedAppoint': confirm_notif})
    resp = Response(data,
                status=200)
    return resp

if __name__ == '__main__':                                                                                        
    app.run(
            host="0.0.0.0",
            port=int("5500"), 
            debug=True)
