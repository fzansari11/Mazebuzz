from maze import app 
import os
# We'll render HTML templates and access data sent by POST
# using the request object from flask. Redirect and url_for
# will be used to redirect the user once the upload is done
# and send_from_directory will help us to send/show on the
# browser the file that the user just uploaded
from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from werkzeug import secure_filename
import json
from flask import Response
from urlparse import urlparse
from models import db, User
from maze.professionals.models import Credentials
import datetime
from maze.common import errorhandler

#from flask.ext.storage import get_default_storage_class
#from flask.ext.uploads import delete, init, save, Upload

# For a given file, return whether it's an allowed type or not
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in app.config['ALLOWED_EXTENSIONS']

# Route that will process the default pic upload
@app.route('/upload/<int:user_id>', methods=['POST'])
@errorhandler
def upload(user_id):
    ###import pdb; pdb.set_trace()
    # Get the name of the uploaded file
    try:
        file1 = request.files['files']

        # Check if the file is one of the allowed types/extensions
        if file1 and allowed_file(file1.filename):
            # Make the filename safe, remove unsupported chars
            filename1 = secure_filename(file1.filename)
            filename = "defaultprofilepic.png"

 ####### This code block will be replaced by a distributed fileserver like Amazon S3 ############
            file_dir = os.path.join(app.config['UPLOAD_FOLDER'], str(user_id))
            if not os.path.exists(file_dir):
                os.makedirs(file_dir)
            ret = file1.save(os.path.join(file_dir, filename))

            # Create url to save the uploaded file
            url_path = app.config['FILE_URL_PATH'] + str(user_id) + '/' + filename
            hostname = app.config['FILE_SERVER']
            new_url = hostname + url_path
####### A new url will be returned by amazon S3 which will be stored in user DB ##############

            user = User.query.filter_by(userId = user_id).first()
            user.profilePicture = new_url
            db.session.commit()

            data = json.dumps({'fileUrl':new_url})
            resp = Response(response=data,
                    status=200, \
                    mimetype="application/json")
            return resp, '', 200
    except Exception as err:
        return "Error uploading photo : %s" % str(err), 'user_id: %s, request.url: %s' \
                    % (user_id, request.url), 500

# Route that will process the portfolio pics upload
@app.route('/upload/portimages/<int:user_id>', methods=['POST'])
@errorhandler
def uploadport(user_id):
    ###import pdb; pdb.set_trace()
    # Get the name of the uploaded file
    file1 = request.files['files']
    # Check if the file is one of the allowed types/extensions
    if file1 and allowed_file(file1.filename.lower()):
        # Make the filename safe, remove unsupported chars
        filename = secure_filename(file1.filename)
        filename = datetime.datetime.now().strftime('%Y_%m_%d_%H_%M_%S') + '_' + filename

 ####### This code block will be replaced by a distributed fileserver like Amazon S3 ############
        file_dir = os.path.join(app.config['UPLOAD_FOLDER'], str(user_id))
        if not os.path.exists(file_dir):
            os.makedirs(file_dir)
        ret = file1.save(os.path.join(file_dir, filename))

        # Create url to save the uploaded file
        url_path = app.config['FILE_URL_PATH'] + str(user_id) + '/' + filename
        hostname = app.config['FILE_SERVER']
        new_url = hostname + url_path
####### A new url will be returned by amazon S3 which will be stored in user DB ##############

        user = Credentials.query.filter_by(userId = user_id).first()
        if not user:
            return "User not found", 'user_id: %s, data: %s, request.url: %s' \
                    % (user_id, str(data), request.url), 400
        images = user.images
        if images:
            images_list = images.split(',')
            images_list.append(new_url)
            subp = (',').join(images_list)
            user.update({"images":subp})
        else:
            user.update({"images":new_url})
        db.session.commit()

        data = json.dumps({'fileUrl':new_url})
        resp = Response(response=data,
                status=200, \
                mimetype="application/json")
        return resp, '', 200


