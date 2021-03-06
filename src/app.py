import json
import time
from flask import Flask, request
from db import db, User, Post, Tag
#from google.oauth2 import id_token
import requests
#from google.auth.transport import requests

def create_app():
    app = Flask(__name__)
    db_filename = 'data.db'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///%s' % db_filename
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ECHO'] = True
    # Dynamically bind SQLAlchemy to application
    db.init_app(app)
    app.app_context().push() # this does the binding
    return app

app = create_app()
with app.app_context():
    db.create_all()
# the dict to return in the event of an invalid request
error_dict = {
    'success': False
}
AUTH_URL = "https://www.googleapis.com/userinfo/v2/me"
TH_APP_ID = "1054326645687-jqg2n4pf3iqdufsgni9blo7kcpu6ljed.apps.googleusercontent.com"


@app.route('/api/seed/', methods=['GET'])
def create_seed_data():
    new_user = User(
        google_id="106380710636073572230",
        nickname="littletree",
        join_date=int(time.time())
    )
    db.session.add(new_user)
    constructed_post = Post(
        text="I'm so sad",
        nickname="littletree",
        upload_date=int(time.time()),
        user_id=1
    )
    db.session.add(constructed_post)
    db.session.commit()
    return json.dumps({'success': True})


@app.route('/api/posts/', methods=['GET'])
def get_all_posts():
    posts = Post.query.all()
    response = {
        'success': True,
        'data': [post.serialize() for post in posts]
    }
    return json.dumps(response), 200


@app.route('/api/users/', methods=['POST'])
def register_user():
    # ensure the body is valid JSON
    try:
        post = json.loads(request.data)
    except ValueError:
        return json.dumps({'success': False, 'data': 'Error: Body not a valid JSON'}), 400

    nickname = post.get("nickname")
    token = post.get("token")
    # ensure the body is in the expected format
    if len(list(post.keys())) != 2 or nickname is None\
            or token is None:
        return json.dumps({'success': False, 'data': 'Error: Body not in the expected format'}), 400
    # validate the user token with google oauth2
    get_params = {
        'access_token': token
    }
    r = requests.get(url=AUTH_URL, params=get_params)
    data = r.json()

    try:
        google_id = data['id']
    except KeyError:
        # token is invalid
        return json.dumps({'success': False, 'data': 'Error: Token is invalid'}), 400

    print(google_id)
    user = User.query.filter_by(google_id=google_id).first()
    if not(user is None):
        # the user trying to register already has an account
        print("User already exists with that google id")
        return json.dumps({'success': False, 'data': 'Error: Account already registered'}), 400

    constructed_user = User(
        google_id=google_id,
        nickname=nickname,
        join_date=int(time.time()),
    )
    db.session.add(constructed_user)
    db.session.commit()
    response = {
        'success': True,
        'data': constructed_user.serialize()
    }
    return json.dumps(response), 201


@app.route('/api/users/<string:token>/', methods=['GET'])
def get_user_by_token(token):
    # validate the user token with google oauth2
    get_params = {
        'access_token': token
    }
    r = requests.get(url=AUTH_URL, params=get_params)
    data = r.json()

    try:
        google_id = data['id']
    except KeyError:
        # token is invalid
        return json.dumps({'success': False, 'data': 'Error: Token is invalid'}), 400

    user = User.query.filter_by(google_id=google_id).first()
    # ensure a user exists with such google id
    if user is None:
        return json.dumps({'success': False, 'data': 'Error: User does not exist'}), 400
    response = {
        "success": True,
        "data": user.serialize()
    }
    return json.dumps(response), 400

@app.route('/api/users/nickname/', methods=['POST'])
def edit_nickname():
    # ensure the body is valid JSON
    try:
        user = json.loads(request.data)
    except ValueError:
        return json.dumps({'success': False, 'data': 'Error: Body not a valid JSON'}), 400
    nickname = user.get("nickname")
    token = user.get("token")
    # ensure the body is in the expected format
    if len(list(user.keys())) != 2 or nickname is None\
            or token is None:
        return json.dumps({'success': False, 'data': 'Error: Body not in the expected format'}), 400
    # validate the user token with google oauth2
    get_params = {
        'access_token': token
    }
    r = requests.get(url=AUTH_URL, params=get_params)
    data = r.json()

    try:
        google_id = data['id']
    except KeyError:
        # token is invalid
        return json.dumps({'success': False, 'data': 'Error: Token is invalid'}), 400

    print(google_id)
    old_user = User.query.filter_by(google_id=google_id).first()
    if user is None:
        # the user trying to create a post is not stored in our database.
        # i dont think this should ever happen (hopefully ?)
        print("No user exists with that google id")
        return json.dumps({'success': False, 'data': 'Error: User does not exist'}), 400

    constructed_user = User(
        google_id=google_id,
        nickname=nickname,
        join_date=old_user.join_date
    )

    db.session.delete(old_user)
    db.session.add(constructed_user)
    db.session.commit()
    response = {
        'success': True,
        'data': constructed_user.serialize()
    }
    return json.dumps(response), 201

