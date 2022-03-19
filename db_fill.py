from app import app, db, models, bcrypt

#initialise locations
location = models.collection_point(location = 'Trinity Centre', num_scooters = 0)
db.session.add(location)
location = models.collection_point(location = 'Train Station', num_scooters = 0)
db.session.add(location)
location = models.collection_point(location = 'Merrion Centre', num_scooters = 0)
db.session.add(location)
location = models.collection_point(location = 'LRI Hospital', num_scooters = 0)
db.session.add(location)
location = models.collection_point(location = 'UoL Edge Sports Centre', num_scooters = 0)
db.session.add(location)

#initialise pricing
pricing = models.pricing(duration = "1 Hour", price = 10.00)
db.session.add(pricing)
pricing = models.pricing(duration = "4 Hours", price = 39.00)
db.session.add(pricing)
pricing = models.pricing(duration = "1 Day", price = 109.00)
db.session.add(pricing)
pricing = models.pricing(duration = "1 Week", price = 399.00)
db.session.add(pricing)

#initialise scooters
scooter = models.scooter(availability = 1, collection_id = 1)
db.session.add(scooter)
scooter = models.scooter(availability = 1, collection_id = 1)
db.session.add(scooter)
scooter = models.scooter(availability = 1, collection_id = 2)
db.session.add(scooter)
scooter = models.scooter(availability = 1, collection_id = 2)
db.session.add(scooter)

db.session.commit()

#initialise user
user = models.user(name ="Test", email="test@gmail.com", account_type="customer", user_type="default", password=bcrypt.generate_password_hash("test"))
employee = models.user(name ="Employee", email="employee@gmail.com", account_type="employee", user_type="default", password=bcrypt.generate_password_hash("test"))
db.session.add(user)
db.session.add(employee)
db.session.commit()