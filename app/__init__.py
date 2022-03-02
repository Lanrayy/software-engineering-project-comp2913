from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_bcrypt import Bcrypt

#global variables
app = Flask(__name__)
bcrypt = Bcrypt(app)
app.config.from_object('config')
db = SQLAlchemy(app)

# for user authentication
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

migrate = Migrate(app, db)

from app import views, models
