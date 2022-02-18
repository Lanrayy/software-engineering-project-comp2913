from app import db

#User Database
class user(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(50), unique=True, nullable=False)
    #Cannot be 'type' cause its a key variable. Let users pick 1,2,3 rather than type it in.
    status = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(50), nullable=False)
    card = db.relationship('card_details', backref='user', lazy=True)

    def __repr__(self):
            return f'User <{self.id}|{self.name}|{self.email}|{self.status}>'

#Card_Details Database
class card_details(db.Model):       
    id = db.Column(db.Integer, primary_key=True)
    cardnumber = db.Column(db.String(16), nullable=False)
    expire_date = db.Column(db.String(4), nullable=False)
    cvv = db.Column(db.String(10), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
            return f'Card <{self.id}|{self.cardnumber}|{self.expire_date}|{self.user_id}>'

#-------------------------------------------------------------
#----------------------NOT TESTED-----------------------------
#-------------------------------------------------------------

#Collection_Point Database
class collection_point(db.Model):  
    id = db.Column(db.Integer, primary_key=True)
    location = db.Column(db.String(50), nullable=False)
    num_scooters = db.Column(db.Integer, nullable=False)

class scooter(db.Model): 
    id = db.Column(db.Integer, primary_key=True)
    availability = db.Column(db.Integer, nullable=False)
    collection_id = db.Column(db.Integer, db.ForeignKey('collection_point.id'), nullable=False)

class booking(db.Model):   
    id = db.Column(db.Integer, primary_key=True)
    hire_period = db.Column(db.String(50), nullable=False)
    status = db.Column(db.Integer, nullable=False)
    cost = db.Column(db.Real, nullable=False)
    date_time = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(50), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    scooter_id = db.Column(db.Integer, db.ForeignKey('scooter.id'), nullable=False)
    collection_id = db.Column(db.Integer, db.ForeignKey('collection_point.id'), nullable=False)

class admin(db.Model):  
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(50), nullable=False)



