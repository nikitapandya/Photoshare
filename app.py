######################################
# author ben lawson <balawson@bu.edu> 
######################################
# Some code adapted from 
# CodeHandBook at http://codehandbook.org/python-web-application-development-using-flask-and-mysql/
# and MaxCountryMan at https://github.com/maxcountryman/flask-login/
# and Flask Offical Tutorial at  http://flask.pocoo.org/docs/0.10/patterns/fileuploads/
# see links for further understanding
###################################################

import flask
from flask import Flask, Response, request, render_template, redirect, url_for
from flaskext.mysql import MySQL
import flask.ext.login as flask_login
from flask import abort 

#for image uploading
from werkzeug import secure_filename
import os, base64

import datetime
from operator import itemgetter


mysql = MySQL()
app = Flask(__name__)
app.secret_key = 'super secret string'  # Change this!

#These will need to be changed according to your creditionals
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'SDAolc2903'
app.config['MYSQL_DATABASE_DB'] = 'photoshare'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)

#begin code used for login
login_manager = flask_login.LoginManager()
login_manager.init_app(app)

conn = mysql.connect()
cursor = conn.cursor()
cursor.execute("SELECT email from Users") 
users = cursor.fetchall()

def getUserList():
    cursor = conn.cursor()
    cursor.execute("SELECT email from Users") 
    return cursor.fetchall()

class User(flask_login.UserMixin):
    pass

@login_manager.user_loader
def user_loader(email):
    users = getUserList()
    if not(email) or email not in str(users):
        return
    user = User()
    user.id = email
    return user

@login_manager.request_loader
def request_loader(request):
    users = getUserList()
    email = request.form.get('email')
    if not(email) or email not in str(users):
        return
    user = User()
    user.id = email
    cursor = mysql.connect().cursor()
    cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email))
    data = cursor.fetchall()
    if len(data) == 0:
        return
    pwd = str(data[0][0])
    user.is_authenticated = request.form['password'] == pwd 
    return user

'''
A new page looks like this:
@app.route('new_page_name')
def new_page_function():
    return new_page_html
'''

@app.route('/login', methods=['GET', 'POST'])
def login():
    if flask.request.method == 'GET':
        try:
            uid = getUserIdFromEmail(flask_login.current_user.id)
            return render_template('hello.html', message2='You are alreay logged in!')
        except:
            return render_template('login.html')
    #The request method is POST (page is recieving data)
    email = flask.request.form['email']
    cursor = conn.cursor()
    #check if email is registered
    if cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email)):
        data = cursor.fetchall()
        pwd = str(data[0][0] )
        if flask.request.form['password'] == pwd:
            user = User()
            user.id = email
            flask_login.login_user(user) #okay login in user
            return flask.redirect(flask.url_for('protected')) #protected is a function defined in this file

    #information did not match
    return render_template('login.html', message='The login information you entered did not match our records. Please try again or register!')

@app.route('/logout')
def logout():
    flask_login.logout_user()
    return render_template('hello.html', message2='Logged out') 

@login_manager.unauthorized_handler
def unauthorized_handler():
    return render_template('unauth.html') 

#you can specify specific methods (GET/POST) in function header instead of inside the functions as seen earlier
@app.route("/register", methods=['GET'])
def register():
    return render_template('register.html', supress='True')  

@app.route("/register", methods=['POST'])
def register_user():
    try:
        email=request.form.get('email')
        password=request.form.get('password')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        dob = request.form.get('date_of_birth')
        hometown = request.form.get('hometown')
        gender = request.form.get('gender')
    except:
        return flask.redirect(flask.url_for('register'))
    cursor = conn.cursor()
    test =  isEmailUnique(email)
    if test:
        print cursor.execute("INSERT INTO Users (email, password, first_name, last_name, dob, hometown, gender) VALUES ('{0}', '{1}', '{2}', '{3}', '{4}', '{5}', '{6}')".format(
        email, password, first_name, last_name, dob, hometown, gender))
        conn.commit()
        #log user in
        user = User()
        user.id = email
        flask_login.login_user(user)
        return render_template('hello.html', name=email, message='Account Created!')
    else:
        return flask.redirect(flask.url_for('register'))

