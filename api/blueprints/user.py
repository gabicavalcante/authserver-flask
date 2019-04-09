# coding: utf-8
import os
import logging
from bson import ObjectId 
from flask import (
    Blueprint, request, current_app, send_from_directory, jsonify, session
) 
from ..models import User 
from ..annotations.auth import login_required, roles_accepted, make_login
from flasgger import swag_from 
from ..utils.token import validate_token, create_token


logger = logging.getLogger(__name__)
user_blueprint = Blueprint('user', __name__, url_prefix="/api")
 
@user_blueprint.route("/users", methods=["GET"]) 
@login_required
@roles_accepted('read')
def get_users():
    users = User.objects.all()
    return jsonify({'users': users}), 200

@user_blueprint.route("/user/<username>", methods=["GET"])  
@login_required
@roles_accepted('read')
def get_user(username):
    if not User.objects(username=username):
        return jsonify({'error': "user doesn't exist"}), 400

    user = User.objects.get(username=username)  
    return jsonify({'username': user}), 400

@user_blueprint.route("/user/<username>", methods=["DELETE"])  
@login_required
@roles_accepted('delete')
def delete_user(username): 
    if not User.objects(username=username):
        return jsonify({'error': "user doesn't exist"}), 400

    user = User.objects.get(username=username).delete()
    return jsonify({'username': username}), 400

@user_blueprint.route("/user", methods=["POST"])    
def create_user():  
    content = request.json
    username = content.get('username')
    email = content.get('email')
    password = content.get('password')
    permissions = content.get('permissions')
     
    if username is None or password is None or email is None:
        return jsonify({'error': "missing arguments"}), 400
 
    if User.objects(username=username):
        return jsonify({'error': "user {} already exists".format(username)}), 400

    user = User(username=username, email=email, password=password, permissions=permissions)
    user.hash_password(password)
    user.save()

    return jsonify({'username': username}), 201


@user_blueprint.route("/login", methods=["POST"]) 
def login():  
    username = request.form.get("username")
    password = request.form.get("password")

    result = make_login(username, password)
    if not result:
        return jsonify({'WWW-Authenticate': 'Basic realm=Login Required'}), 401
    
    resp = jsonify({"message": "User authenticated"})
    resp.status_code = 200
    resp.headers.extend({'token': result})
    return resp

@user_blueprint.route('/logout', methods=["POST"])
def logout():
    # remove the username from the session if it's there
    session.pop('username', None)
    session.pop('token', None)
    return jsonify({'logout': True}), 201

@user_blueprint.route('/token/refresh', methods=["POST"]) 
def token_refresh():
    # remove the username from the session if it's there
    if session.get('username'):
        data_token = request.headers.get('Authorization')
        token = str(data_token['key'])
        if validate_token(token, session['token']):
            return token
        else:
            token = create_token(session.get('username')) 
            return token

    return jsonify({'logout': True}), 201