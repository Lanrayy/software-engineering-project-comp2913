from flask import render_template, flash
from app import app, db, bcrypt, models
from .forms import LoginForm, SignUpForm, AdminBookingForm, BookingForm, CardForm, AddScooterForm, ConfigureScooterForm
from flask import request, redirect, url_for, abort, make_response, session
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


@app.route('/user_login', methods=['GET', 'POST'])
def user_login():
    if current_user.is_authenticated:   # if current user is logged in
        return redirect (url_for('index'))

    form = LoginForm()
    if form.validate_on_submit():
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

    return render_template('user_login.html',
                           title='User Login',
                           form=form)

# card route - to be integrated with the bookings page
@app.route('/card', methods=['GET', 'POST'])
def card():
    form = CardForm()
    data = models.card_details.query.filter_by(user_id=current_user.id).all()

    if data: # if the user already has card details saved
        card_found = True
    else:
        card_found = False
    
    if request.method == 'POST':
        if form.validate_on_submit():
            if form.save_card_details.data:
                # if the user want to save the card details
                # save information into database
                p = models.card_details(name = form.name.data,
                                        cardnumber = form.card_number.data,
                                        expiry_date = form.expiry.data,
                                        cvv = form.cvv.data,
                                        user_id = current_user.id)
                db.session.add(p)
                db.session.commit()
                flash("Card details saved")
                return redirect(url_for('card')) # needs to be changed
                
    return render_template('card.html', 
                           title='Card',
                           form=form,
                           data=data,
                           card_found = card_found)

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if current_user.is_authenticated:   # if current user is logged in
        return redirect (url_for('index'))

    form = LoginForm()
    if form.validate_on_submit():

        # get first instance of user in db
        u = models.user.query.filter_by(email = form.email.data).first()

        # check username and password
        if u and bcrypt.check_password_hash(u.password, form.password.data):
            login_user(u)
            flash('Admin Login Successful!', 'success')
            if(u.account_type == "employee" or u.account_type == "manager"):
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('user_dashboard'))
        else:
            flash(f'Admin Login unsuccessful. Please check email and password', 'error')

    return render_template('admin_login.html',
                           title='Admin Login',
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


@app.route('/booking1_user')
def booking1_user():
    #needs to send to user/booking2_saved or user/booking2_unsaved depending on saved card details
    collection_points = models.collection_point.query.all()
    scooter = models.scooter
    return render_template('booking1_user.html',
                            title='Choose a Location',
                            collection_points=collection_points,
                            scooter=scooter)


#intermediate route to save the collection point and scooter ID
@app.route('/booking2_user_variables/<string:booking_collection_point>/<int:scooter_id>')
def booking2_user_variables(booking_collection_point, scooter_id):
    session['collection_location'] = booking_collection_point
    session['collection_id'] = models.collection_point.query.filter_by(location = booking_collection_point).first().id
    session['scooter_id'] = scooter_id

    return redirect(url_for('booking2_saved'))


@app.route('/booking2_saved', methods=['GET', 'POST'])
def booking2_saved():
    form = BookingForm()

    if form.validate_on_submit():
        if form.hire_period.data == 1:
            cost = 10.00
            hours = 1
        if form.hire_period.data == 2:
            cost = 39.00
            hours = 4
        if form.hire_period.data == 3:
            cost = 109.00
            hours = 24
        if form.hire_period.data == 4:
            cost = 399.00
            hours = 168
        else:
            cost = 10.00
            hours = 1

        booking = models.booking(hire_period = form.hire_period.data,
                                 status = "active",
                                 cost = cost,
                                 initial_date_time = datetime.utcnow(),
                                 final_date_time = datetime.utcnow() + timedelta(hours = hours),
                                 email = current_user.email,
                                 scooter_id = session.get('scooter_id', None),
                                 collection_id = session.get('collection_id', None))

        db.session.add(booking)
        scooter = models.scooter.query.filter_by(id = session.get('scooter_id', None)).first() #find the scooter
        scooter.availability = 2 #mark as unavailable
        db.session.commit()

        session['booking_id'] = booking.id

        flash(f'Booking Created!', 'success')

        return redirect("/booking3")
    else:
        return render_template('booking2_saved.html',
                                title='Make a Booking',
                                form=form)


@app.route('/booking2_unsaved')
def booking2_unsaved():
    return render_template('booking2_unsaved.html',
                            title='Make a Booking')


@app.route('/booking3')
def booking3():
    booking = models.booking.query.filter_by(id = session.get('booking_id', None)).first()
    location = session.get('collection_location', None)
    return render_template('booking3.html',
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



@app.route('/view_scooters', methods=['GET', 'POST'])
def view_scooters():

    rec = models.scooter.query.all()
    form = ConfigureScooterForm()

    if request.method == 'POST':
        id = request.form["edit_button"]
        u = models.scooter.query.get(id)
        session['confg_sctr_id'] = u.id
        return redirect(url_for('configure_scooter'))

    return render_template('view_scooters.html',
                            title='View Scooters', rec=rec)



@app.route('/add_scooter', methods=['GET','POST'])
def add_scooter():
    form = AddScooterForm()
    
    if form.validate_on_submit():
        u = models.scooter(availability = form.availability.data, collection_id = form.location_id.data)
        db.session.add(u)    # add scooter to db
        db.session.commit()     # commit scooter to db
    return render_template('add_scooter.html',
                            title='Add New Scooter', form=form)


@app.route('/configure_scooter', methods=['GET', 'POST'])
def configure_scooter():
    scooter = models.scooter.query.get(session['confg_sctr_id'])
    form = ConfigureScooterForm()
    #retrieve details to display
    form.scooter_id.data = session['confg_sctr_id']
    form.availability.data = scooter.availability
    form.location_id.data = scooter.collection_id
    if request.method == 'POST':
        # update details if user clicks confirm
        if request.form.get("cancel") is None:
            print("updating scooter")
            scooter.availability = request.form.get("availability")
            scooter.collection_id = request.form.get("location_id")
            db.session.commit()
            # print(models.scooter.query.all())
            flash(f'Scooter Details Updated', 'success')
        return redirect(url_for('view_scooters'))
    return render_template('configure_scooter.html',
                            title='Configure A Scooter', form=form)


@app.route('/sales_metrics')
def sales_metrics():
    return render_template('sales_metrics.html',
                            title='View Sales Metrics')


@app.route('/booking1_admin')
def booking1_admin():
    collection_points = models.collection_point.query.all()
    scooter = models.scooter
    return render_template('booking1_admin.html',
                            title='Choose a Location',
                            collection_points=collection_points,
                            scooter=scooter)

#intermediate route to save the collection point and scooter ID
@app.route('/booking2_admin_variables/<string:booking_collection_point>/<int:scooter_id>')
def booking2_admin_variables(booking_collection_point, scooter_id):
    session['collection_location'] = booking_collection_point
    session['collection_id'] = models.collection_point.query.filter_by(location = booking_collection_point).first().id
    session['scooter_id'] = scooter_id

    return redirect(url_for('booking2_admin'))


@app.route('/booking2_admin', methods=['GET', 'POST'])
def booking2_admin():
    form = AdminBookingForm()

    if form.validate_on_submit():
        if form.hire_period.data == 1:
            cost = 10.00
            hours = 1
        if form.hire_period.data == 2:
            cost = 39.00
            hours = 4
        if form.hire_period.data == 3:
            cost = 109.00
            hours = 24
        if form.hire_period.data == 4:
            cost = 399.00
            hours = 168
        else:
            cost = 10.00
            hours = 1

        booking = models.booking(hire_period = form.hire_period.data,
        status = "active",
        cost = cost,
        initial_date_time = datetime.utcnow(),
        final_date_time = datetime.utcnow() + timedelta(hours = hours),
        email = form.email.data,
        scooter_id = session.get('scooter_id', None),
        collection_id = session.get('collection_id', None))

        db.session.add(booking)
        scooter = models.scooter.query.filter_by(id = session.get('scooter_id', None)).first() #find the scooter
        scooter.availability = 2 #mark as unavailable
        db.session.commit()

        session['booking_id'] = booking.id

        flash(f'Booking Created!', 'success')

        return redirect("/booking3")
    else:
        return render_template('booking2_admin.html',
        title='Make a Booking',
        form=form)