def getDate():
    now = datetime.datetime.now()
    string = '%s/%s/%s' % (now.year, now.month, now.day)
    return string

def getTaggedPhotos(tag_word):
    cursor = conn.cursor()
    cursor.execute("SELECT p.imgdata, p.picture_id FROM Pictures p, Has h, Tags t WHERE h.picture_id=p.picture_id \
                    AND h.tag_id=t.tag_id AND t.key_word='{0}'".format(tag_word))
    return cursor.fetchall()


def you_may_also_tag(photo_id, album_id, uid):
    if uid == None:
        return None 
    #all of user's albums 

    if uid: 
        cursor = conn.cursor()
        cursor.execute("SELECT * from Creates WHERE user_id='{0}' AND album_id='{1}'".format(uid, album_id))
        result = cursor.fetchall()
        if len(result) == 0:
            return None

    # all distinct present tags for this photo
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT h.tag_id FROM Has h WHERE h.picture_id='{0}'".format(photo_id))
    result = cursor.fetchall()
    if len(result) == 0:
        return None

    final = []
    for tag in result:
        cursor = conn.cursor()
        #getting tag word while making sure its not the tag word from this picture
        cursor.execute("SELECT DISTINCT t.key_word FROM Has h JOIN Tags t ON t.tag_id=h.tag_id AND h.tag_id!='{0}' AND h.picture_id!='{1}' LIMIT 5".format(int(tag[0]), photo_id))
        other_tags = cursor.fetchall()
        for o in other_tags:
            if o[0] not in final:
                final.append(o[0]) 

    conn.commit()
    return ', '.join(final)

@app.route('/add_tags', methods=['GET', 'POST'])
def add_tags():
    uid = getUserIdFromEmail(flask_login.current_user.id)
    ids = request.form.get('ids').split(',')
    album_id = ids[0]
    photo_id = ids[1]

    tags = request.form.get('tags').rstrip(',').split(',')

    # ADD TAGS :) 
    lst = []
    for i in tags:
        if ' ' in i:
            e = i.rstrip(' ').split(' ')
            for j in e:
                if j != '':
                    lst.append(j)
        elif i != '':
            lst.append(i)

    for tag in lst:
        cursor = conn.cursor()
        cursor.execute("SELECT tag_id FROM tags WHERE key_word = '{0}'".format(tag))
        tag_id = cursor.fetchall()
        if len(tag_id) == 0:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO Tags (key_word) VALUES ('{0}')".format(tag))
            cursor = conn.cursor()
            cursor.execute("SELECT MAX(tag_id) from Tags")
            tag_id = cursor.fetchall()
        # Add to Has 
        cursor = conn.cursor()
        cursor.execute("SELECT tag_id, picture_id FROM Has WHERE tag_id = '{0}' AND picture_id='{1}'".format(tag_id[0][0], photo_id))
        result = cursor.fetchall()
        if len(result) == 0:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO Has (tag_id, picture_id) VALUES ('{0}', '{1}')".format(tag_id[0][0], photo_id))

        # Add to Forms 
        cursor = conn.cursor()
        cursor.execute("SELECT tag_id, user_id FROM Forms WHERE tag_id = '{0}' AND user_id='{1}'".format(tag_id[0][0], uid))
        result = cursor.fetchall()
        if len(result) == 0:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO Forms (tag_id, user_id, date_formed) VALUES ('{0}', '{1}', '{2}')".format(tag_id[0][0], uid, getDate()))

    album_name = getAlbumName(album_id)

    conn.commit()
    return render_template('view_album.html', message="Here are the photos in album %s" % album_name, photos=preparePhotoListing(album_id))


def getUsersAlbums(uid):
    cursor = conn.cursor()
    cursor.execute("SELECT a.name, a.album_id FROM Creates c, Albums a WHERE c.user_id = '{0}' AND c.album_id=a.album_id".format(uid))
    return cursor.fetchall() #NOTE list of tuples, [(imgdata, pid), ...]

