from flask import render_template, flash, jsonify
from app import app, db, bcrypt, models
from .forms import LoginForm, SignUpForm, BookingForm
from flask import request, redirect, url_for, abort, make_response
from flask_login import login_user, current_user, logout_user, login_required
import os
from datetime import datetime

#Unregistered user exclusive pages
@app.route('/')
def index():
    return render_template('landing_page.html',
                            title='Home')


@app.route('/info')
def info():
    return render_template('info.html',
                            title='How it Works')


#Login routes
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:   # if current user is logged in
        return redirect(url_for('index'))

    form = SignUpForm()

    # if form is submitted

    if form.validate_on_submit():

        #encrypt password
        hashed_password= bcrypt.generate_password_hash(form.password1.data)

        u = models.user(password = hashed_password, email = form.email.data, user_type = "1", name = form.name.data)

        db.session.add(u)    # add user to db
        db.session.commit()     # commit user to db
        flash(f'Account Created!', 'success')

        return redirect(url_for('user_login'))   # redirect to login page

    else:
        return render_template('register.html',
                        title='Sign Up',
                        form=form)


@app.route('/user_login', methods=['GET', 'POST'])
def user_login():
    if current_user.is_authenticated:   # if current user is logged in
        return redirect (url_for('index'))

    form = LoginForm()
    if form.validate_on_submit():

        ##flash('Succesfully received form data. %s %s %s'%(form.username.data, form.password.data, form.remember.data))

        # get first instance of user in db
        u = models.user.query.filter_by(email = form.email.data).first()

        # check username and password
        if u and bcrypt.check_password_hash(u.password, form.password.data):
            login_user(u)
            flash('Login Successful!', 'success')
            return redirect(url_for('user_dashboard'))
        else:
            flash(f'Login unsuccessful. Please check email and password', 'error')

    return render_template('user_login.html',
                           title='User Login',
                           form=form)


@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    return render_template('admin_login.html',
                           title='Admin Login')


# only logout if user is logged in
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logout Successful!', 'info')
    # redirect to home page
    return redirect(url_for('index'))


#User exclusive pages
@app.route('/user_dashboard')
def user_dashboard():
    return render_template('user_dashboard.html',
                            name=current_user.name,
                            title='User Dashboard')


@app.route('/pricing')
def pricing():
    return render_template('pricing.html',
                            title='Our Prices')


@app.route('/profile')
def profile():
    return render_template('profile.html',
                            title='Your Profile',
                            name=current_user.name,
                            email=current_user.email,
                            user_type=current_user.user_type)


@app.route('/send_feedback')
def send_feedback():
    return render_template('send_feedback.html',
                            title='Send Us Your Feedback')


@app.route('/locations')
def locations():
    return render_template('locations.html',
                            title='Pickup Locations')


@app.route('/booking1_user', methods=['GET', 'POST'])
def booking1_user():
    # if user has saved card details
    # form = BookingForm()
    #if user does not have saved card details
    form = BookingForm()
    
    form.scooter_id.choices = [("Scooter " + str(scooter.id)) for scooter in models.scooter.query.filter_by(location=form.location_id.data).all()]
    flash (form.hire_period.data)
    
    


    date = datetime.now()
    if form.validate_on_submit():
        b = models.booking(hire_period=form.hire_period.data, status="Normal", cost=5.0, initial_date_time=date, final_date_time=date,email=current_user.email, user_id=current_user.id, scooter_id=form.scooter_id.data, collection_id=1)
        db.session.add(b)
        db.session.commit()
        flash ("Successful booking")

        return redirect(url_for('user_payment'))

    return render_template('booking1_user.html',
                            title='Choose a Location', form=form)



@app.route('/booking2_saved')
def booking2_saved():
    return render_template('booking2_saved.html',
                            title='Make a Booking')


@app.route('/booking2_unsaved')
def booking2_unsaved():
    return render_template('booking2_unsaved.html',
                            title='Make a Booking')


@app.route('/booking3_user')
def booking3_user():
    return render_template('booking3_user.html',
                            title='Booking Confirmation')


@app.route('/cancel_booking')
def cancel_booking():
    return render_template('cancel_booking.html',
                            title='Cancel Booking')


@app.route('/extend_booking')
def extend_booking():
    return render_template('extend_booking.html',
                            title='Extend Booking')


#Admin exclusive pages
@app.route('/admin_dashboard')
def admin_dashboard():
    return render_template('admin_dashboard.html',
                            name=current_user.name,
                            title='Admin Dashboard')


@app.route('/review_feedback')
def review_feedback():
    return render_template('review_feedback.html',
                            title='Review Customer Feedback')

@app.route('/view_scooters')
def view_scooters():
    return render_template('view_scooters.html',
                            title='View Scooters')


@app.route('/add_scooter')
def add_scooter():
    return render_template('add_scooter.html',
                            title='Add New Scooter')

@app.route('/configure_scooter')
def configure_scooter():
    return render_template('configure_scooter.html',
                            title='Configure A Scooter')


@app.route('/sales_metrics')
def sales_metrics():
    return render_template('sales_metrics.html',
                            title='View Sales Metrics')


@app.route('/booking1_admin')
def booking1_admin():
    return render_template('booking1_admin.html',
                            title='Choose a Location')


@app.route('/booking2_admin')
def booking2_admin():
    return render_template('booking2_admin.html',
                            title='Make a Booking')


@app.route('/booking3_admin')
def booking3_admin():
    return render_template('booking3_admin.html',
                            title='Booking Confirmation')

@app.route('/user_payment')
def user_payment():
    return render_template('user_payment.html',
                            title='Payment')
