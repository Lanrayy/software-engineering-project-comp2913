import os

basedir = os.path.abspath(os.path.dirname(__file__))
SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'app.db')
SQLALCHEMY_TRACK_MODIFICATIONS = True   

WTF_CSRF_ENABLED = True

# You should change this
SECRET_KEY = 'another-secret-secret'