def getUsersFriends(uid):
    cursor = conn.cursor()
    cursor.execute("SELECT user_id2 FROM Friends_with WHERE user_id1 = '{0}'".format(uid))
    return cursor.fetchall() #NOTE list of tuples, [(imgdata, pid), ...]

def getUsersPhotos(album_id):
    cursor = conn.cursor()
    cursor.execute("SELECT p.imgdata, p.picture_id, p.caption FROM Pictures p, Contains c WHERE p.picture_id=c.picture_id AND c.album_id = '{0}'".format(album_id))
    return cursor.fetchall() #NOTE list of tuples, [(imgdata, pid), ...]

def getPhotoComments(photo_id):
    cursor = conn.cursor()
    cursor.execute("SELECT c.comment_text, u.first_name, u.last_name FROM Users u, Comments c, Makes m, Comment_on o \
                    WHERE m.user_id = u.user_id AND c.comment_id = m.comment_id AND c.comment_id = o.comment_id AND o.picture_id = '{0}'".format(photo_id))
    return cursor.fetchall() # (comment_text, firstname, lastname)) 

def getPhotoLikes(photo_id):
    cursor = conn.cursor()
    cursor.execute("SELECT u.first_name, u.last_name FROM Likes l, Users u WHERE l.user_id = u.user_id AND l.picture_id = '{0}'".format(photo_id))
    return cursor.fetchall() # (firstname, lastname) 

def getPhotoTags(photo_id):
    cursor = conn.cursor()
    cursor.execute("SELECT t.key_word FROM Tags t, Has h WHERE h.tag_id = t.tag_id AND h.picture_id = '{0}'".format(photo_id))
    return cursor.fetchall() # (tags key words) 

def getUserIdFromEmail(email):
    cursor = conn.cursor()
    cursor.execute("SELECT user_id  FROM Users WHERE email = '{0}'".format(email))
    return cursor.fetchone()[0]

def isEmailUnique(email):
    #use this to check if a email has already been registered
    cursor = conn.cursor()
    if cursor.execute("SELECT email  FROM Users WHERE email = '{0}'".format(email)): 
        #this means there are greater than zero entries with that email
        return False
    else:
        return True
#end login code

def getUsersInfo(uid):
    cursor = conn.cursor()
    cursor.execute("SELECT first_name, last_name, dob, email, hometown, gender FROM Users WHERE user_id='{0}'".format(uid))
    info = cursor.fetchall()[0]
    prettier_info = []
    prettier_info.append('Name: '+info[0]+' '+info[1])
    prettier_info.append('Date of birth: '+str(info[2]))
    prettier_info.append('Email address: '+info[3])
    prettier_info.append('Hometown: '+info[4])
    prettier_info.append('Gender: '+info[5])

    cursor = conn.cursor()
    cursor.execute("SELECT count(*) FROM Contains n, Creates r WHERE r.album_id=n.album_id AND r.user_id='{0}'".format(uid))
    num_pics = cursor.fetchall()[0][0]
    cursor = conn.cursor()
    cursor.execute("SELECT count(*) FROM Makes m WHERE m.user_id='{0}'".format(uid))
    num_comments = cursor.fetchall()[0][0]
    conn.commit()
    return [prettier_info, num_pics, num_comments] 

@app.route('/profile')
@flask_login.login_required
def protected():
    uid = getUserIdFromEmail(flask_login.current_user.id)
    return render_template('hello.html', name=flask_login.current_user.id, message="Here's your profile", info=getUsersInfo(uid))

