from flask import render_template, flash, request, redirect, url_for, abort, make_response, session, jsonify
from app import app, db, bcrypt, models, login_manager
from .forms import LoginForm, SignUpForm, AdminBookingForm, UserBookingForm, CardForm, AddScooterForm
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
        return redirect(url_for('login'))   # redirect to login page
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
            if form.save_card_details.data: # if the user want to save the card details,  save information into database
                hashed_card_num = bcrypt.generate_password_hash(form.card_number.data)
                hashed_cvv = bcrypt.generate_password_hash(form.cvv.data)
                last_four = form.card_number.data[12:]
                p = models.card_details(name = form.name.data,
                                        cardnumber = hashed_card_num,
                                        last_four = last_four,
                                        expiry_date = form.expiry.data,
                                        cvv = hashed_cvv,
                                        user_id = current_user.id)
                db.session.add(p)
                db.session.commit()
                flash("Card details saved")

            booking = 0

            if session.get('booking_user_id') == 0:
                booking = models.booking(duration = session.get('booking_duration', None),
                                         status= session.get('booking_status', None),
                                         cost = session.get('booking_cost', None),
                                         initial_date_time = session.get('booking_initial', None),
                                         final_date_time = session.get('booking_final', None),
                                         email = session.get('booking_email', None),
                                         scooter_id = session.get('booking_scooter_id', None),
                                         collection_id = session.get('booking_collection_id', None))
                db.session.add(booking)
            else:
                booking = models.booking(duration = session.get('booking_duration', None),
                                         status= session.get('booking_status', None),
                                         cost = session.get('booking_cost', None),
                                         initial_date_time = session.get('booking_initial', None),
                                         final_date_time = session.get('booking_final', None),
                                         email = session.get('booking_email', None),
                                         user_id = session.get('booking_user_id', None),
                                         scooter_id = session.get('booking_scooter_id', None),
                                         collection_id = session.get('booking_collection_id', None))
                db.session.add(booking)

            scooter = models.scooter.query.filter_by(id = session.get('booking_scooter_id', None)).first() #find the scooter
            scooter.availability = 2 #mark as unavailable
            db.session.commit()

            session['booking_id'] = booking.id

            flash("Booking Successful!")
            return redirect("/booking2") #send to booking confirmation

    return render_template('card.html',
                           title='Card',
                           form=form,
                           data=data,
                           card_found = card_found)


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

