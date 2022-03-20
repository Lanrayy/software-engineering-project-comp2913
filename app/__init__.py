from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from flask_bcrypt import Bcrypt
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView

#global variables
app = Flask(__name__)
bcrypt = Bcrypt(app)
app.config.from_object('config')
db = SQLAlchemy(app)
mail = Mail(app)

# for user authentication
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

migrate = Migrate(app, db)

from app import views, models

# flask admin
admin = Admin(app)

admin.add_view(ModelView(models.user, db.session))
admin.add_view(ModelView(models.card_details, db.session))
admin.add_view(ModelView(models.collection_point, db.session))
admin.add_view(ModelView(models.booking, db.session))
admin.add_view(ModelView(models.feedback, db.session))
admin.add_view(ModelView(models.pricing, db.session))
admin.add_view(ModelView(models.scooter, db.session))
admin.add_view(ModelView(models.transactions, db.session))


