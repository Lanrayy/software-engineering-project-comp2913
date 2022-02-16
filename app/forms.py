from flask_wtf import Form

from wtforms import IntegerField
from wtforms import StringField
from wtforms import TextAreaField
from wtforms import DateField
from wtforms import SubmitField
from wtforms import PasswordField
from wtforms import BooleanField
from wtforms import ValidationError
from wtforms import SelectField

from wtforms.validators import InputRequired, EqualTo, Length, Email

# sign up form
class SignUpForm(Form):
    name = StringField('name', validators=[InputRequired()])
    username = StringField('username', validators=[InputRequired(), Length(min=2, max=20)])
    email = StringField('email', validators=[InputRequired(), Email()])
    password1 = PasswordField('password1', validators=[InputRequired()])
    password2 = PasswordField('password2', validators=[EqualTo('password1'), InputRequired()]) #makes sure password1 equals password2

    # validating that the username is unique
    # def validate_username(self, username):
    #     user = models.Users.query.filter_by(username=username.data).first()
    #     # if a username if found raise an error
    #     if user:
    #         raise ValidationError('Username taken! Please choose a different username')

# login form
class LoginForm(Form):
    username = StringField('username', validators=[InputRequired()])
    password = PasswordField('password', validators=[InputRequired()])
    remember = BooleanField('Remember Me')

# card details
class CardDetailsForm(Form):
    name = StringField('name', validators=[InputRequired()])
    card_number = IntegerField('card_number', validators=[InputRequired(), Length(16)])
    expiry = DateField('expiry', validators=[InputRequired()])

# booking details
class BookingForm(Form):
    scooter_id = SelectField('scooter_id', choices=[('1', 'Select Scooter ID')])
    location_id = SelectField('location_id', choices=[('1', 'Trinity Centre'), ('2', 'Train Station'), ('3', 'Merrion Centre'),
        ('4', 'LRI Hospital'), ('5', 'UoL Edge Sports Centre')])
    hire_period = SelectField('hire_period', choices = [('1', '1 Hour'), ('2', '4 Hours'), ('3', '1 Day'), ('4', '1 Week')])