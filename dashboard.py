import hashlib
import json
from random import randint

import rethinkdb as r
from flask import render_template, request, Blueprint, url_for, session, redirect

from utils.db import get_db
from utils.make_session import make_session

config = json.load(open('config.json'))

dash = Blueprint('dashboard', __name__, template_folder='views', static_folder='views/assets')

API_BASE_URL = 'https://discordapp.com/api'
AUTHORIZATION_BASE_URL = API_BASE_URL + '/oauth2/authorize'
TOKEN_URL = API_BASE_URL + '/oauth2/token'


def limited_access(func):
    def wrapper(*args, **kwargs):
        if 'user' not in session:
            discord = make_session(token=session.get('oauth2_token'))
            user = discord.get(API_BASE_URL + '/users/@me').json()

            if 'id' not in user:
                return redirect(url_for('.login'))

            session['user'] = user  # TODO: Expiry

        return func(*args, **kwargs)

    wrapper.__name__ = func.__name__
    return wrapper


@dash.route('/login')
def login():
    discord = make_session(scope='identify email', redirect_uri=request.host_url + 'callback')
    authorization_url, state = discord.authorization_url(AUTHORIZATION_BASE_URL)
    return redirect(authorization_url)


@dash.route('/logout')
def logout():
    session.clear()
    return redirect(request.host_url)


@dash.route('/callback')
def callback():
    if request.values.get('error'):
        return request.values['error']

    discord = make_session(state=session.get('oauth2_state'), redirect_uri=request.host_url + 'callback')
    token = discord.fetch_token(
        TOKEN_URL,
        client_secret=config['client_secret'],
        authorization_response=request.url)
    session['oauth2_token'] = token
    return redirect(url_for('.dashboard'))


@dash.route('/dashboard')
@limited_access
def dashboard():
    user = session['user']
    is_admin = user['id'] in config['admins']
    keys = get_db().table('keys', filter=(r.row['owner'] == user['id']))
    return render_template('dashboard.html', name=user['username'], keys=keys, admin=is_admin)


@dash.route('/request', methods=['GET', 'POST'])
@limited_access
def request_key():
    user = session['user']

    if request.method == 'GET':
        return render_template('request.html')

    elif request.method == 'POST':
        name = request.form.get('name', None)
        reason = request.form.get('reason', None)

        if not reason or not name:
            result = 'Please enter a name and reason for your application'
            return render_template('result.html', result=result, success=False)

        get_db().insert('applications', {
            "owner": user['id'],
            "email": user['email'],
            "name": name,
            "owner_name": f'{user["username"]}#{user["discriminator"]}',
            "reason": reason
        })
        result = 'Application Submitted 👌'
        return render_template('result.html', result=result, success=True)


@dash.route('/createkey', methods=['GET', 'POST'])
@limited_access
def create_key():
    user = session['user']

    if user['id'] not in config['admins']:
        return render_template('gitout.html')

    if request.method == 'GET':
        return render_template('create.html')
    elif request.method == 'POST':
        name = request.form.get('name', None)
        token = request.form.get('token', None)
        owner = request.form.get('owner', None)
        owner_name = request.form.get('owner_name', None)
        email = request.form.get('email', None)

        if not token or not name or not owner or not owner_name or not email:
            result = 'Please fill in all required inputs'
            return render_template('result.html', result=result, success=False)

        get_db().insert('keys', {
            "id": token,
            "name": name,
            "owner": owner,
            "owner_name": owner_name,
            "email": email,
            "total_usage": 0,
            "usages": {},
            "unlimited": False,
            "ratelimit_reached": 0
        })
        result = 'Key Created 👌'
        return render_template('result.html', result=result, success=True)


@dash.route('/admin')
@limited_access
def admin():
    user = session['user']

    if user['id'] not in config['admins']:
        return render_template('gitout.html')

    apps = get_db().table('applications')
    keys = get_db().table('keys')
    return render_template('admin.html', name=user['username'], apps=apps, keys=keys)


@dash.route('/approve/<key_id>')
@limited_access
def approve(key_id):
    user = session['user']

    if user['id'] not in config['admins']:
        return render_template('gitout.html')

    key = get_db().get('applications', key_id)
    if 'id' not in key:
        key['id'] = key['_id']

    m = hashlib.sha256()
    m.update(str(key['id']).encode())
    m.update(str(randint(10000, 99999)).encode())
    token = m.hexdigest()
    get_db().insert('keys', {
        "id": token,
        "name": key['name'],
        "owner": key['owner'],
        "owner_name": key['owner_name'],
        "email": key['email'],
        "total_usage": 0,
        "usages": {},
        "unlimited": False,
        "ratelimit_reached": 0
    })
    get_db().delete('applications', key_id)
    return redirect(url_for('.admin'))


@dash.route('/decline/<key_id>')
@limited_access
def decline(key_id):
    user = session['user']

    if user['id'] not in config['admins']:
        return render_template('gitout.html')

    get_db().delete('applications', key_id)
    return redirect(url_for('.admin'))


@dash.route('/delete/<key_id>')
@limited_access
def delete(key_id):
    user = session['user']

    if user['id'] not in config['admins']:
        return render_template('gitout.html')
    get_db().delete('keys', key_id)
    return redirect(url_for('.admin'))


@dash.route('/unlimited/<key_id>')
@limited_access
def unlimited(key_id):
    user = session['user']

    if user['id'] not in config['admins']:
        return render_template('gitout.html')

    key = get_db().get('keys', key_id)
    unlimited = not key['unlimited']
    get_db().update('keys', key_id, {'unlimited': unlimited})
    return redirect(url_for('.admin'))
