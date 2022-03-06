from app import app, db
import unittest
class FlaskTestCase(unittest.TestCase):

    # Ensure flask was set up correctly
    def test_index(self):
        tester = app.test_client(self)
        response = tester.get('/login', content_type='html/text')
        self.assertEqual(response.status_code, 200)

    # Ensure landing page loads correctly
    def test_landing_page_loads(self):
        tester = app.test_client(self)
        response = tester.get('/', content_type='html/text')
        self.assertTrue(b'Learn More' in response.data)

    # Ensure register page loads correctly
    def testing_register_page_loads(self):
        tester = app.test_client(self)
        response = tester.get('/register', content_type='html/text')
        self.assertTrue(b'Name' in response.data)
    
    # Ensure login page loads correctly
    def testing_login_page_loads(self):
        tester = app.test_client(self)
        response = tester.get('/login', content_type='html/text')
        self.assertTrue(b'Remember details' in response.data)

    # Ensure Send Feedback page loads correctly
    def testing_feedback_page_loads(self):
        tester = app.test_client(self)
        response = tester.get('/send_feedback', content_type='html/text')
        self.assertTrue(b'Submit Feedback' in response.data)

    # Ensure how it works page loads correctly
    def testing_info_page_loads(self):
        tester = app.test_client(self)
        response = tester.get('/info', content_type='html/text')
        self.assertTrue(b'Locations' in response.data)


    # ensure that sign up behaves correctly given the correct credentials
    def test_correct_signup(self):
        
        tester = app.test_client(self)
        response = tester.post('/register', 
                                data=dict(name="user1",
                                email="user1@demo.com", 
                                password1="user1",
                                password2="user1"), 
                                follow_redirects=True)
        #self.assertIn(b'Remember details', response.data)

    # ensure that sign up behaves correctly given the INCORRECT credentials
    def test_incorrect_signup(self):
        
        tester = app.test_client(self)
        response = tester.post('/register', 
                                data=dict(email="jeodn@demo.com", 
                                password="lwidm"), 
                                follow_redirects=True)
        self.assertIn(b'Name', response.data)

    # ensure that login behaves correctly given the correct credentials
    def test_correct_login(self):
        
        tester = app.test_client(self)
        response = tester.post('/login', 
                                data=dict(email="testuser@demo.com", 
                                password="testing"), 
                                follow_redirects=True)
        self.assertIn(b'View Profile', response.data)
    
    # Ensure sign up behaves correctly given the INCORRECT credentials
    def test_incorrect_login(self):
        
        tester = app.test_client(self)
        response = tester.post('/login', 
                                data=dict(email="notuser@demo.com", 
                                password="wdsd"), 
                                follow_redirects=True)
        self.assertIn(b'Login unsuccessful', response.data)


if __name__ == '__main__':
    unittest.main()