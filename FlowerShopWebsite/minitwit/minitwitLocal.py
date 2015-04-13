# -*- coding: utf-8 -*-
"""
    MiniTwit
    ~~~~~~~~

    A microblogging application written with Flask and sqlite3.

    :copyright: (c) 2010 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""

import time
from sqlite3 import dbapi2 as sqlite3
from hashlib import md5
from datetime import datetime
from flask import Flask, request, session, url_for, redirect, \
     render_template, abort, g, flash, _app_ctx_stack
from werkzeug import check_password_hash, generate_password_hash
import requests
import json

# configuration
DATABASE = 'minitwit.db'
PER_PAGE = 30
DEBUG = True
SECRET_KEY = 'development key'

#FOURSQUARE OAUTH2
FOURSQUARE_CLIENT_ID = 'XN05NEDOBMXOTMERCBNQDAK1HTKZELS2WYOIRMQ2WY0KT5O2'
FOURSQUARE_CLIENT_SECRET = '0OXMRBNZURZKGOEBT0VM2WNAVAKMDKC2AZTMHZCZGLQA2BZ4'
FOURSQUARE_REDIRECT_URI = "https://127.0.0.1:5000/authenticated"
FOURSQUARE_API_BASE = "https://api.foursquare.com/v2/"

# create our little application :)
app = Flask(__name__)
app.config.from_object(__name__)
app.config.from_envvar('MINITWIT_SETTINGS', silent=True)


def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    top = _app_ctx_stack.top
    if not hasattr(top, 'sqlite_db'):
        top.sqlite_db = sqlite3.connect(app.config['DATABASE'])
        top.sqlite_db.row_factory = sqlite3.Row
    return top.sqlite_db


@app.teardown_appcontext
def close_database(exception):
    """Closes the database again at the end of the request."""
    top = _app_ctx_stack.top
    if hasattr(top, 'sqlite_db'):
        top.sqlite_db.close()


def init_db():
    """Creates the database tables."""
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            try:
                db.cursor().executescript(f.read())
            except sqlite3.OperationalError, msg:
                print msg
        db.commit()


def query_db(query, args=(), one=False):
    """Queries the database and returns a list of dictionaries."""
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    return (rv[0] if rv else None) if one else rv


def get_user_id(username):
    """Convenience method to look up the id for a username."""
    rv = query_db('select user_id from user where username = ?',
                  [username], one=True)
    return rv[0] if rv else None


def format_datetime(timestamp):
    """Format a timestamp for display."""
    return datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d @ %H:%M')


def gravatar_url(email, size=80):
    """Return the gravatar image for the given email address."""
    return 'http://www.gravatar.com/avatar/%s?d=identicon&s=%d' % \
        (md5(email.strip().lower().encode('utf-8')).hexdigest(), size)


@app.before_request
def before_request():
    g.user = None
    if 'user_id' in session:
        g.user = query_db('select * from user where user_id = ?',
                          [session['user_id']], one=True)

@app.route('/authenticated')
def authenticated():
	db = get_db()
	CODE = request.args.get('code', '')
	response = requests.get("https://foursquare.com/oauth2/access_token?client_id=" + FOURSQUARE_CLIENT_ID
		+ "&client_secret=" + FOURSQUARE_CLIENT_SECRET + "&grant_type=authorization_code&redirect_uri="
		+ FOURSQUARE_REDIRECT_URI +"&code=" + CODE + "&sort=newestfirst")
	dict = json.loads(response.text)
	db.execute('insert into access_token (user_id, access_token_text) values (?, ?)', 
		[session['user_id'], dict['access_token']])
	db.commit()
	return redirect(url_for('foursquare'), code=302)

@app.route('/foursquare')
def foursquare():
	"""Shows your foursquare info. Or, if you have not authorized this app to connect to 
	foursquare, then it will redirect you to foursquare.
	"""
	if not g.user:
		return redirect(url_for('public_timeline'))
	result = query_db('select access_token_text from access_token where user_id = ?',
                          [session['user_id']], one=True)
	if not result:
		return redirect("https://foursquare.com/oauth2/authenticate?response_type=code&client_id=" + FOURSQUARE_CLIENT_ID + "&redirect_uri=" + FOURSQUARE_REDIRECT_URI,code=302)
	else:
		#Get info from foursquare
		token = result['access_token_text']
		response = requests.get(FOURSQUARE_API_BASE + "users/self/checkins?oauth_token=" + token + 
			"&v=20150326&m=foursquare")
		dict = json.loads(response.text)
		list = dict['response']['checkins']['items']
		return render_template('foursquare.html', listOfCheckins=list)
	
@app.route('/')
def timeline():
	"""Shows a users timeline or if no user is logged in it will
	redirect to the public timeline.  This timeline shows the user's
	messages as well as all the messages of followed users.
	"""
	if not g.user:
		return redirect(url_for('public_timeline'))
	#Get info from foursquare
	result = query_db('select access_token_text from access_token where user_id = ?',
                          [session['user_id']], one=True)
	if result:    
		token = result['access_token_text']
		response = requests.get(FOURSQUARE_API_BASE + "users/self/checkins?oauth_token=" + token + 
			"&v=20150326&m=foursquare")
		dict = json.loads(response.text)
		item = dict['response']['checkins']['items'][0]
		return render_template('timeline.html',messages=query_db('''
			select message.*, user.* from message, user
			where message.author_id = user.user_id and (
				user.user_id = ? or
				user.user_id in (select whom_id from follower
										where who_id = ?))
			order by message.pub_date desc limit ?''',
			[session['user_id'], session['user_id'], PER_PAGE]),checkin=item)
	return render_template('timeline.html',messages=query_db('''
			select message.*, user.* from message, user
			where message.author_id = user.user_id and (
				user.user_id = ? or
				user.user_id in (select whom_id from follower
										where who_id = ?))
			order by message.pub_date desc limit ?''',
			[session['user_id'], session['user_id'], PER_PAGE]),checkin=None)


@app.route('/public')
def public_timeline():
    """Displays the latest messages of all users."""
    return render_template('timeline.html', messages=query_db('''
        select message.*, user.* from message, user
        where message.author_id = user.user_id
        order by message.pub_date desc limit ?''', [PER_PAGE]))


@app.route('/<username>')
def user_timeline(username):
	"""Display's a users tweets."""
	profile_user = query_db('select * from user where username = ?',
                            [username], one=True)
	if profile_user is None:
		abort(404)
	followed = False
	if g.user:
		followed = query_db('''select 1 from follower where
            follower.who_id = ? and follower.whom_id = ?''',
            [session['user_id'], profile_user['user_id']],
            one=True) is not None
            
	#Get info from foursquare
	result = query_db('select access_token_text from access_token where user_id = ?',
                          [profile_user['user_id']], one=True)
	if result:    
		token = result['access_token_text']
		response = requests.get(FOURSQUARE_API_BASE + "users/self/checkins?oauth_token=" + token + 
			"&v=20150326&m=foursquare")
		dict = json.loads(response.text)
		item = dict['response']['checkins']['items'][0]

	return render_template('timeline.html', messages=query_db('''
            select message.*, user.* from message, user where
            user.user_id = message.author_id and user.user_id = ?
            order by message.pub_date desc limit ?''',
            [profile_user['user_id'], PER_PAGE]), followed=followed,
            profile_user=profile_user, checkin=item)


