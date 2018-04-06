from app import mongo, login
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


class User(UserMixin):
    username = ''
    password_hash = ''
    id = ''

    def __init__(self, user=None):
        super(UserMixin, self).__init__()
        if user is not None:
            self.username = user.get('username')
            self.password_hash = user['password_hash']
            self.id = self.username
            self.enabled = user.get('enabled', False)
            self.admin = user.get('admin', False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def request_registration(self):
        mongo.db.user_requests.insert({
            'username': self.username,
            'password_hash': self.password_hash
            })

    def enable(self):
        if not self.enabled:
            self.enabled = True
            mongo.db.users.update_one({'username': self.username}, {"$set": {'enabled': True}})

    def disable(self):
        if self.enabled:
            self.enabled = False
            mongo.db.users.update_one({'username': self.username}, {"$set": {'enabled': False}})

    def delete(self):
        mongo.db.users.delete_one({'username': self.username})

    def __repr__(self):
        return '<User> {}'.format(self.username)

    @staticmethod
    def find_user(username):
        user = mongo.db.users.find_one({'username': username})
        if not user:
            return None
        return User(user)

    @staticmethod
    def find_user_request(username):
        user = mongo.db.user_requests.find_one({'username': username})
        if not user:
            return None
        return User(user)

    @staticmethod
    def get_list_user_requests():
        return mongo.db.user_requests.find()

    @staticmethod
    def get_list_users():
        return mongo.db.users.find()

    @staticmethod
    def accept_request(request):
        mongo.db.users.insert_one({
            'username': request.username,
            'password_hash': request.password_hash,
            'enabled': 'True',
            'admin': 'False'
            })
        User.delete_request(request)

    @staticmethod
    def delete_request(request):
        mongo.db.user_requests.delete_one({'username': request.username})


@login.user_loader
def login_user(username):
    u=User.find_user(username)
    if u.enabled:
        return u
    else:
        return None


