import os

basedir = os.path.abspath(os.path.dirname(__file__))
SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'app.db')
SQLALCHEMY_TRACK_MODIFICATIONS = True   

WTF_CSRF_ENABLED = True
MAIL_SERVER = 'smtp.gmail.com'
MAIL_PORT = 465
MAIL_USE_SSL = True
MAIL_USERNAME = 'scootersleeds@gmail.com'
MAIL_PASSWORD = 'scooters123'

# You should change this
SECRET_KEY = 'another-secret-secret'