#begin photo uploading code
# photos uploaded using base64 encoding so they can be directly embeded in HTML 
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['GET', 'POST'])
@flask_login.login_required
def upload_file():
    if request.method == 'POST':
        uid = getUserIdFromEmail(flask_login.current_user.id)
        imgfile = request.files['file']
	photo_data = base64.standard_b64encode(imgfile.read())
        caption = request.form.get('caption')
        album_name = request.form.get('album_name')
        tags = request.form.get('tags').rstrip(',').split(',')
        
        # Check if album doesn't exist, then create it
        # otherwise, just add the relationship :) 
        cursor = conn.cursor()
        cursor.execute("SELECT album_id from Albums WHERE name = '{0}'".format(album_name))
        album_id = cursor.fetchall()
        if len(album_id) == 0:
            # create a new album
            cursor = conn.cursor()
            cursor.execute("INSERT INTO Albums (name) VALUES ('{0}')".format(album_name))
            
            # get its id
            cursor = conn.cursor()
            cursor.execute("SELECT MAX(album_id) FROM Albums")
            album_id =  cursor.fetchall()

            # connect the user to the new album
            cursor = conn.cursor()
            cursor.execute("INSERT INTO Creates (album_id, user_id, date_created) VALUES ('{0}', '{1}', '{2}')".format(album_id[0][0], uid, getDate()))        

        # add the photo to Pictures 
        try:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO Pictures (imgdata, caption) VALUES ('{0}', '{1}')".format(photo_data, caption))
        except:
            return render_template('error.html', message='The picture is too big! Please try again with a smaller picture :)!')

        # get the photo id
        cursor = conn.cursor()
        cursor.execute("SELECT MAX(picture_id) FROM Pictures")
        photo_id = cursor.fetchall()[0][0]

        # connect the photo to the album
        cursor = conn.cursor()
        cursor.execute("INSERT INTO Contains (album_id, picture_id, date_added) VALUES ('{0}', '{1}', '{2}')".format(album_id[0][0], photo_id, getDate()))

        # ADD TAGS :) 
        lst = []
        for i in tags:
            if ' ' in i:
                e = i.rstrip(' ').split(' ')
                for j in e:
                    if j != '':
                        lst.append(j)
            elif i != '':
                lst.append(i)

        for tag in lst:
            cursor = conn.cursor()
            cursor.execute("SELECT tag_id FROM tags WHERE key_word = '{0}'".format(tag))
            tag_id = cursor.fetchall()
            if len(tag_id) == 0:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO Tags (key_word) VALUES ('{0}')".format(tag))
                cursor = conn.cursor()
                cursor.execute("SELECT MAX(tag_id) from Tags")
                tag_id = cursor.fetchall()
            # Add to Has 
            cursor = conn.cursor()
            cursor.execute("SELECT tag_id, picture_id FROM Has WHERE tag_id = '{0}' AND picture_id='{1}'".format(tag_id[0][0], photo_id))
            result = cursor.fetchall()
            if len(result) == 0:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO Has (tag_id, picture_id) VALUES ('{0}', '{1}')".format(tag_id[0][0], photo_id))

            # Add to Forms 
            cursor = conn.cursor()
            cursor.execute("SELECT tag_id, user_id FROM Forms WHERE tag_id = '{0}' AND user_id='{1}'".format(tag_id[0][0], uid))
            result = cursor.fetchall()
            if len(result) == 0:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO Forms (tag_id, user_id, date_formed) VALUES ('{0}', '{1}', '{2}')".format(tag_id[0][0], uid, getDate()))
 
        conn.commit()
        return view_album(album_id[0][0])
	#return render_template('hello.html', name=flask_login.current_user.id, message='Photo uploaded!', photos=getUsersPhotos(album_id[0][0]))
    #The method is GET so we return a  HTML form to upload the a photo.
    return render_template('upload.html')

#end photo uploading code 

@app.route('/friends', methods=['GET', 'POST'])
@flask_login.login_required
def list_friends(message=None):
    uid = getUserIdFromEmail(flask_login.current_user.id)
    lst = [i[0] for i in getUsersFriends(uid)]
    names = []
    for j in lst:
        cursor = conn.cursor()
        cursor.execute("SELECT first_name, last_name, email FROM Users where user_id = '{0}'".format(j))
        names.append(cursor.fetchall()[0])
    return render_template('friends.html', message=message, friends=names)

