from email import message
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
from wtforms import FloatField
from wtforms import DateTimeField
from app import models
from wtforms.validators import InputRequired, EqualTo, Length, Email, Regexp, NumberRange
from flask import flash
from datetime import datetime, timedelta
import calendar

# sign up form
class SignUpForm(FlaskForm):
    name = StringField('name', validators=[InputRequired(), Regexp("^([^0-9]*)$", message = "Name cannot contain digits")])
    #username = StringField('username', validators=[InputRequired(), Length(min=2, max=20)])
    email = StringField('email', validators=[InputRequired(), Email()])
    password1 = PasswordField('password1', validators=[InputRequired()])
    password2 = PasswordField('password2', validators=[EqualTo('password1'), InputRequired()]) #makes sure password1 equals password2
    user_type = SelectField('user_type', choices = [('default', 'default'), ('senior', 'senior'), ('student', 'student')], validators=[InputRequired()])

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
class UserBookingForm(FlaskForm):
    scooter_id = SelectField('scooter_id', choices=[])
    location_id = SelectField('location_id', choices=[('1', 'Trinity Centre'), ('2', 'Train Station'), ('3', 'Merrion Centre'),
                                                      ('4', 'LRI Hospital'), ('5', 'UoL Edge Sports Centre')], validators=[InputRequired()])
    hire_period = SelectField('hire_period', choices = [('1', '1 Hour'), ('2', '4 Hours'), ('3', '1 Day'), ('4', '1 Week')], validators=[InputRequired()])
    start_date = DateTimeField('start_date', format = '%d-%m-%Y %H:%M', validators=[InputRequired()])
    #cvv = IntegerField('cvv', validators=[InputRequired(), Length(3)])



# card form
class CardForm(FlaskForm):
    card_number = StringField('card_number', validators=[InputRequired(), Regexp("(^[0-9]*)$", message = "Card Number must be a number"), Length(min=16, max=16, message="Card number must be 16 characters")])
    name = StringField('name', validators=[InputRequired()])
    # expiry = DateField('expiry', format= '%m-%Y', validators=[InputRequired()])
    expiry = DateTimeField('expiry', format='%m-%Y', validators=[InputRequired()]) #changed to DateTimeField asking for month then year input
    cvv = StringField('cvv', validators=[InputRequired(), Regexp("(^[0-9]*)$", message = "cvv must be a number"), Length(min=3, max=3, message="cvv must be 3 characters")])
    save_card_details = BooleanField('save_card_details')

    def validate_expiry(self, expiry): # cards expire on the last day of the month
        today = datetime.utcnow()
        if(expiry.data is None):
            raise ValidationError('Expiry date is invalid!')

        # get the last day of current month and the last day of the card expiry month
        last_day_of_current_month = today.replace(day = calendar.monthrange(today.year, today.month)[1])
        last_day_of_card_month = expiry.data.replace(day = calendar.monthrange(expiry.data.year, expiry.data.month)[1])
        
        if(last_day_of_card_month.date() < last_day_of_current_month.date()):
            raise ValidationError('Expiry date is invalid! Card is expired!')

# admin booking form
class AdminBookingForm(FlaskForm):
    scooter_id = SelectField('scooter_id', choices=[])
    location_id = SelectField('location_id', choices=[('1', 'Trinity Centre'), ('2', 'Train Station'), ('3', 'Merrion Centre'),
                                                      ('4', 'LRI Hospital'), ('5', 'UoL Edge Sports Centre')], validators=[InputRequired()])
    hire_period = SelectField('hire_period', choices = [('1', '1 Hour'), ('2', '4 Hours'), ('3', '1 Day'), ('4', '1 Week')], validators=[InputRequired()])
    start_date = DateTimeField('start_date', format = '%d-%m-%Y %H:%M', validators=[InputRequired()])
    email = StringField('email', validators=[InputRequired(), Email()])
    #cvv = IntegerField('cvv', validators=[InputRequired(), Length(3)])


# extend booking form
class ExtendBookingForm(FlaskForm):
    hire_period = SelectField('hire_period', choices = [('1', '1 Hour'), ('2', '4 Hours'), ('3', '1 Day'), ('4', '1 Week')], validators=[InputRequired()])


# configure scooter form
class ConfigureScooterForm(FlaskForm):
    scooter_id = SelectField('scooter_id', choices=[('1', 'Select Scooter ID')], validators=[InputRequired()])
    availability = SelectField('availability', choices = [('1', 'Available'), ('2', 'Unavailable')], validators=[InputRequired()],coerce=int)
    location_id = SelectField('location_id', choices=[('1', 'Trinity Centre'), ('2', 'Train Station'), ('3', 'Merrion Centre'),
        ('4', 'LRI Hospital'), ('5', 'UoL Edge Sports Centre')], validators=[InputRequired()], coerce=int)


class AddScooterForm(FlaskForm):
    availability = SelectField('availability', choices = [(1, 'Available'), (2, 'Unavailable')], validators=[InputRequired()])
    location_id = SelectField('location_id', choices=[(1, 'Trinity Centre'), (2, 'Train Station'), (3, 'Merrion Centre'),
        (4, 'LRI Hospital'), (5, 'UoL Edge Sports Centre')], validators=[InputRequired()])


# feedback form
class FeedbackForm(FlaskForm):
    feedback = TextAreaField('feedback', validators=[InputRequired()])


# edit feedback form
class EditFeedbackForm(FlaskForm):
    # The only fields needed in form are priority and resolve
    priority = BooleanField()
    resolve = BooleanField()


# configure prices form
class PricesForm(FlaskForm):
    duration = SelectField('duration', choices=[('1', '1 hour'), ('2', '4 hour'), ('3', '1 day'), ('4', '1 week')], validators=[InputRequired()])
    price = FloatField('price', validators=[InputRequired()])

    def validate_price(self, price):
        # if price is negative or 0
        if price.data <= 0:
            raise ValidationError('please input a positive value for price')