@app.route('/profile', methods=['GET', 'POST'])
def profile():

    #filter the query into the bookings and card
    cards = models.card_details.query.first()

    #Doesn't delete cards
    #if request.method == 'POST':
    #    db.session.delete(cards)
    #    db.session.commit()
    #flask('Card deleted')

    bookings =  models.booking.query.all()  

    return render_template('profile.html',
                            title='Your Profile',
                            name=current_user.name,
                            email=current_user.email,
                            account_type=current_user.account_type,
                            cards = cards,
                            booking = bookings)


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

        form.location_id.choices = [(collection_point.id, collection_point.location)
                                    for collection_point in models.collection_point.query.all()]

        if form.start_date.data == None:
            form.start_date.data = datetime.now()
        if form.location_id.data == None:
            form.location_id.data = '1'

        form.scooter_id.choices = [(scooter.id, "Scooter ID: " + str(scooter.id))
                                    for scooter in models.scooter.query.filter_by(collection_id = form.location_id.data, availability = 1).all()]

        if len(form.scooter_id.choices) == 0:
            form.scooter_id.choices = [("0", "No Scooters Available")]

        if form.is_submitted():
            if form.scooter_id.data == "0":
                flash("Please choose a location with available scooters")
                return render_template('booking1_user.html',
                                        title='Choose a Location',
                                        form = form)

            if form.start_date.data == None:
                flash("Please enter a valid date")
                return render_template('booking1_user.html',
                                        title='Choose a Location',
                                        form = form)

            if form.start_date.data < datetime.now():
                flash("The start date can't be in the past")
                return render_template('booking1_user.html',
                                        title='Choose a Location',
                                        form = form)

            if form.hire_period.data == '1':
                cost = models.pricing.query.filter_by(id = 1).first().price
                hours = 1
            elif form.hire_period.data == '2':
                cost = models.pricing.query.filter_by(id = 1).first().price
                hours = 4
            elif form.hire_period.data == '3':
                cost = models.pricing.query.filter_by(id = 1).first().price
                hours = 24
            elif form.hire_period.data == '4':
                cost = models.pricing.query.filter_by(id = 1).first().price
                hours = 168
            else:
                cost = 10.00
                hours = 1

            session['booking_duration'] = hours
            session['booking_status'] = "active"
            session['booking_cost'] = cost
            session['booking_initial'] = form.start_date.data
            session['booking_final'] = form.start_date.data + timedelta(hours = hours)
            session['booking_user_id'] = current_user.id
            session['booking_email'] = current_user.email
            session['booking_scooter_id'] = int(form.scooter_id.data)
            session['booking_collection_id'] = int(form.location_id.data)

            #card details do not exist, send to payment page
            exists = models.card_details.query.filter_by(user_id = current_user.id).first() is not None
            if(exists):
                #card details exist, book then send to confirmation page straight away
                booking = models.booking(duration = hours,
                                         status="active",
                                         cost = cost,
                                         initial_date_time = form.start_date.data,
                                         final_date_time = form.start_date.data + timedelta(hours = hours),
                                         email = current_user.email,
                                         user_id = current_user.id,
                                         scooter_id = int(form.scooter_id.data),
                                         collection_id = int(form.location_id.data))

                db.session.add(booking)
                scooter = models.scooter.query.filter_by(id = form.scooter_id.data).first() #find the scooter
                scooter.availability = 2 #mark as unavailable
                db.session.commit()

                session['booking_id'] = booking.id

                flash("Booking Successful!")
                return redirect("/booking2")
            else:
                #card details do not exist, send to payment page
                return redirect("/card")

        return render_template('booking1_user.html',
                                title='Choose a Location',
                                form = form)

    elif current_user.account_type == "employee" or current_user.account_type == "manager":
        #Employee or Manager booking
        form = AdminBookingForm()

        form.location_id.choices = [(collection_point.id, collection_point.location)
                                    for collection_point in models.collection_point.query.all()]

        if form.start_date.data == None:
            form.start_date.data = datetime.now()
        if form.location_id.data == None:
            form.location_id.data = '1'

        form.scooter_id.choices = [(scooter.id, "Scooter ID: " + str(scooter.id))
                                    for scooter in models.scooter.query.filter_by(collection_id = form.location_id.data, availability = 1).all()]

        if len(form.scooter_id.choices) == 0:
            form.scooter_id.choices = [("0", "No Scooters Available")]

        if form.is_submitted():
            if form.scooter_id.data == "0":
                flash("Please choose a location with available scooters")
                return render_template('booking1_admin.html',
                                        title='Choose a Location',
                                        form = form)

            if form.start_date.data == None:
                flash("Please enter a valid date")
                return render_template('booking1_admin.html',
                                        title='Choose a Location',
                                        form = form)

            if form.start_date.data < datetime.now():
                flash("The start date can't be in the past")
                return render_template('booking1_admin.html',
                                        title='Choose a Location',
                                        form = form)

            if form.hire_period.data == '1':
                cost = models.pricing.query.filter_by(id = 1).first().price
                hours = 1
            elif form.hire_period.data == '2':
                cost = models.pricing.query.filter_by(id = 1).first().price
                hours = 4
            elif form.hire_period.data == '3':
                cost = models.pricing.query.filter_by(id = 1).first().price
                hours = 24
            elif form.hire_period.data == '4':
                cost = models.pricing.query.filter_by(id = 1).first().price
                hours = 168
            else:
                cost = 10.00
                hours = 1

            session['booking_duration'] = hours
            session['booking_status'] = "active"
            session['booking_cost'] = cost
            session['booking_initial'] = datetime.utcnow()
            session['booking_final'] = datetime.utcnow() + timedelta(hours = hours)
            session['booking_user_id'] = 0
            session['booking_email'] = form.email.data
            session['booking_scooter_id'] = int(form.scooter_id.data)
            session['booking_collection_id'] = int(form.location_id.data)

            return redirect("/card")

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

    if booking.duration == 1:
        session['booking_period'] = "1 Hour"
    elif booking.duration == 4:
        session['booking_period'] = "4 Hours"
    elif booking.duration == 24:
        session['booking_period'] = "1 Day"
    elif booking.duration == 168:
        session['booking_period'] = "1 Week"

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

    rec = models.scooter.query.all()
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


@app.route('/configure_scooter')
def configure_scooter():
    return render_template('configure_scooter.html',
                            title='Configure A Scooter')


@app.route('/sales_metrics')
def sales_metrics():
    data = models.transactions.query.all()
    one_hour_metric = 0
    four_hour_metric = 0
    twentyfour_hour_metric = 0
    one_week_metric = 0
    date = datetime.utcnow()
    week_start = date + timedelta(-date.weekday(), weeks=0)
    week_end = date + timedelta(-date.weekday() + 6)

    # for each transaction in if it is within the last week add it to the correct metric
    for transaction in data:
        if transaction.hire_period == 1 and transaction.booking_time > week_start and transaction.booking_time < week_end:
            one_hour_metric += 1
        elif transaction.hire_period == 4 and transaction.booking_time > week_start and transaction.booking_time < week_end:
            four_hour_metric += 1
        elif transaction.hire_period == 24 and transaction.booking_time > week_start and transaction.booking_time < week_end:
            twentyfour_hour_metric += 1
        elif transaction.hire_period == 168 and transaction.booking_time > week_start and transaction.booking_time < week_end:
            one_week_metric += 1

    return render_template('sales_metrics.html',
                            title='View Sales Metrics',
                            one_hour_metric = one_hour_metric,
                            four_hour_metric = four_hour_metric,
                            twentyfour_hour_metric = twentyfour_hour_metric,
                            one_week_metric = one_week_metric,
                            week_start = week_start,
                            week_end = week_end)