@app.route('/add_friends', methods=['GET', 'POST'])
@flask_login.login_required
def add_friends():
    if request.method == 'GET':
      return render_template('add_friends.html') 

    uid = getUserIdFromEmail(flask_login.current_user.id)
    email = request.form.get('email')

    cursor = conn.cursor()
    cursor.execute("SELECT user_id from Users WHERE email = '{0}'".format(email))
    id = cursor.fetchall()
 
    if len(id) == 0:
        message = 'This email does not exist in the database!'
        return list_friends(message=message)

    if uid == id[0][0]:
        message = "You can't friend yourself hon!"
        return list_friends(message=message)

    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO Friends_with (user_id1, user_id2, since) VALUES ('{0}', '{1}', '{2}')".format(uid, id[0][0], getDate()))
        cursor = conn.cursor()
        cursor.execute("INSERT INTO Friends_with (user_id1, user_id2, since) VALUES ('{0}', '{1}', '{2}')".format(id[0][0], uid, getDate()))
        message = 'User added as a friend!!'
    except:
        message = 'You are already friends with this user!'

    conn.commit()
    return list_friends()

def getTopTags():
    cursor = conn.cursor()
    cursor.execute("select count(*), t.tag_id, t.key_word from Tags t, Has h where t.tag_id = h.tag_id group by h.tag_id order by count(*) desc limit 5")
    return cursor.fetchall() 

@app.route('/albums', methods=['GET', 'POST'])
def list_albums():
    try:
        uid = getUserIdFromEmail(flask_login.current_user.id)
        albums=getUsersAlbums(uid)
        albums2=getAllAlbums()
    except:
        albums=None
        albums2=getAllAlbums()
    return render_template('albums.html', albums=albums, albums2=albums2)

@app.route('/delete_album', methods=['GET', 'POST'])
def delete_album():
    uid = getUserIdFromEmail(flask_login.current_user.id)
    ids = request.form.get('ids').split(',')
    album_id = ids[0]
    cursor = conn.cursor()
    cursor.execute("SELECT picture_id from Contains where album_id='{0}'".format(album_id))
    allPhotos = cursor.fetchall() #((1,), (3,) ... )
    
    for i in allPhotos:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM Pictures WHERE picture_id='{0}'".format(i[0]))
 
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Albums WHERE album_id='{0}'".format(album_id))
    conn.commit()
    return list_albums()

def getAllAlbums():
    cursor = conn.cursor()
    cursor.execute("SELECT a.name, a.album_id FROM Albums a")
    return cursor.fetchall() #NOTE list of tuples, [(imgdata, pid), ...]

def preparePhotoListing(album_id):
    try: 
        uid = getUserIdFromEmail(flask_login.current_user.id)
    except:
        uid = None
        
    photos = getUsersPhotos(album_id) # ((data, photo_id, caption), ( ), ( ) ...)
    photos_list = [] 
    for i in range(len(photos)):
        comments = getPhotoComments(photos[i][1]) #text, fname, lname
        comments_names = [] #(name: txt) 
        for c in comments:
            comments_names.append((c[1]+' '+c[2]+' : '+c[0]))
 
        likes = getPhotoLikes(photos[i][1]) # fname, lname 
        likes_names = [] #(name1, name2, name3 ....)
        for j in likes: 
            name = j[0] + ' ' + j[1]
            if name not in likes_names:
                likes_names.append(name) 

        tags = getPhotoTags(photos[i][1]) #key words
        other_tags = you_may_also_tag(int(photos[i][1]), int(album_id), uid)
        photos_list.append((photos[i], comments_names, len(likes), ', '.join(likes_names), tags, album_id, other_tags))
        
    return photos_list

@app.route('/view_album', methods=['GET', 'POST'])
def view_album(album_id=None):
   try:
        uid = getUserIdFromEmail(flask_login.current_user.id)
   except:
        uid = create_anonymous()

   if not album_id:
        ids = request.form.get('ids').split(',')
        album_id = ids[0]
   
   album_name = getAlbumName(album_id)

   cursor = conn.cursor()
   cursor.execute("SELECT c.album_id FROM Creates c WHERE c.user_id='{0}'".format(uid))
   result = cursor.fetchall()
   conn.commit()
   return render_template('view_album.html', message="Here are the photos in album %s" % album_name, photos=preparePhotoListing(album_id))