# Route that will process the attachments upload
@app.route('/upload/attach/<int:user_id>', methods=['POST'])
@errorhandler
def upload_files(user_id):
    # Get the name of the uploaded file
    try:
        file1 = request.files['files']

        # Check if the file is one of the allowed types/extensions
        if file1:
            # Make the filename safe, remove unsupported chars
            filename = secure_filename(file1.filename)
            filename = datetime.datetime.now().strftime('%Y_%m_%d_%H_%M_%S') + '_' + filename

 ####### This code block will be replaced by a distributed fileserver like Amazon S3 ############
            file_dir = os.path.join(app.config['UPLOAD_FOLDER'], str(user_id))
            if not os.path.exists(file_dir):
                os.makedirs(file_dir)
            ret = file1.save(os.path.join(file_dir, filename))

            # Create url to save the uploaded file
            url_path = app.config['FILE_URL_PATH'] + str(user_id) + '/' + filename
            hostname = app.config['FILE_SERVER']
            new_url = hostname + url_path
####### A new url will be returned by amazon S3 which will be stored in user DB ##############

            data = json.dumps({'fileUrl':new_url})
            resp = Response(response=data,
                    status=200, \
                    mimetype="application/json")
            return resp, '', 200
    except Exception as err:
        return "Error uploading photo : %s" % str(err), 'user_id: %s, request.url: %s' \
                    % (user_id, request.url), 400


# Route that will process the file delete
@app.route('/upload/portimages/<int:user_id>', methods=['DELETE'])
@errorhandler
def deleteportimage(user_id):
    ###import pdb; pdb.set_trace()
    data = request.get_json(force=True)
    try:
        new_url = data['fileUrl']  
        user = Credentials.query.filter_by(userId = user_id).first()
        images = user.images
        if images:
            images_list = images.split(',')
            if new_url in images_list:
                images_list.remove(new_url)
                subp = (',').join(images_list)
                user.update({"images":subp})
                db.session.commit()
            else:
                return "File not found", 'user_id: %s, data: %s, request.url: %s' \
                    % (user_id, str(data), request.url), 400

        resp = Response(response=json.dumps({"ImageDelete":"Success"}),
                    status=200, \
                    mimetype="application/json")

        return resp, '', 200
    except Exception as err:
        return "Error deleting image %s" % str(err), 'user_id: %s, data: %s, request.url: %s' \
                    % (user_id, str(data), request.url), 500




# This route is expecting a parameter containing the name
# of a file. Then it will locate that file on the upload
# directory and show it on the browser, so if the user uploads
# an image, that image is going to be shown after the upload
@app.route('/upload/<filename>', methods=['GET'])
@app.route('/upload/<int:user_id>/<filename>', methods=['GET'])
def uploaded_file(filename, user_id=0):
    ###import pdb; pdb.set_trace()
    if user_id:
        file_dir = os.path.join(app.config['UPLOAD_FOLDER'], str(user_id))
    else:    
        file_dir = os.path.join(app.config['UPLOAD_FOLDER'])

    return send_from_directory(file_dir,
                               filename)

'''
@app.route('/uploadphoto/<int:user_id>', methods=['GET', 'POST'])
@errorhandler
def upload_photo(user_id):
    ###import pdb; pdb.set_trace()
    if request.method == 'POST' and 'photo' in request.files:
        filename = photos.save(request.files['photo'])
        rec = Photo(filename=filename, user=g.user.id)
        rec.store()
        flash("Photo saved.")
        return redirect(url_for('show', id=rec.id))
    return "Success", '' , 200

@app.route('/photo/<id>')
def show(id):
    ###import pdb; pdb.set_trace()
    photo = Photo.load(id)
    if photo is None:
        abort(404)
    url = photos.url(photo.filename)
    return url


@app.route('/uploadall')
def index():
    ###import pdb; pdb.set_trace()
    """List the uploads."""
    uploads = Upload.query.all()
    for u in uploads:
        a = Storage().url(u.name)
        b = u.name
        c = u.id
    return True
'''
