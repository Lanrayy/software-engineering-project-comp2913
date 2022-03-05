from app import db
from app import app, login_manager
from flask_login import UserMixin
from sqlalchemy.engine import Engine
from sqlalchemy import event
import datetime

#Note:
#Make sure PRAGMA foreign_keys=ON;

#In order to refresh the database delete migrations, pycache, app.db from the main folder (not app):
#	delete -> migrations,pycache,app.db

#In order to create the databases run the following command into the terminal, you should do this at least once:
#	upgrade -> flask db init, flask db migrate, flask db upgrade

#Testing examples through the terminal after calling python :
#>>> from app import db, models


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

#User Database
class user(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(50), unique=True, nullable=False)
    account_type = db.Column(db.String(50), nullable=False) #choices are: customer, employee, manager
    user_type = db.Column(db.String(50), nullable=False) #choices are: default (includes emplyee and managers), senior, and frequent
    password = db.Column(db.String(50), nullable=False)

    card = db.relationship('card_details', uselist=False, backref='user') #one-to-one relation, "If you would want to have a one-to-one relationship you can pass uselist=False to relationship()."
    booking = db.relationship('booking', backref='user', lazy=True)  #one-to-many relation


    def __repr__(self):
        return f'User {self.id} < Name={self.name}| Email={self.email}| Type={self.user_type}| Password={self.password}>' #Password is shown for testing, remove for security later

#Card_Details Database
class card_details(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cardnumber = db.Column(db.String(16), nullable=False)
    expire_date = db.Column(db.String(5), nullable=False) #example : 08/24
    cvv = db.Column(db.String(3), nullable=False)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
            return f'Card {self.id} < CardNumber={self.cardnumber}| ExpireDate={self.expire_date}| User_id={self.user_id}>'


#Collection_Point Database
class collection_point(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    location = db.Column(db.String(50), nullable=False) #Let users pick 1,2,3 rather than type it in. Make integer?
    num_scooters = db.Column(db.Integer, nullable=False)

    scooter = db.relationship('scooter', backref='collection_point', lazy=True)  #one-to-many relation
    booking = db.relationship('booking', backref='collection_point', lazy=True)  #one-to-many relation

    def __repr__(self):
            return f'CollectionPoint {self.id} < Location={self.location}| Number of scooters={self.num_scooters} >'


#Scooter Database
class scooter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    availability = db.Column(db.Integer, nullable=False) #1 is available, 2 is unavailable

    collection_id = db.Column(db.Integer, db.ForeignKey('collection_point.id'), nullable=False)

    booking = db.relationship('booking', backref='scooter', lazy=True)  #one-to-many relation

    def __repr__(self):
            return f'Scooter {self.id} < Availability={self.availability}| Collection_id={self.collection_id} >'

#Booking Database
class booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    duration = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(50), nullable=False) #Let users pick 1,2,3 rather than type it in. Make integer?
    cost = db.Column(db.Float, nullable=False)
    initial_date_time = db.Column(db.DateTime(), nullable=False)
    final_date_time = db.Column(db.DateTime(), nullable=False)
    email = db.Column(db.String(50), nullable=False) #manually link this to the user through the code

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    scooter_id = db.Column(db.Integer, db.ForeignKey('scooter.id'), nullable=False)
    collection_id = db.Column(db.Integer, db.ForeignKey('collection_point.id'), nullable=False)

    def __repr__(self):
            return f'Booking {self.id} < Durationd={self.duration}| Status={self.status}| Cost={self.cost}| Initial Date/Time={self.initial_date_time}| Final Date/Time={self.final_date_time}|Email={self.email}| User_id={self.user_id}| Scooter_id={self.scooter_id}| Collection_id={self.collection_id}>'

#Feedback Database
class feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.String(50), nullable=False)

#Query User_id for login
@login_manager.user_loader
def load_user(user_id):
    return user.query.get(int(user_id)) # get user by their ID