@app.route('/get_album_of', methods=['GET', 'POST'])
def get_album_of():
   picture_id = request.form.get('picture_id')
   cursor = conn.cursor()
   cursor.execute("SELECT c.album_id FROM Contains c WHERE c.picture_id='{0}'".format(picture_id))
   album_id = cursor.fetchall()[0][0]
   album_name = getAlbumName(album_id)
   conn.commit() 
   return render_template('view_album.html', message="Here are the photos in album %s" % album_name, photos=preparePhotoListing(album_id))

def create_anonymous():
    cursor = conn.cursor()
    cursor.execute("INSERT INTO Users (first_name, last_name, password) VALUES ('Anonymous', '', '123')")
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(user_id) FROM Users")
    uid = cursor.fetchall()[0][0]
    conn.commit()
    return uid

@app.route('/search_tags', methods=['GET', 'POST'])
def search_tags():
    tag_word = request.form.get('tag_word')
    return render_template('view_album.html', message="Here are the pictures with the tag", tag=tag_word, tagged=getTaggedPhotos(tag_word))

@app.route('/search_users', methods=['GET', 'POST'])
def search_users():
    email2 = request.form.get('email')
    cursor = conn.cursor()
    cursor.execute("SELECT user_id from Users WHERE email = '{0}'".format(email2))
    id = cursor.fetchall()
    conn.commit()
    if len(id) == 0:
        message = 'This email does not exist in the database!'
        return render_template('hello.html', message2=message)
    else:
        message = 'Here is the profile for user %s' % email2
        sth = getUsersInfo(id[0][0])
        return render_template('friends.html', message2=message, info=sth)

@app.route('/delete_photo', methods=['GET', 'POST'])
@flask_login.login_required
def delete_photo():
    uid = getUserIdFromEmail(flask_login.current_user.id)
    ids = request.form.get('ids').split(',')
    album_id = ids[0]
    photo_id = ids[1]

    cursor = conn.cursor() 
    cursor.execute("SELECT * FROM Creates c WHERE c.user_id='{0}' AND c.album_id='{1}'".format(uid, album_id))
    result = cursor.fetchall()
    if len(result) == 0:
       return view_album(album_id) 

    cursor = conn.cursor()
    cursor.execute("DELETE FROM Pictures WHERE picture_id='{0}'".format(photo_id))
    conn.commit()
    return view_album(album_id)

@app.route('/add_likes', methods=['GET', 'POST'])
def add_likes():
    try:
        uid = getUserIdFromEmail(flask_login.current_user.id)
    except:
        uid = create_anonymous()

    ids = request.form.get('ids').split(',')
    album_id = ids[0]
    photo_id = ids[1]
    
    cursor = conn.cursor()
    cursor.execute("SELECT * from Likes WHERE user_id = '{0}' AND picture_id = '{1}'".format(uid, photo_id))
    result = cursor.fetchall()
    if len(result) == 0:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO Likes (user_id, picture_id) VALUES ('{0}', '{1}')".format(uid, photo_id))

    conn.commit()
    return render_template('view_album.html', photos=preparePhotoListing(album_id))

def getAlbumName(album_id):
    cursor = conn.cursor()
    cursor.execute("SELECT a.name from Albums a WHERE a.album_id='{0}'".format(album_id))
    n = cursor.fetchall()
    return n[0][0]

@app.route('/add_comments', methods=['GET', 'POST'])
def add_comments():
    try:
        uid = getUserIdFromEmail(flask_login.current_user.id)
    except:
        uid = create_anonymous()

    comment_text = request.form.get('comment_text')
    ids = request.form.get('ids').split(',')
    album_id = ids[0]
    album_name = getAlbumName(album_id)
    photo_id = ids[1]
   
    cursor = conn.cursor()
    cursor.execute("SELECT * from Creates WHERE user_id='{0}' AND album_id='{1}'".format(uid, album_id))
    result = cursor.fetchall()
    if len(result) > 0:
        return render_template('view_album.html', message="You can't comment on your own pictures! :)", photos=preparePhotoListing(album_id))
 
    cursor = conn.cursor()
    cursor.execute("INSERT INTO Comments (comment_text) VALUES ('{0}')".format(comment_text))
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(comment_id) FROM Comments")
    comment_id = cursor.fetchall()[0][0]
    
    cursor = conn.cursor()
    cursor.execute("INSERT INTO Makes (user_id, comment_id) VALUES ('{0}', '{1}')".format(uid, comment_id))

    cursor = conn.cursor()
    cursor.execute("INSERT INTO Comment_on (comment_id, picture_id) VALUES ('{0}', '{1}')".format(comment_id, photo_id))

    conn.commit()
    return render_template('view_album.html', message="Here is the photo in album %s" % album_name, photos=preparePhotoListing(album_id))

