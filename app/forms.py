from flask_wtf import FlaskForm
from wtforms import IntegerField
from wtforms import StringField
from wtforms import TextAreaField
from wtforms import DateField
from wtforms import SubmitField
from wtforms import PasswordField
from wtforms import BooleanField
from wtforms import ValidationError
from wtforms import SelectField
from app import models

from wtforms.validators import InputRequired, EqualTo, Length, Email

# sign up form
class SignUpForm(FlaskForm):
    name = StringField('name', validators=[InputRequired()])
    #username = StringField('username', validators=[InputRequired(), Length(min=2, max=20)])
    email = StringField('email', validators=[InputRequired(), Email()])
    password1 = PasswordField('password1', validators=[InputRequired()])
    password2 = PasswordField('password2', validators=[EqualTo('password1'), InputRequired()]) #makes sure password1 equals password2

    # validate username
    def validate_email(self, email) :

        # get first instance of this username in the database
        # changer "User" to model name
        user = models.user.query.filter_by(email = email.data).first()

        # if username found in database, raise error
        if user:
            raise ValidationError('email is already taken')

# login form
class LoginForm(FlaskForm):
    email = StringField('email', validators=[InputRequired()])
    password = PasswordField('password', validators=[InputRequired()])
    remember = BooleanField('Remember Me')

# user booking form
class BookingForm(FlaskForm):
    scooter_id = SelectField('scooter_id', choices=[('1', 'Select Scooter ID')], validators=[InputRequired()])
    # location_id = SelectField('location_id', choices=[('1', 'Trinity Centre'), ('2', 'Train Station'), ('3', 'Merrion Centre'),
    #     ('4', 'LRI Hospital'), ('5', 'UoL Edge Sports Centre')], validators=[InputRequired()])
    hire_period = SelectField('hire_period', choices = [('1', '1 Hour'), ('2', '4 Hours'), ('3', '1 Day'), ('4', '1 Week')], validators=[InputRequired()])
    cvv = IntegerField('cvv', validators=[InputRequired(), Length(3)])

class UnsavedBookingForm(FlaskForm):
    scooter_id = SelectField('scooter_id', choices=[('1', 'Select Scooter ID')], validators=[InputRequired()])
    # location_id = SelectField('location_id', choices=[('1', 'Trinity Centre'), ('2', 'Train Station'), ('3', 'Merrion Centre'),
    #     ('4', 'LRI Hospital'), ('5', 'UoL Edge Sports Centre')], validators=[InputRequired()])
    hire_period = SelectField('hire_period', choices = [('1', '1 Hour'), ('2', '4 Hours'), ('3', '1 Day'), ('4', '1 Week')], validators=[InputRequired()])
    card_number = IntegerField('card_number', validators=[InputRequired(), Length(16)])
    name = StringField('name', validators=[InputRequired()])
    expiry = DateField('expiry', validators=[InputRequired()])
    cvv = IntegerField('cvv', validators=[InputRequired(), Length(3)])
    save_card_details = BooleanField('save_card_details')

# admin booking form
class AdminBookingForm(FlaskForm):
    scooter_id = SelectField('scooter_id', choices=[('1', 'Select Scooter ID')], validators=[InputRequired()])
    # location_id = SelectField('location_id', choices=[('1', 'Trinity Centre'), ('2', 'Train Station'), ('3', 'Merrion Centre'),
    #     ('4', 'LRI Hospital'), ('5', 'UoL Edge Sports Centre')], validators=[InputRequired()])
    hire_period = SelectField('hire_period', choices = [('1', '1 Hour'), ('2', '4 Hours'), ('3', '1 Day'), ('4', '1 Week')], validators=[InputRequired()])
    email = StringField('email', validators=[InputRequired(), Email()])
    card_number = IntegerField('card_number', validators=[InputRequired(), Length(16)])
    name = StringField('name', validators=[InputRequired()])
    expiry = DateField('expiry', validators=[InputRequired()])
    cvv = IntegerField('cvv', validators=[InputRequired(), Length(3)])
    
# configure scooter form
class ConfigureScooterForm(FlaskForm):
    scooter_id = SelectField('scooter_id', choices=[('1', 'Select Scooter ID')], validators=[InputRequired()])
    availability = SelectField('availability', choices = [('1', 'Available'), ('2', 'Unavailable')], validators=[InputRequired()])
    location_id = SelectField('location_id', choices=[('1', 'Trinity Centre'), ('2', 'Train Station'), ('3', 'Merrion Centre'),
        ('4', 'LRI Hospital'), ('5', 'UoL Edge Sports Centre')], validators=[InputRequired()])

# feedback form
class FeedbackForm(FlaskForm):
    feedback = TextAreaField('feedback')


