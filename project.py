#-*- coding: utf-8 -*- 

import sys
reload(sys)
sys.setdefaultencoding("utf-8")

from flask import Flask, render_template, request, redirect, jsonify, url_for, flash
import jobkorea_crawling
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
from database_setup import Base, User, Announcement, Resume
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests
from flask import session as login_session
import os

app = Flask(__name__)

# Connect to Database and create database session
engine = create_engine('sqlite:///joblistwithusers.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']


# Create anti-forgery state token
@app.route('/login')
def login():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    return render_template('login.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response


    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    # ADD PROVIDER TO LOGIN SESSION
    login_session['provider'] = 'google'

    # see if user exists, if it doesn't make a new one
    user_id = getUserID(data["email"])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h3>'
    output += login_session['username']
    output += '님, 환영합니다. </h3>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 100px; height: 100px;border-radius: 150px;-webkit-border-radius: 50px;-moz-border-radius: 50px;"> '
    flash("현재 %s로 로그인 했습니다." % login_session['username'])
    print "done!"
    return output


# User Helper Functions
def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    try:
        user = session.query(User).filter_by(id=user_id).one()
        return user
    except:
        return None


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


@app.route('/gdisconnect')
def gdisconnect():
    # Only disconnect a connected user.
    credentials = login_session.get('credentials')
    if credentials is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = credentials.access_token
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] != '200':
        # For whatever reason, the given token was invalid.
        response = make_response(
            json.dumps('Failed to revoke token for given user.'), 400)
        response.headers['Content-Type'] = 'application/json'
        return response


@app.route('/fbconnect', methods=['POST'])
def fbconnect():
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = request.data

    app_id = json.loads(open('fb_client_secrets.json', 'r').read())[
        'web']['app_id']
    app_secret = json.loads(
        open('fb_client_secrets.json', 'r').read())['web']['app_secret']
    url = 'https://graph.facebook.com/oauth/access_token?grant_type=fb_exchange_token&client_id=%s&client_secret=%s&fb_exchange_token=%s' % (
        app_id, app_secret, access_token)
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]

    # Use token to get user info from API
    userinfo_url = "https://graph.facebook.com/v2.4/me"
    # strip expire tag from access token
    token = result.split("&")[0]


    url = 'https://graph.facebook.com/v2.4/me?%s&fields=name,id,email' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]

    data = json.loads(result)

    login_session['provider'] = 'facebook'
    login_session['username'] = data["name"]
    login_session['email'] = data["email"]
    login_session['facebook_id'] = data["id"]

    stored_token = token.split('=')[1]
    login_session['access_token'] = stored_token

        # Get user picture
    url = 'https://graph.facebook.com/v2.4/me/picture?%s&redirect=0&height=200&width=200' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)

    login_session['picture'] = data["data"]["url"].encode('utf-8')

    # see if user exists
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h3>'
    output += login_session['username']
    output += '님, 환영합니다. </h3>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 100px; height: 100px;border-radius: 150px;-webkit-border-radius: 50px;-moz-border-radius: 50px;"> '

    flash("현재 %s로 로그인했습니다." % login_session['username'])
    return output


@app.route('/fbdisconnect')
def fbdisconnect():
    facebook_id = login_session['facebook_id']
    # The access token must me included to successfully logout
    access_token = login_session['access_token']
    url = 'https://graph.facebook.com/%s/permissions?access_token=%s' % (facebook_id,access_token)
    h = httplib2.Http()
    result = h.request(url, 'DELETE')[1]
    return "you have been logged out"


