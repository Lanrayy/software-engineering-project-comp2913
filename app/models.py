#To refresh Database:
#delete -> migrations,pycache,app.db
#upgrade -> flask db init, flask db migrate, flask db upgrade.

from app import db
from app import app, login_manager
from flask_login import UserMixin

#User Database
class user(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(50), unique=True, nullable=False)
    #Cannot be 'type' cause its a key variable. Let users pick 1,2,3 rather than type it in.
    status = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(50), nullable=False)
    card = db.relationship('card_details', backref='user', lazy=True)

    def __repr__(self):
        return f'User <{self.id}|{self.name}|{self.email}|{self.status}>'

    def isUser(self):
        return True

    def isAdmin(self):
        return False

#Card_Details Database
class card_details(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cardnumber = db.Column(db.String(16), nullable=False)
    expire_date = db.Column(db.String(4), nullable=False)
    cvv = db.Column(db.String(10), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
            return f'Card <{self.id}|{self.cardnumber}|{self.expire_date}|{self.user_id}>'

#Query User_id for login
@login_manager.user_loader
def load_user(user_id):
    return user.query.get(int(user_id)) # get user by their ID
