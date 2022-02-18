from app import db


class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True, unique=True)
    name = db.Column(db.String(70))
    email = db.Column(db.String(100))
    status = db.Column(db.Integer)
    password = db.Column(db.String(30))
    card_details = db.relationship('CardDetails', backref='user', uselist=False)
    bookings = db.relationship('Booking', backref='user')


class CardDetails(db.Model):
    __tablename__ = 'card_details'
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    card_number = db.Column(db.String(16))
    expiry_date = db.Column(db.String(5))
    cvv = db.Column(db.String(3))


class CollectionPoint(db.Model):
    __tablename__ = 'collection_point'
    id = db.Column(db.Integer, primary_key=True, unique=True)
    location = db.Column(db.String(25), unique=True)
    num_scooters = db.Column(db.Integer)
    scooters = db.relationship('Scooter', backref='collection_point')
    bookings = db.relationship('Booking', backref='collection_point')


class Scooter(db.Model):
    __tablename__ = 'scooter'
    id = db.Column(db.Integer, primary_key=True, unique=True)
    availability = db.Column(db.Integer)
    collection_id = db.Column(db.Integer, db.ForeignKey('collection_point.id'))
    bookings = db.relationship('Booking', backref='scooter')


class Booking(db.Model):
    __tablename__ = 'booking'
    id = db.Column(db.Integer, primary_key=True, unique=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    scooter_id = db.Column(db.Integer, db.ForeignKey('scooter.id'))
    collection_id = db.column(db.Integer, db.ForeignKey('collection_point.id'))
    hire_period = db.Column(db.String(6))
    status = db.Column(db.Integer)
    cost = db.Column(db.Float)
    date_time = db.Column(db.DateTime)
    email = db.Column(db.String(100))


class Admin(db.Model):
    __tablename__ = 'admin'
    id = db.Column(db.Integer, primary_key=True, unique=True)
    name = db.Column(db.String(70))
    email = db.Column(db.String(100))
    password = db.Column(db.String(30))