@app.route('/kconnect', methods=['POST'])
def kconnect():
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    
    # Store the access token in the session for later use.
    access_token = request.data.split('"')[3]
    login_session['access_token'] = access_token


    # Get user Info
    userinfo_url = "https://kapi.kakao.com/v1/user/me"
    #headers = {'Authorization': 'Bearer 8mLOnNtdmiSVV0nlgbaqkB_WrxsaUus2Q0uD0AopdgcAAAFaOkTUnw'}
    headers = {'Authorization': 'Bearer %s' % access_token}
    answer = requests.post('https://kapi.kakao.com/v1/user/me', headers=headers)
    data = answer.json()

    if data.get('error') is not None:
        response = make_response(json.dumps(data.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    login_session['username'] = data['properties']['nickname'].encode('utf-8')
    login_session['picture'] = data['properties']['profile_image'].encode('utf-8')
    login_session['provider'] = 'kakao'
    login_session['kakao_id'] = data['id']
    login_session['email'] = ""

    # see if user exists
    user = getUserInfo(data['id'])
    if not user:
        newUser = User(name=buffer(login_session['username']), picture=login_session['picture'],
                        email ="", id = login_session['kakao_id'])
        session.add(newUser)
        session.commit()

    login_session['user_id'] = user.id


    output = ''
    output += '<h3>'
    output += login_session['username']
    output += '님, 환영합니다. </h3>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 100px; height: 100px;border-radius: 150px;-webkit-border-radius: 50px;-moz-border-radius: 50px;"> '
    flash("현재  %s로 로그인했습니다." % login_session['username'])
    print "done!"
    return output


@app.route('/kdisconnect')
def kdisconnect():
    # The access token must me included to successfully logout
    access_token = login_session['access_token']
    #access_token = request.data.split('"')[3]
    headers = {'Authorization': 'Bearer %s' % access_token}
    result = requests.get("https://kapi.kakao.com/v1/user/logout", headers = headers)
    return "you have been logged out"


# Disconnect based on provider
@app.route('/disconnect')
def disconnect():
    if 'provider' in login_session:
        if login_session['provider'] == 'google':
            gdisconnect()
            del login_session['gplus_id']
            #del login_session['credentials']
        if login_session['provider'] == 'facebook':
            fbdisconnect()
            del login_session['facebook_id']
        if login_session['provider'] == 'kakao':
            kdisconnect()
            del login_session['kakao_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']
        del login_session['provider']
        flash("로그아웃 되었습니다.")
        return redirect(url_for('jobPosting'))
    else:
        flash("You were not logged in")
        return redirect(url_for('jobPosting'))


@app.route('/fetchingpublic', methods=['GET','POST'])
def listFetchingPublic():
	if request.method == "GET":
		return render_template("jobpostingpublic.html")
	companyList = jobkorea_crawling.crawlCompanyList()
	
	output=""
	output += '<div class="panel panel-default">'
	output += '<div class="panel-heading">기업 리스트</div>'
	output += '<table class="table">'
	output += '<thead><tr><th>#</th><th>기업명</th><th>공고 제목</th><th>직무</th>'
	output += '<th>페이지링크</th><th>기한</th></tr></thead><tbody>'

	index = 0
	for c in companyList:
		index +=1
		output += '<tr><th>'+str(index)+'</th><td>'+c['이름']+'</td>'
		output += '<td>'+c['공고 제목']+'</td>'
		output += '<td>'+c['직무']+'</td>'
		link = c['공고 주소']
		output += '<td><a href="%s">보러가기</a></td>' % link
		output += '<td>'+c['기한']+'</td></tr>'

	output += '</tbody></table></div>'

	return output



@app.route('/fetching', methods=['POST'])
def listFetching():
	if 'username' not in login_session:
		return redirect('/login')

	companyList = jobkorea_crawling.crawlCompanyList()

	output=""
	output += '<div class="panel panel-default">'
	output += '<div class="panel-heading">기업 리스트</div>'
	output += '<table class="table">'
	output += '<thead><tr><th>#</th><th>기업명</th><th>공고 제목</th><th>직무</th>'
	output += '<th>페이지링크</th><th>기한</th><th>즐겨찾기</th>'
	output += '</tr></thead><tbody>'

	index = 0
	for c in companyList:
		index +=1
		output += '<tr id="tr%s"><th>' % str(index)
		output += str(index)+'</th><td>'+c['이름']+'</td>'
		output += '<td>'+c['공고 제목']+'</td>'
		output += '<td>'+c['직무']+'</td>'
		link = c['공고 주소']
		output += '<td><a href="%s">보러가기</a></td>' % link
		output += '<td>'+c['기한']+'</td>'
		output += '<td><i id="star%s" class="fa fa-star-o" aria-hidden="true"></i></td><tr>' % str(index)

	output += '</tbody></table></div>'

	return output
	

def get_rookie_salary(cName):
	baseUrl = "https://kreditjob.com/api_ver2/getInfoByQueryPkNm?query="
	response = requests.get(baseUrl+cName)
	try:
		return response.json().get('data')[0].get('ROOKEY_SALARY_YY')
	except:
		return None


@app.route('/storingfavorite', methods = ['POST'])
def storingFavorite():
	htmlText = request.form.get("htmlText")
	checked = request.form.get("checked")

	htmlText = htmlText.replace('</th><td>', '$$')
	company = htmlText.replace('</td><td>', '$$')
	aList = company.split('$$')

	try:
		thisAnnounce=session.query(Announcement).filter_by(\
					user_id=login_session['user_id']).filter_by(\
					companyName=aList[1]).one()
	except:
		thisAnnounce = None

	if checked == 'true':
		if thisAnnounce is None:
			a = Announcement(companyName=aList[1], title=aList[2],position=aList[3],pageLink=aList[4][9:-10],\
						  dueDate=aList[5], payment=get_rookie_salary(aList[1]), user_id=login_session['user_id'],)
			session.add(a)
			session.commit()
			return "%s이(가) 추가되었습니다." % aList[1]
		else:
			return "이미 %s이(가) 추가되어있습니다." % aList[1]
	elif checked == 'false':
		session.delete(thisAnnounce)
		session.commit()
		return "%s이(가) 삭제되었습니다." % aList[1]
	
	return ""


@app.route('/')
def jobPosting():
	if 'username' not in login_session:
		return render_template('jobpostingpublic.html')
	else:
		return render_template('jobposting.html')


@app.route('/public')
def jobPostingPublic():
	return render_template('jobpostingpublic.html')


@app.route('/deleteFavorite', methods=['POST'])
def deleteFavorite():
	aId = request.form.get('aId')
	a = session.query(Announcement).filter_by(id=aId).one()
	session.delete(a)
	session.commit()
	return "제거했습니다."


@app.route('/my')
def myPosting():
	#quer = session.query(Announcement).all()
	#for q in quer:
	#	print q

	# delete all query
	#for tbl in reversed(Base.metadata.sorted_tables):
	#	engine.execute(tbl.delete())
	if 'username' not in login_session:
		return redirect('/login')

	user=session.query(User).all()
	for u in user:
		print u.id
	print login_session['user_id']


	data = session.query(Announcement).filter_by(user_id=login_session['user_id']).all()
	return render_template('my.html', data = data)


@app.route('/resume/<int:post_id>')
def resume(post_id):
	a = session.query(Announcement).filter_by(id = post_id).one()
	
	if 'username' not in login_session:
		return redirect('/login')
	if a.user_id != login_session['user_id']:
		return "<script>function myFunction() {alert(\
				'권한이 없습니다. 본인의 자소서를 확인해주세요.');}</script><body onload='myFunction()''>"

	resumes = session.query(Resume).filter_by(announcement_id = post_id).all()
	return render_template('myresume.html', post_id = post_id, resumes = resumes, a=a)


@app.route('/resume/<int:post_id>/new', methods=['GET', 'POST'])
def newQuestion(post_id):
	a = session.query(Announcement).filter_by(id=post_id).one()

	if 'username' not in login_session:
		return redirect('/login')
	if a.user_id != login_session['user_id']:
		return "<script>function myFunction() {alert(\
				'권한이 없습니다. 본인의 자소서를 확인해주세요.');}</script><body onload='myFunction()''>"

	if request.method=='POST':
		newQuestion = Resume(question=request.form['question'], answer=request.form['answer'],\
							user_id=a.user_id, announcement_id=a.id)
		session.add(newQuestion)
		session.commit()
		flash("자소서 문항이 추가되었습니다.")
		return redirect(url_for('resume', post_id=post_id))
	else:
		return render_template('newresume.html', a=a)


@app.route('/resume/<int:post_id>/<int:q_id>/edit', methods=['GET', 'POST'])
def editQuestion(post_id, q_id):
	r = session.query(Resume).filter_by(id=q_id).one()

	if 'username' not in login_session:
		return redirect('/login')
	if r.user_id != login_session['user_id']:
		return "<script>function myFunction() {alert(\
				'권한이 없습니다. 본인의 자소서를 확인해주세요.');}</script><body onload='myFunction()''>"

	if request.method=='POST':
		r.question = request.form['question']
		r.answer = request.form['answer']
		session.add(r)
		session.commit()
		flash('문항이 수정되었습니다.')
		return redirect(url_for('resume', post_id=post_id))
	else:
		return render_template('editresume.html', r=r)


@app.route('/resume/<int:post_id>/<int:q_id>/delete', methods=['GET', 'POST'])
def deleteQuestion(post_id, q_id):
	r=session.query(Resume).filter_by(id=q_id).one()

	if 'username' not in login_session:
		return redirect('/login')
	if r.user_id != login_session['user_id']:
		return "<script>function myFunction() {alert(\
				'권한이 없습니다. 본인의 자소서를 확인해주세요.');}</script><body onload='myFunction()''>"

	if request.method =='POST':
		session.delete(r)
		session.commit()
		flash('문항이 삭제되었습니다.')
		return redirect(url_for('resume', post_id=post_id))
	else:
		return render_template('deleteresume.html', r=r)



if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)