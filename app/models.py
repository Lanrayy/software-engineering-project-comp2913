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
    user_type = db.Column(db.String(50), nullable=False) #choices are: default (includes emplyee and managers), senior, student, and frequent, #choices are: default, senior, frequent, student, frequent is automatically given
    password = db.Column(db.String(50), nullable=False)

    card = db.relationship('card_details', uselist=False, backref='user') #one-to-one relation
    booking = db.relationship('booking', backref='user', lazy=True)  #one-to-many relation
    transactions = db.relationship('transactions', backref='user', lazy=True)


    def __repr__(self):
        return f'User {self.id} < Name={self.name}| Email={self.email}| Type={self.user_type}| Password={self.password}>' #Password is shown for testing, remove for security later

#Card_Details Database
class card_details(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    cardnumber = db.Column(db.String(16), nullable=False)
    last_four = db.Column(db.String(4), nullable=False) # last four digits on card
    expiry_date = db.Column(db.Date, nullable=False) #example : 08/24
    cvv = db.Column(db.String(3), nullable=False)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False) #one-to-one relation

    def __repr__(self):
            return f'Card {self.id} < CardNumber={self.cardnumber}| ExpireDate={self.expiry_date}| User_id={self.user_id}>'


#Collection_Point Database
class collection_point(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    location = db.Column(db.String(50), nullable=False) #The name of the location
    num_scooters = db.Column(db.Integer, nullable=False) # NUmber of scooters available at that location

    scooter = db.relationship('scooter', backref='collection_point', lazy=True)  #one-to-many relation
    booking = db.relationship('booking', backref='collection_point', lazy=True)  #one-to-many relation

    def __repr__(self):
            return f'CollectionPoint {self.id} < Location={self.location}| Number of scooters={self.num_scooters} >'



#Booking Database
class booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    duration = db.Column(db.Integer, nullable=False) # Duration of the booking
    status = db.Column(db.String(50), nullable=False) # choices are: active, cancelled, expired, upcoming
    cost = db.Column(db.Float, nullable=False) # the cost of booking this scooter altogether
    initial_date_time = db.Column(db.DateTime(), nullable=False) # start date and time of the booking
    final_date_time = db.Column(db.DateTime(), nullable=False) # end date and time of the booking
    email = db.Column(db.String(50), nullable=False) #manually link this to the user through the code

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    scooter_id = db.Column(db.Integer, db.ForeignKey('scooter.id'), nullable=False)
    collection_id = db.Column(db.Integer, db.ForeignKey('collection_point.id'), nullable=False)

    # relationships
    transactions = db.relationship('transactions', backref='booking', lazy=True)

    def __repr__(self):
            return f'Booking {self.id} < Duration={self.duration}| Status={self.status}| Cost={self.cost}| Initial Date/Time={self.initial_date_time}| Final Date/Time={self.final_date_time}|Email={self.email}| User_id={self.user_id}| Scooter_id={self.scooter_id}| Collection_id={self.collection_id}>'

#Feedback Database
class feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.String(50), nullable=False)
    priority = db.Column(db.Integer, nullable=False) # 0 for low priority, 1 for high
    resolved = db.Column(db.Integer, nullable=False) # 0 for not resolved, 1 for resolved

#Pricing Table
class pricing(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    duration = db.Column(db.String(20), nullable=False) # Options are "1 hour", "4 hours", "1 day", "1 week"
    price = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f'Pricing {self.id} < Duration={self.duration}| Price={self.price}'

#Query User_id for login
@login_manager.user_loader
def load_user(user_id):
    return user.query.get(int(user_id)) # get user by their ID

#Scooter Database
class scooter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    availability = db.Column(db.Integer, nullable=False) #1 is available, 2 is unavailable
    collection_id = db.Column(db.Integer, db.ForeignKey('collection_point.id'), nullable=False)


    booking = db.relationship('booking', backref='scooter', lazy=True)  #one-to-many relation

    def __repr__(self):
            return f'Scooter {self.id} < Availability={self.availability}| Collection_id={self.collection_id} >'

#Transactions database
class transactions(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hire_period = db.Column(db.Integer, nullable=False) # store in hours (1, 4, 24, 168)
    booking_time = db.Column(db.DateTime(), nullable=False) # start date and time
    transaction_cost = db.Column(db.Float, nullable=False) # stores the cost of the transaction

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    booking_id = db.Column(db.Integer, db.ForeignKey('booking.id'))

    def __repr__(self):
            return f'Transaction {self.id} < Hire period={self.hire_period}| Booking time={self.booking_time} | user_id={self.user_id} | booking={self.booking_id} >'
