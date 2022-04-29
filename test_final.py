import email
import os
from time import time
import unittest
from datetime import datetime, timedelta
from flask import Flask
from app import app, db, models, bcrypt


class TestCase(unittest.TestCase):
    def setUp(self):

        # Create new database for testing
        app.config.from_object('config')
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        #the basedir lines could be added like the original db
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
        self.app = app.test_client()
        db.create_all()

        # Populate database
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
        user = models.user(name ="Normal User", email="test@gmail.com", account_type="customer", user_type="default", password=bcrypt.generate_password_hash("test"))
        student = models.user(name ="Student", email="student@gmail.com", account_type="customer", user_type="student", password=bcrypt.generate_password_hash("test"))
        senior = models.user(name ="Senior", email="senior@gmail.com", account_type="customer", user_type="senior", password=bcrypt.generate_password_hash("test"))
        employee = models.user(name ="Employee", email="employee@gmail.com", account_type="employee", user_type="default", password=bcrypt.generate_password_hash("test"))
        manager = models.user(name ="Manager", email="manager@gmail.com", account_type="manager", user_type="default", password=bcrypt.generate_password_hash("test"))
        db.session.add(user)
        db.session.add(employee)
        db.session.add(manager)
        db.session.add(student)
        db.session.add(senior)
        db.session.commit()

    # Tests

#--------------------------------------------------------------------------------
#                               Not Signed In Pages
#--------------------------------------------------------------------------------
    # Ensure landing page loads correctly
    def test_landing_page_loads(self):
        tester = app.test_client(self)
        response = tester.get('/', content_type='html/text')
        self.assertTrue(b'Find out more' in response.data)

    # Ensure register page loads correctly
    def test_register_page_loads(self):
        tester = app.test_client(self)
        response = tester.get('/register', content_type='html/text')
        self.assertTrue(b'Name' in response.data)

    # Ensure login page loads correctly
    def test_login_page_loads(self):
        tester = app.test_client(self)
        response = tester.get('/login', content_type='html/text')
        self.assertTrue(b"Don't have an account?" in response.data)

    # Ensure Send Feedback page loads correctly
    def test_feedback_page_loads(self):
        tester = app.test_client(self)
        response = tester.get('/send_feedback', content_type='html/text')
        self.assertTrue(b'provide feedback' in response.data)

    # Ensure how it works page loads correctly
    def test_info_page_loads(self):
        tester = app.test_client(self)
        response = tester.get('/info', content_type='html/text')
        self.assertTrue(b'Locations' in response.data)


    def test_correct_registration(self):
        tester = app.test_client(self)
        response = tester.post('/register',
                                data=dict(name="userX",
                                email="userx@gmail.com",
                                password1="password",
                                password2="password",
                                user_type="default"),
                                follow_redirects=True)
        self.assertIn(b'Account Created!', response.data)


    # Ensure login does not work with incorrect credentials
    def test_incorrect_login(self):
        tester = app.test_client(self)
        response = tester.post('/login',
                                data=dict(email="test@gmail.com",
                                password=("notpassword")),
                                follow_redirects=True)
        self.assertIn(b'Login unsuccessful', response.data)

    # Ensure login works with correct credentials
    def test_correct_login(self):
        tester = app.test_client(self)
        response = tester.post('/login',
                                data=dict(email="test@gmail.com",
                                password=("test")),
                                follow_redirects=True)
        self.assertIn(b'Login Successful!', response.data)

#--------------------------------------------------------------------------------
#                               User Pages
#--------------------------------------------------------------------------------
    def test_user_dashboard_page_loads(self):
        tester = app.test_client(self)

        # Log in first
        tester.post('/login',
                    data=dict(email="test@gmail.com",
                    password=("test")),
                    follow_redirects=True)
        response = tester.get('/user_dashboard', content_type='html/text')
        self.assertTrue(b'.sctr works for your wellbeing' in response.data)

    def test_user_booking_page_loads(self):
        tester = app.test_client(self)

        # Log in first
        tester.post('/login',
                    data=dict(email="test@gmail.com",
                    password=("test")),
                    follow_redirects=True)
        response = tester.get('/booking1', content_type='html/text')
        self.assertTrue(b'Choose a Collection Point' in response.data)

    def test_user_feedback_page_loads(self):
        tester = app.test_client(self)

        # Log in first
        tester.post('/login',
                    data=dict(email="test@gmail.com",
                    password=("test")),
                    follow_redirects=True)
        response = tester.get('/send_feedback', content_type='html/text')
        self.assertTrue(b'Please provide feedback' in response.data)
    
    def test_user_profile_page_loads(self):
        tester = app.test_client(self)

        # Log in first
        tester.post('/login',
                    data=dict(email="test@gmail.com",
                    password=("test")),
                    follow_redirects=True)
        response = tester.get('/profile', content_type='html/text')
        self.assertTrue(b'User Details' in response.data)