@app.route('/<username>/follow')
def follow_user(username):
    """Adds the current user as follower of the given user."""
    if not g.user:
        abort(401)
    whom_id = get_user_id(username)
    if whom_id is None:
        abort(404)
    db = get_db()
    db.execute('insert into follower (who_id, whom_id) values (?, ?)',
              [session['user_id'], whom_id])
    db.commit()
    flash('You are now following "%s"' % username)
    return redirect(url_for('user_timeline', username=username))


@app.route('/<username>/unfollow')
def unfollow_user(username):
    """Removes the current user as follower of the given user."""
    if not g.user:
        abort(401)
    whom_id = get_user_id(username)
    if whom_id is None:
        abort(404)
    db = get_db()
    db.execute('delete from follower where who_id=? and whom_id=?',
              [session['user_id'], whom_id])
    db.commit()
    flash('You are no longer following "%s"' % username)
    return redirect(url_for('user_timeline', username=username))


@app.route('/add_message', methods=['POST'])
def add_message():
    """Registers a new message for the user."""
    if 'user_id' not in session:
        abort(401)
    if request.form['text']:
        db = get_db()
        db.execute('''insert into message (author_id, text, pub_date)
          values (?, ?, ?)''', (session['user_id'], request.form['text'],
                                int(time.time())))
        db.commit()
        flash('Your message was recorded')
    return redirect(url_for('timeline'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Logs the user in."""
    if g.user:
        return redirect(url_for('timeline'))
    error = None
    if request.method == 'POST':
        user = query_db('''select * from user where
            username = ?''', [request.form['username']], one=True)
        if user is None:
            error = 'Invalid username'
        elif not check_password_hash(user['pw_hash'],
                                     request.form['password']):
            error = 'Invalid password'
        else:
            flash('You were logged in')
            session['user_id'] = user['user_id']
            return redirect(url_for('timeline'))
    return render_template('login.html', error=error)


@app.route('/register', methods=['GET', 'POST'])
def register():
    """Registers the user."""
    if g.user:
        return redirect(url_for('timeline'))
    error = None
    if request.method == 'POST':
        if not request.form['username']:
            error = 'You have to enter a username'
        elif not request.form['email'] or \
                 '@' not in request.form['email']:
            error = 'You have to enter a valid email address'
        elif not request.form['password']:
            error = 'You have to enter a password'
        elif request.form['password'] != request.form['password2']:
            error = 'The two passwords do not match'
        elif get_user_id(request.form['username']) is not None:
            error = 'The username is already taken'
        else:
            db = get_db()
            db.execute('''insert into user (
              username, email, pw_hash) values (?, ?, ?)''',
              [request.form['username'], request.form['email'],
               generate_password_hash(request.form['password'])])
            db.commit()
            flash('You were successfully registered and can login now')
            return redirect(url_for('login'))
    return render_template('register.html', error=error)

@app.route('/api/receive_text', methods=['GET', 'POST'])
def receive_text():
	"""receive a text message from Twilio."""
	return 

@app.route('/logout')
def logout():
    """Logs the user out."""
    flash('You were logged out')
    session.pop('user_id', None)
    return redirect(url_for('public_timeline'))


# add some filters to jinja
app.jinja_env.filters['datetimeformat'] = format_datetime
app.jinja_env.filters['gravatar'] = gravatar_url


if __name__ == '__main__':
    init_db()
    app.run(host='127.0.0.1', debug=False, port=5000,  ssl_context=('/Users/lexi/Development/Certificates/server.crt', '/Users/lexi/Development/Certificates/server.key'))
