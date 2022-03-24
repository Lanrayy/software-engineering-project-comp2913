import email
import os
from ssl import SSLSocket
from time import time
import unittest
from datetime import datetime, timedelta
from flask import Flask
from app import app, db, models, bcrypt


class TestCase(unittest.TestCase):
    # Ensure landing page loads correctly
    def test_landing_page_loads(self):
        tester = app.test_client(self)
        response = tester.get('/', content_type='html/text')
        self.assertTrue(b'Learn More' in response.data)

    # Ensure register page loads correctly
    def test_register_page_loads(self):
        tester = app.test_client(self)
        response = tester.get('/register', content_type='html/text')
        self.assertTrue(b'Name' in response.data)

    # Ensure login page loads correctly
    def test_login_page_loads(self):
        tester = app.test_client(self)
        response = tester.get('/login', content_type='html/text')
        self.assertTrue(b'Remember details' in response.data)

    # Ensure Send Feedback page loads correctly
    def test_feedback_page_loads(self):
        tester = app.test_client(self)
        response = tester.get('/send_feedback', content_type='html/text')
        self.assertTrue(b'provide feedback' in response.data)

    # Ensure how it works page loads correctly
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


# Run unit tests
if __name__ == '__main__':
    unittest.main()