@app.route('/tagged_photos', methods=['GET', 'POST'])
def tagged_photos():
    tag_word = request.form.get('tag_word')
    return render_template('view_album.html', message="You don't have any pictures in this tag", tag=tag_word, tagged=getTaggedPhotos(tag_word)) 

def getTaggedPhotos2(tag_word, uid):
    cursor = conn.cursor()
    cursor.execute("SELECT distinct h.picture_id, p.imgdata FROM Creates r, Contains n, Pictures p, Has h, Tags t WHERE h.picture_id=p.picture_id \
                    AND h.tag_id=t.tag_id AND t.key_word='{0}' AND r.album_id=n.album_id AND h.picture_id=n.picture_id AND r.user_id!='{1}'".format(tag_word, uid))
    return cursor.fetchall()


def you_may_also_like():
    try: 
        uid = getUserIdFromEmail(flask_login.current_user.id)
    except:
        return None

    cursor = conn.cursor()
    cursor.execute("select distinct t.key_word from Albums a JOIN Creates c JOIN Contains n JOIN Has h JOIN Tags t ON \
                    t.tag_id=h.tag_id AND h.picture_id=n.picture_id AND n.album_id=c.album_id AND c.album_id=a.album_id AND c.user_id='{0}'".format(uid))
    tags = cursor.fetchall()
    result = []
    for t in tags:
        cursor = conn.cursor()
        cursor.execute("SELECT count(h.picture_id) FROM Has h JOIN Tags t WHERE t.key_word='{0}' AND h.tag_id=t.tag_id".format(t[0]))
        count = cursor.fetchall()
        result.append([t[0], count[0][0]])
    final = sorted(result, key=itemgetter(1), reverse=True)[:5]
    allPhotos = []
    for i in final:
        allPhotos.append(getTaggedPhotos2(i[0], uid))
    return allPhotos    

def getConNumbers():
    cursor = conn.cursor()
    cursor.execute("SELECT count(m.comment_id), m.user_id from Makes m GROUP BY m.user_id")
    comments = cursor.fetchall()
    
    cursor = conn.cursor()
    cursor.execute("SELECT count(n.picture_id), r.user_id FROM Creates r, Contains n WHERE r.album_id=n.album_id GROUP BY r.user_id")
    photos = cursor.fetchall()
    
    users1 = []
    users2 = []
    for i in comments:
        users1 += [i[1]]

    for j in photos:
        users2 += [j[1]]

    result = [] #[ (user_id, count photos, count comments), (user_id, 0, count_comment) ]

    for i in comments:
        if i[1] in users2: 
            for j in photos:
                if i[1] == j[1]:
                    result.append((i[1], i[0], j[0]))
        
    for k in comments:
        if k[1] not in users2:
            result.append((k[1], 0, k[1]))

    for m in photos:
        if m[1] not in users1:
            result.append((m[1], m[1], 0))

    final = []
    for b in result:
        cursor = conn.cursor()
        cursor.execute("SELECT u.first_name, u.last_name FROM Users u WHERE u.user_id='{0}'".format(b[0]))
        name = cursor.fetchall()[0]
        if name[0] != 'Anonymous':
            final.append([name[0]+' '+name[1], b[1]+b[2]])
    return sorted(final, key=itemgetter(1), reverse=True)[:10]

#default page  
@app.route("/", methods=['GET'])
def hello():
    return render_template('hello.html', tags=getTopTags(), total=getConNumbers(), also_like=you_may_also_like())

if __name__ == "__main__":
    #this is invoked when in the shell  you run 
    #$ python app.py 
    app.run(port=5000, debug=True)