@app.route('/api/users/', methods=['GET'])
def get_all_users():
    users = User.query.all()
    response = {
        'success': True,
        'data': [user.serialize() for user in users]
    }
    return json.dumps(response), 200


@app.route('/api/posts/', methods=['POST'])
def create_a_post():
    # ensure the body is valid JSON
    try:
        post = json.loads(request.data)
    except ValueError:
        return json.dumps({'success': False, 'data': 'Error: Body not a valid JSON'}), 400
    text = post.get("text")
    token = post.get("token")
    # ensure the body is in the expected format
    if len(list(post.keys())) != 2 or text is None\
            or token is None:
        return json.dumps({'success': False, 'data': 'Error: Body not in the expected format'}), 400
    # validate the user token with google oauth2
    get_params = {
        'access_token': token
    }
    r = requests.get(url=AUTH_URL, params=get_params)
    data = r.json()

    try:
        google_id = data['id']
    except KeyError:
        # token is invalid
        return json.dumps({'success': False, 'data': 'Error: Token is invalid'}), 400

    print(google_id)
    user = User.query.filter_by(google_id=google_id).first()
    if user is None:
        # the user trying to create a post is not stored in our database.
        # i dont think this should ever happen (hopefully ?)
        print("No user exists with that google id")
        return json.dumps({'success': False, 'data': 'Error: User does not exist'}), 400

    constructed_post = Post(
        text=text,
        nickname=user.nickname,
        upload_date=int(time.time()),
        user_id=user.id
    )
    db.session.add(constructed_post)
    db.session.commit()
    response = {
        'success': True,
        'data': constructed_post.serialize()
    }
    return json.dumps(response), 201


@app.route('/api/post/<int:post_id>/', methods=['GET'])
def get_post_by_id(post_id):
    post = Post.query.filter_by(id=post_id).first()
    # ensure a post exists with such id
    if post is None:
        return json.dumps({'success': False, 'data': 'Error: Post with id does not exist'}), 400
    response = {
        "success": True,
        "data": post.serialize()
    }
    return json.dumps(response), 400


@app.route('/api/post/<int:post_id>/', methods=['POST'])
def edit_post_by_id(post_id):
    # ensure the body is valid JSON
    try:
        post = json.loads(request.data)
    except ValueError:
        return json.dumps({'success': False, 'data': 'Error: Body not a valid JSON'}), 400
    text = post.get("text")
    token = post.get("token")
    # ensure the body is in the expected format
    if len(list(post.keys())) != 2 or text is None\
            or token is None:
        return json.dumps({'success': False, 'data': 'Error: Body is not in expected format'}), 400
    # validate the user token with google oauth2
    get_params = {
        'access_token': token
    }
    r = requests.get(url=AUTH_URL, params=get_params)
    data = r.json()

    try:
        google_id = data['id']
    except KeyError:
        # token is invalid
        return json.dumps({'success': False, 'data': 'Error: Token is invalid'}), 400

    print(google_id)
    user = User.query.filter_by(google_id=google_id).first()
    if user is None:
        # the user trying to edit a post is not stored in our database.
        # i dont think this should ever happen (hopefully ?)
        print("No user exists with that google id")
        return json.dumps({'success': False, 'data': 'Error: User does not exist'}), 400

    post = Post.query.filter_by(id=post_id).first()
    # ensure a post exists with such id
    if post is None:
        return json.dumps({'success': False, 'data': 'Error: Post with id does not exist'}), 400

    # ensure the post with such id is owned by the user trying to edit it
    if not(post.user_id == user.id):
        return json.dumps({'success': False, 'data': 'Error: User does not own post'}), 400

    post.text = text
    db.session.commit()
    response = {
        'success': True,
        'data': post.serialize()
    }
    return json.dumps(response), 201


@app.route('/api/post/<int:post_id>/token/<string:token>/', methods=['DELETE'])
def delete_post_by_id(post_id, token):
    # validate the user token with google oauth2
    get_params = {
        'access_token': token
    }
    r = requests.get(url=AUTH_URL, params=get_params)
    data = r.json()

    try:
        google_id = data['id']
    except KeyError:
        # token is invalid
        return json.dumps({'success': False, 'data': 'Error: Token is invalid'}), 400

    user = User.query.filter_by(google_id=google_id).first()
    if user is None:
        # the user trying to delete the post is not stored in our database.
        # i dont think this should ever happen (hopefully ?)
        print("No user exists with that google id")
        return json.dumps({'success': False, 'data': 'Error: User does not exist'}), 400

    post = Post.query.filter_by(id=post_id).first()
    # ensure a post exists with such id
    if post is None:
        return json.dumps({'success': False, 'data': 'Error: Post with id does not exist'}), 400

    # ensure the post with such id is owned by the user trying to delete it
    if not(post.user_id == user.id):
        return json.dumps({'success': False, 'data': 'Error: User does not own post'}), 400

    db.session.delete(post)
    db.session.commit()
    response = {
        'success': True,
        'data': post.serialize()
    }
    return json.dumps(response), 201


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