#--------------------------------------------------------------------------------
#                               Admin Pages
#--------------------------------------------------------------------------------
    def test_admin_dashboard_page_loads(self):
        tester = app.test_client(self)

        # Log in first
        tester.post('/login',
                    data=dict(email="employee@gmail.com",
                    password=("test")),
                    follow_redirects=True)
        response = tester.get('/admin_dashboard', content_type='html/text')
        self.assertTrue(b'Welcome,' in response.data)

    def test_view_scooters_page_loads(self):
        tester = app.test_client(self)
        # Log in first
        tester.post('/login',
                    data=dict(email="employee@gmail.com",
                    password=("test")),
                    follow_redirects=True)
        response = tester.get('/view_scooters', content_type='html/text')
        self.assertTrue(b'View Scooter Details and Availability' in response.data)
    
    def test_review_feedback_page_loads(self):
        tester = app.test_client(self)
        # Log in first
        tester.post('/login',
                    data=dict(email="employee@gmail.com",
                    password=("test")),
                    follow_redirects=True)
        response = tester.get('/review_feedback', content_type='html/text')
        self.assertTrue(b'Feedback Reports' in response.data)

    # Ensure login does not work with incorrect credentials
    def test_configure_prices(self):
        tester = app.test_client(self)

        # Log in first
        tester.post('/login',
                    data=dict(email="manager@gmail.com",
                    password=("test")),
                    follow_redirects=True)

        # Fill in booking form
        configure = tester.post('/configure_costs',
                    data=dict(duration='3',
                    price=50.0),
                    follow_redirects=True)


        self.assertIn(b'Price updated', configure.data)
    

#--------------------------------------------------------------------------------
#                               Booking
#--------------------------------------------------------------------------------
    # Ensure correct bookings are made
    def test_booking_is_made(self):
        tester = app.test_client(self)

        # Log in first
        tester.post('/login',
                    data=dict(email="test@gmail.com",
                    password=("test")),
                    follow_redirects=True)

        # Fill in booking form
        tester.post('/booking1',
                    data=dict(scooter_id= '2',
                    location_id='1',
                    hire_period='3',
                    start_date=datetime.utcnow() + timedelta(minutes=2)),
                    follow_redirects=True)

        # Fill in card details
        booking = tester.post('/card',
                    data=dict(card_number="1010101010101010",
                    name="test",
                    expiry="12-3000",
                    cvv="123",
                    save_card_details=True),
                    follow_redirects=True)

        self.assertIn(b'Check your inbox for an email confirming your booking.', booking.data)
    

    def test_used_scooter_not_booked(self):
        tester = app.test_client(self)

        # Log in first
        tester.post('/login',
                    data=dict(email="test@gmail.com",
                    password=("test")),
                    follow_redirects=True)

        # Fill in booking form
        tester.post('/booking1',
                    data=dict(scooter_id= '2',
                    location_id='1',
                    hire_period='3',
                    start_date=datetime.utcnow() + timedelta(minutes=2)),
                    follow_redirects=True)

        # Fill in card details
        tester.post('/card',
                    data=dict(card_number="1010101010101010",
                    name="test",
                    expiry="12-3000",
                    cvv="123",
                    save_card_details=True),
                    follow_redirects=True)

        booking = tester.post('/booking1',
                    data=dict(scooter_id= '2',
                    location_id='1',
                    hire_period='3',
                    start_date=datetime.utcnow() + timedelta(minutes=2)),
                    follow_redirects=True)

        self.assertIn(b'The scooter is unavailable for that start time', booking.data)

    def test_extend_booking(self):
        tester = app.test_client(self)

        # Log in first
        tester.post('/login',
                    data=dict(email="test@gmail.com",
                    password=("test")),
                    follow_redirects=True)

        # Fill in booking form
        tester.post('/booking1',
                    data=dict(scooter_id= '2',
                    location_id='1',
                    hire_period='3',
                    start_date=datetime.utcnow()),
                    follow_redirects=True)

        # Fill in card details
        tester.post('/card',
                    data=dict(card_number="1010101010101010",
                    name="test",
                    expiry="12-3000",
                    cvv="123",
                    save_card_details=True),
                    follow_redirects=True)

        booking = tester.post('/extend_booking',
                    data=dict(hire_period='2'),
                    follow_redirects=True)

        self.assertIn(b'Booking Extension Successful!', booking.data)

    def test_cancel_booking(self):
        tester = app.test_client(self)

        # Log in first
        tester.post('/login',
                    data=dict(email="test@gmail.com",
                    password=("test")),
                    follow_redirects=True)

        # Fill in booking form
        tester.post('/booking1',
                    data=dict(scooter_id= '2',
                    location_id='1',
                    hire_period='3',
                    start_date=datetime.utcnow() + timedelta(hours=1)),
                    follow_redirects=True)

        # Fill in card details
        tester.post('/card',
                    data=dict(card_number="1010101010101010",
                    name="test",
                    expiry="12-3000",
                    cvv="123",
                    save_card_details=True),
                    follow_redirects=True)

        booking = tester.post('/cancel_booking',
                    follow_redirects=True)

        self.assertIn(b'Booking successfully cancelled!', booking.data)

    
    # Ensure login does not work with incorrect credentials
    def test_store_card_details(self):
        tester = app.test_client(self)

        # Log in first
        tester.post('/login',
                    data=dict(email="test@gmail.com",
                    password=("test")),
                    follow_redirects=True)

        # Fill in booking form
        tester.post('/booking1',
                    data=dict(scooter_id= '2',
                    location_id='1',
                    hire_period='3',
                    start_date=datetime.utcnow() + timedelta(minutes=2)),
                    follow_redirects=True)

        # Fill in card details
        booking = tester.post('/card',
                    data=dict(card_number="1010101010101010",
                    name="test",
                    expiry="12-3000",
                    cvv="123",
                    save_card_details=True),
                    follow_redirects=True)

        self.assertIn(b'Card details saved', booking.data)

#--------------------------------------------------------------------------------
#                               Feedback Pages
#--------------------------------------------------------------------------------
    def test_feedback_is_submitted(self):
        tester = app.test_client(self)
        response = tester.post('/send_feedback',
                                data=dict(feedback= 'this is a test'),
                                follow_redirects=True)
        self.assertIn(b'Feedback Submitted', response.data)


    # Delete database created
    def tearDown(self):
        db.session.remove()
        db.drop_all()

# Run unit tests
if __name__ == '__main__':
    unittest.main()
