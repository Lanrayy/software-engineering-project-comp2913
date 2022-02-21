from app import db
from app import app, login_manager
from flask_login import UserMixin

#User Database
class user(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(50), unique=True, nullable=False)
    status = db.Column(db.String(50), nullable=False) #Cannot be 'type' cause its a key variable. Let users pick 1,2,3 rather than type it in. Make integer?
    password = db.Column(db.String(50), nullable=False)

    card = db.relationship('card_details', backref='user', lazy=True) #one-to-one relation, "If you would want to have a one-to-one relationship you can pass uselist=False to relationship()."
    booking = db.relationship('booking', uselist=False, backref='user')  #one-to-many relation


    def __repr__(self):
            return f'User {self.id} < Name={self.name}| Email={self.email}| Status={self.status}| Password={self.password}>' #Password is shown for testing, remove for security later

#Card_Details Database
class card_details(db.Model):       
    id = db.Column(db.Integer, primary_key=True)
    cardnumber = db.Column(db.String(16), nullable=False)
    expire_date = db.Column(db.String(4), nullable=False)
    cvv = db.Column(db.String(10), nullable=False)

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
    availability = db.Column(db.Integer, nullable=False)

    collection_id = db.Column(db.Integer, db.ForeignKey('collection_point.id'), nullable=False)

    booking = db.relationship('booking', backref='scooter', lazy=True)  #one-to-many relation

    def __repr__(self):
            return f'Scooter {self.id} < Availability={self.availability}| Collection_id={self.collection_id} >'

#Booking Database
class booking(db.Model):   
    id = db.Column(db.Integer, primary_key=True)
    hire_period = db.Column(db.String(50), nullable=False)
    status = db.Column(db.Integer, nullable=False) #Let users pick 1,2,3 rather than type it in. Make integer?
    cost = db.Column(db.Float, nullable=False)
    date_time = db.Column(db.String(50), nullable=False) #Date and time?
    email = db.Column(db.String(50), nullable=False) #manually link this to the user

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    scooter_id = db.Column(db.Integer, db.ForeignKey('scooter.id'), nullable=False)
    collection_id = db.Column(db.Integer, db.ForeignKey('collection_point.id'), nullable=False)

    def __repr__(self):
            return f'Booking {self.id} < Hire_Period={self.hire_period}| Status={self.status}| Cost={self.cost}| Date/Time={self.date_time}| Email={self.email}| User_id={self.user_id}| Scooter_id={self.scooter_id}| Collection_id={self.collection_id}>'


#Admin Database
class admin(db.Model):  
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(50), unique=True, nullable=False) #Added <unique=True>
    password = db.Column(db.String(50), nullable=False)

    def __repr__(self):
            return f'Admin {self.id} < Name={self.name}| Email={self.email}| Password={self.password}>' #Password is shown for testing, remove for security later
