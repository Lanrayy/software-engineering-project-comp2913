from flask import render_template, flash, request, redirect, url_for, abort, make_response, session, jsonify
from app import app, db, bcrypt, models, login_manager
from .forms import LoginForm, SignUpForm, AdminBookingForm, UserBookingForm
from flask_login import login_user, current_user, logout_user, login_required
from datetime import datetime, timedelta
import os

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

        u = models.user(password = hashed_password, email = form.email.data, account_type = "customer", user_type = "default", name = form.name.data)

        db.session.add(u)    # add user to db
        db.session.commit()     # commit user to db
        flash(f'Account Created!', 'success')

        return redirect(url_for('user_login'))   # redirect to login page

    else:
        return render_template('register.html',
                        title='Sign Up',
                        form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
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
            if(u.account_type == "employee" or u.account_type == "manager"):
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('user_dashboard'))
        else:
            flash(f'Login unsuccessful. Please check email and password', 'error')

    return render_template('login.html',
                           title='Login',
                           form=form)


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
                            account_type=current_user.account_type)


@app.route('/send_feedback')
def send_feedback():
    return render_template('send_feedback.html',
                            title='Send Us Your Feedback')


@app.route('/locations')
def locations():
    return render_template('locations.html',
                            title='Pickup Locations')


@app.route('/booking1', methods=['GET', 'POST'])
def booking1():
    if not current_user.account_type == "employee" and not current_user.account_type == "manager":
        #User booking
        form = UserBookingForm()

        form.location_id.data = '1'

        form.scooter_id.choices = [(scooter.id, "Scooter ID: " + str(scooter.id))
                                    for scooter in models.scooter.query.filter_by(collection_id = form.location_id.data, availability = 1).all()]

        if len(form.scooter_id.choices) == 0:
            form.scooter_id.choices = [("0", "No Scooters Available")]

        if form.is_submitted():
            if(form.scooter_id.data == "0"):
                flash("Please choose a location with available scooters")
                return render_template('booking1_user.html',
                                        title='Choose a Location',
                                        form = form)
            if form.hire_period.data == '1':
                cost = 10.00
                hours = 1
            elif form.hire_period.data == '2':
                cost = 39.00
                hours = 4
            elif form.hire_period.data == '3':
                cost = 109.00
                hours = 24
            elif form.hire_period.data == '4':
                cost = 399.00
                hours = 168
            else:
                cost = 10.00
                hours = 1

            booking = models.booking(duration = hours,
                                     status="active",
                                     cost = cost,
                                     initial_date_time = datetime.utcnow(),
                                     final_date_time = datetime.utcnow() + timedelta(hours = hours),
                                     email = current_user.email,
                                     user_id = current_user.id,
                                     scooter_id = int(form.scooter_id.data),
                                     collection_id = int(form.location_id.data))

            db.session.add(booking)
            scooter = models.scooter.query.filter_by(id = form.scooter_id.data).first() #find the scooter
            scooter.availability = 2 #mark as unavailable
            db.session.commit()

            session['booking_id'] = booking.id

            #card details do no exist, send to payment page
            flash("Booking Successful from an admin")
            return redirect("/booking2")

        return render_template('booking1_user.html',
                                title='Choose a Location',
                                form = form)
    elif current_user.account_type == "employee" or current_user.account_type == "manager":
        #Employee or Manager booking
        form = AdminBookingForm()

        form.location_id.data = '1'

        form.scooter_id.choices = [(scooter.id, "Scooter ID: " + str(scooter.id))
                                    for scooter in models.scooter.query.filter_by(collection_id = form.location_id.data, availability = 1).all()]

        if len(form.scooter_id.choices) == 0:
            form.scooter_id.choices = [("0", "No Scooters Available")]

        if form.is_submitted():
            if(form.scooter_id.data == "0"):
                flash("Please choose a location with available scooters")
                return render_template('booking1_admin.html',
                                        title='Choose a Location',
                                        form = form)
            if form.hire_period.data == '1':
                cost = 10.00
                hours = 1
            elif form.hire_period.data == '2':
                cost = 39.00
                hours = 4
            elif form.hire_period.data == '3':
                cost = 109.00
                hours = 24
            elif form.hire_period.data == '4':
                cost = 399.00
                hours = 168
            else:
                cost = 10.00
                hours = 1

            booking = models.booking(duration = hours,
                                     status="active",
                                     cost = cost,
                                     initial_date_time = datetime.utcnow(),
                                     final_date_time = datetime.utcnow() + timedelta(hours = hours),
                                     email = form.email.data,
                                     user_id = current_user.id,
                                     scooter_id = int(form.scooter_id.data),
                                     collection_id = int(form.location_id.data))

            db.session.add(booking)
            scooter = models.scooter.query.filter_by(id = form.scooter_id.data).first() #find the scooter
            scooter.availability = 2 #mark as unavailable
            db.session.commit()

            session['booking_id'] = booking.id

            exists = models.card_details.query.filter_by(user_id = current_user.id).first() is not None
            print(exists)
            if(exists):
                #card details exist, send to confirmation page straight away
                flash("Booking Successful!")
                return redirect("/booking2")
            else:
                #card details do no exist, send to payment page
                flash("Booking Successful from an unsaved user")
                return redirect("/booking2")

        return render_template('booking1_admin.html',
                                title='Choose a Location',
                                form = form)


@app.route('/booking1/<location_id>')
def booking1_location(location_id):
    scooters = models.scooter.query.filter_by(collection_id = location_id, availability = 1).all()

    scooterArray = []

    for scooter in scooters:
        scooterObj = {}
        scooterObj['id'] = scooter.id
        scooterArray.append(scooterObj)

    return jsonify({'scooters' : scooterArray})


@app.route('/booking2')
def booking2():
    booking = models.booking.query.filter_by(id = session.get('booking_id', None)).first()
    location = session.get('collection_location', None)
    return render_template('booking2.html',
                            title='Booking Confirmation',
                            booking=booking,
                            location=location)


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
