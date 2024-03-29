from cmath import log
from flask import render_template, flash, request, redirect, url_for, abort, make_response, session, jsonify
from app import app, db, bcrypt, models, login_manager, mail
from .forms import LoginForm, SignUpForm, AdminBookingForm, UserBookingForm, CardForm, AddScooterForm, ConfigureScooterForm, FeedbackForm, EditFeedbackForm, PricesForm, ExtendBookingForm
from flask_login import login_user, current_user, logout_user, login_required
from datetime import datetime, timedelta
from sqlalchemy import or_
import os
import smtplib
import matplotlib
import matplotlib.pyplot as plt
from flask_mail import Message
import logging, socket
from datetime import datetime

#function for automatically checking if bookings have become moved from active to past or upcoming to active etc
def organise_bookings():
    #get all bookings
    bookings = models.booking.query.filter(or_(models.booking.status == "active", models.booking.status == "upcoming"))

    for booking in bookings:
        #check for upcoming bookings that should become active
        #check if the booking start has past BUT the end time has not
        if booking.initial_date_time < datetime.utcnow() and datetime.utcnow() < booking.final_date_time:
            booking.status = "active"
        #check if the booking's final_date_time is already in the past, and thus should become a "past" booking
        if booking.final_date_time < datetime.utcnow():
            booking.status = "expired"

    #finalise changes
    try:
        db.session.commit()
    except:
        db.session.rollback()
    return 0

#function for automatically adding scooters to locations
def organise_scooters():
    #get all scooters
    scooters = models.scooter.query.all()
    #get all locations
    locations = models.collection_point.query.all()
    #initialise all locations num_scooters as 0
    for location in locations:
        location.num_scooters = 0
    #for each location check how many scooters are assigned to it, then change num_scooters to match
    for scooter in scooters:
        #get the location that the scooter is assigned to
        scooter_location = models.collection_point.query.filter_by(id = scooter.collection_id).first()
        scooter_location.num_scooters = scooter_location.num_scooters + 1

    #finalise changes
    try:
        db.session.commit()
    except:
        db.session.rollback()
    return 0


matplotlib.use('agg') # Does not connect to GUI (Fixes error of crashing sales metrics page on reload)

# obtain additional log info
class LogFormatter(logging.Formatter):
    def format(self, record):
        record.url = request.url
        record.address = socket.gethostbyname(socket.gethostname())
        return super(LogFormatter, self).format(record)

# create logger
logger = logging.getLogger("logger")
logger.setLevel(logging.INFO)
# and a file handler for the logger to write to
fh = logging.FileHandler('app.log')
# fh = logging.F()
fh.setLevel(logging.INFO)
# formatter for layout in log file
FORMAT = '%(asctime)s %(address)s %(url)-40s %(levelname)s %(message)s'

formatter = LogFormatter(FORMAT)
# connect formatter to handler
fh.setFormatter(formatter)
# then add handler to the logger
logger.addHandler(fh)

# prints to the log file each time a client visits a page
def logPage():
    if current_user.is_anonymous:
        logger.info("(anonymous user)")
    else:
        logger.info("(user " + str(current_user.id) + ")")


# redirect to the corresponding pages upon error
def redirectError(exception):
    logger.error(exception)
    try:
        # str(current_user.id)
        return redirect('/user_dashboard')
    except:
        return redirect('/')


#Unregistered user exclusive pages
@app.route('/')
def index():
    logPage()
    return render_template('landing_page.html',
                            title='Home')


@app.route('/info')
def info():
    prices = models.pricing.query.all()
    logPage()
    return render_template('info.html',
                            title='How it Works',
                            prices=prices)

global now

#Login routes
@app.route('/register', methods=['GET', 'POST'])
def register():
    logPage()
    if current_user.is_authenticated:   # if current user is logged in
        return redirect(url_for('index'))
    form = SignUpForm()

    # if form is submitted
    if form.validate_on_submit():
        #encrypt password
        hashed_password= bcrypt.generate_password_hash(form.password1.data)
        u = models.user(password = hashed_password, email = form.email.data, account_type = "customer", user_type = form.user_type.data, name = form.name.data)
        db.session.add(u)    # add user to db
        try:
            db.session.commit()
        except:
            db.session.rollback()     # commit user to db

        now = str(datetime.now())
        logger.info(u.email+" created an account at "+ now)
        flash(f'Account Created!', 'success')
        return redirect(url_for('login'))   # redirect to login page
    else:
        return render_template('register.html',
                        title='Sign Up',
                        form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    logPage()
    if current_user.is_authenticated:   # if current user is logged in
        return redirect (url_for('index'))

    form = LoginForm()
    if form.validate_on_submit():
        # get first instance of user in db
        u = models.user.query.filter_by(email = form.email.data).first()

        # check username and password
        if u:
            if bcrypt.check_password_hash(u.password, form.password.data):
                login_user(u)
                flash('Login Successful!', 'success')
                logger.info(u.email+" logged in")
                if(u.account_type == "employee" or u.account_type == "manager"):
                    return redirect(url_for('admin_dashboard'))
                else:
                    return redirect(url_for('user_dashboard'))
            else:
                now = str(datetime.now())
                app.logger.info(u.email + " unsuccesfull login at "+ now)
                flash(f'Login unsuccessful. Please check email and password', 'danger')
        else:
            logger.info("unsuccesful login")

            flash(f'Login unsuccessful. Please check email and password', 'danger')

    return render_template('login.html',
                           title='Login',
                           form=form)


# card route - to be integrated with the bookings page
@app.route('/card', methods=['GET', 'POST'])
@login_required
def card():
    try:

        logPage()
        form = CardForm()
        data = models.card_details.query.filter_by(user_id=current_user.id).all()

        if data: # if the user already has card details saved
            card_found = True
        else:
            card_found = False

        if request.method == 'POST':
            #if the card details check out
            if form.validate_on_submit():
                logger.info("card form successfully submitted")
                if form.save_card_details.data: # if the user want to save the card details,  save information into database
                    hashed_card_num = bcrypt.generate_password_hash(form.card_number.data) # hash the card number
                    hashed_cvv = bcrypt.generate_password_hash(form.cvv.data)
                    last_four = form.card_number.data[12:] # save the last four digits of the card number
                    p = models.card_details(name = form.name.data,
                                            cardnumber = hashed_card_num,
                                            last_four = last_four,
                                            expiry_date = form.expiry.data,
                                            cvv = hashed_cvv,
                                            user_id = current_user.id)
                    db.session.add(p)
                    try:
                        db.session.commit()
                    except:
                        db.session.rollback()
                    flash("Card details saved", "success")
                    logger.info("card details saved")

                #initialise booking
                booking = 0

                #check if we were booking or extending
                if session.get('extending') != None:
                    if session.pop('extending') == "True":
                        #we are extending, make sure to redirect to profile and send an email about the Extension
                        booking = models.booking.query.filter_by(id = session.get('booking_id', None)).first()

                        #get our variables from the session
                        hours = session.get('extend_hours', None)
                        cost = session.get('extend_cost', None)

                        #extend the booking pointed to by the 'booking_id' in the session, and add to the cost
                        booking.duration = booking.duration + hours
                        booking.cost = booking.cost + cost
                        booking.final_date_time = booking.final_date_time + timedelta(hours = hours)

                        #add a new transaction, with the date for the transaction set as now
                        new_transaction = models.transactions(hire_period = hours,
                                                            booking_time = datetime.utcnow(),
                                                            transaction_cost = cost,
                                                            user_id = current_user.id,
                                                            booking_id = booking.id)
                        db.session.add(new_transaction)
                        try:
                            db.session.commit()
                        except:
                            db.session.rollback()
                        logger.info("new transaction added to transactions table")

                        #write the email message
                        msg = Message('Booking Extension Confirmation',
                                        sender='scootersleeds@gmail.com',
                                        recipients=[current_user.email])

                        msg.body = (f'Thank You, your booking extension has been confirmed. \nStart Date and Time: ' + str(booking.initial_date_time) +
                        '\nEnd Date and Time: ' + str(booking.final_date_time) +
                        '\nScooter ID: ' + str(booking.scooter_id) +
                        '\nReference Number: ' + str(booking.id))
                        mail.send(msg)
                        logger.info("email sent to user successfully")

                        flash("Booking Extension Successful!", "success")
                        logger.info("booking extension successful!")

                        return redirect("/profile")
                else:
                    # not extending, so booking
                    # if admin is is making a booking, the booking_user_id = 0
                    if session.get('booking_user_id') == 0:
                        #admin is making the booking
                        logger.info("admin user is making a booking on behalf of a customer")
                        booking = models.booking(duration = session.get('booking_duration', None),
                                                status= session.get('booking_status', None),
                                                cost = session.get('booking_cost', None),
                                                initial_date_time = session.get('booking_initial', None),
                                                final_date_time = session.get('booking_final', None),
                                                email = session.get('booking_email', None),
                                                scooter_id = session.get('booking_scooter_id', None),
                                                collection_id = session.get('booking_collection_id', None))
                        db.session.add(booking)
                        try:
                            db.session.commit()
                        except:
                            db.session.rollback()

                        # add new transaction to the transaction table- used on the metrics page, no user id
                        new_transaction = models.transactions(hire_period = session.get('booking_duration', None),
                                                            booking_time = datetime.utcnow(),
                                                            transaction_cost = session.get('booking_cost', None),
                                                            booking_id = booking.id)
                        db.session.add(new_transaction)

                        #set the specified email to recipient
                        recipients=[session.get('booking_email', None)]
                    else:
                        #user is making the booking
                        logger.info("customer is making a booking")
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
                        try:
                            db.session.commit()
                        except:
                            db.session.rollback()

                        # add new transaction to the transaction table- used on the metrics page, with user id
                        new_transaction = models.transactions(hire_period = session.get('booking_duration', None),
                                                            booking_time = datetime.utcnow(),
                                                            transaction_cost = session.get('booking_cost', None),
                                                            user_id = session.get('booking_user_id', None),
                                                            booking_id = booking.id)
                        db.session.add(new_transaction)
                        logger.info("new transaction added to transaction table")
                        #set user to recipient
                        recipients=[current_user.email]

                    try:
                        db.session.commit()
                    except:
                        db.session.rollback()

                    msg = Message('Booking Confirmation',
                                    sender='scootersleeds@gmail.com',
                                    recipients=recipients)

                    msg.body = (f'Thank You, your booking has been confirmed. \nStart Date and Time: ' + str(booking.initial_date_time) +
                    '\nEnd Date and Time: ' + str(booking.final_date_time) +
                    '\nScooter ID: ' + str(booking.scooter_id) +
                    '\nReference Number: ' + str(booking.id))
                    mail.send(msg)

                    session['booking_id'] = booking.id
                    logger.info("booking " + str(booking.id) + " successfully created")

                    return redirect("/booking2") #send to booking confirmation

        return render_template('card.html',
                            title='Card',
                            form=form,
                            data=data,
                            card_found = card_found)
    except Exception as e:
        logger.error(e)
        flash("An error has occured", "danger")
        if current_user.is_anonymous:
            return redirect('/')
            # str(current_user.id)
        elif current_user.account_type == "employee" or current_user.account_type == "manager":
            return redirect('/admin_dashboard')
        else:
            return redirect("/user_dashboard")

# only logout if user is logged in
@app.route('/logout')
@login_required
def logout():
    logPage()
    current_user_id = current_user.id
    logout_user()
    flash('Logout Successful!', 'success')
    logger.info("(user "+ str(current_user_id) + ") logged out")
    # redirect to home page
    return redirect(url_for('index'))


#User exclusive pages
@app.route('/user_dashboard')
@login_required
def user_dashboard():
    if current_user.account_type != 'customer': # Check if the logged in user is a customer or admin (True if employee/manager, False if customer)
        return redirect('/admin_dashboard') # Redirect any non-customer users to the admin dashboard

    try:
        logPage()
        #clean up bookings table
        organise_bookings()

        #filter the query into the bookings and locations
        locations = models.collection_point.query.all()
        bookings =  models.booking.query.filter_by(email = current_user.email, status = "upcoming")

        return render_template('user_dashboard.html',
                                name=current_user.name,
                                booking = bookings,
                                location = locations,
                                title='User Dashboard')
    except Exception as e:
        logger.error(e)
        if current_user.is_anonymous:
            return redirect('/')
            # str(current_user.id)
        elif current_user.account_type == "employee" or current_user.account_type == "manager":
            return redirect('/admin_dashboard')
        else:
            return redirect("/user_dashboard")


@app.route('/pricing')
def pricing():
    return render_template('pricing.html',
                            title='Our Prices')

@app.route('/delete/<int:id>', methods=['GET', 'POST'])
@login_required
def delete(id):
    #to_complete is a variable to get the id passed by pressing the complete button
    to_delete=models.card_details.query.get_or_404(id)

    try:
        #change the status value of this id into complete and commit to the database
        db.session.delete(to_delete)
        try:
            db.session.commit()
        except:
            db.session.rollback()
        logger.info("card removed")
        return redirect('/profile')

    except:
        return 'there was an error'


@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if current_user.account_type != 'customer': # Check if the logged in user is a customer or admin (True if employee/manager, False if customer)
        return redirect('/admin_dashboard') # Redirect any non-customer users to the admin dashboard

    try:
        logPage()
        #clean up bookings table
        organise_bookings()


        #filter the query into the bookings and card
        cards = models.card_details.query.filter_by(user_id = current_user.id).first()  #FOREIGN KEY
        locations = models.collection_point.query.all()

        #Doesn't delete
        if request.method == "POST":
            flash("button pressed")
            return redirect('profile')

        bookings =  models.booking.query.filter_by(email = current_user.email)
        collection_points = models.collection_point

        return render_template('profile.html',
                                title='Your Profile',
                                name=current_user.name,
                                email=current_user.email,
                                account_type=current_user.account_type,
                                cards = cards,
                                booking = bookings,
                                location = locations)
    except Exception as e:
        logger.error(e)
        if current_user.is_anonymous:
            return redirect('/')
            # str(current_user.id)
        elif current_user.account_type == "employee" or current_user.account_type == "manager":
            return redirect('/admin_dashboard')
        else:
            return redirect("/user_dashboard")


@app.route('/send_feedback', methods=('GET', 'POST'))
def send_feedback():
    logPage()
    form = FeedbackForm()

    if request.method == 'POST':
        f = models.feedback(message=form.feedback.data, priority=0, resolved=0)
        db.session.add(f)
        try:
            db.session.commit()
        except:
            db.session.rollback()
        flash(f'Feedback Submitted', 'success')
        if current_user.is_authenticated:
            logger.info("(user " + str(current_user.id) + ") feedback sent")

        return redirect(url_for('send_feedback'))
    return render_template('send_feedback.html',
                            title='Send Us Your Feedback',
                            form=form)


@app.route('/locations')
def locations():
    return render_template('locations.html',
                            title='Pickup Locations')




@app.route('/booking1', methods=['GET', 'POST'])
@login_required
def booking1():
    try:
        logPage()
        #clean up bookings table
        organise_bookings()
        #pass the prices to the webpage
        hire_periods = models.pricing.query.all()
        #current user is a customer
        if not current_user.account_type == "employee" and not current_user.account_type == "manager":

            msg = Message('Booking Confirmation',
                                sender='scootersleeds@gmail.com',
                                recipients=[current_user.email])
            #User booking
            form = UserBookingForm()

            #fill the location field with the locations in the table
            form.location_id.choices = [(collection_point.id, collection_point.location)
                                        for collection_point in models.collection_point.query.all()]

            #initialises the start date with the current time
            if form.start_date.data == None:
                form.start_date.data = datetime.utcnow()
            #initialise the location field with the first location_id in the table
            if form.location_id.data == None:
                form.location_id.data = '1'

            #initialise the scooter field with the scooters inside the first location_id
            form.scooter_id.choices = [(scooter.id, "Scooter ID: " + str(scooter.id))
                                        for scooter in models.scooter.query.filter_by(collection_id = form.location_id.data, availability = 1).all()]

            #if the location doesn't actually have any scooters tied to it, initialse the scooter selectfield
            if len(form.scooter_id.choices) == 0:
                form.scooter_id.choices = [("0", "No Scooters Available")]

            #check if the current user has card details or not
            data = models.card_details.query.filter_by(user_id=current_user.id).first()

            if data: # if the user already has card details saved
                card_found = True
            else:
                card_found = False

            #as long as the submit button is pressed
            if form.is_submitted():
                #checks that the user didn't try to book when location is empty of scooters
                if form.scooter_id.data == "0":
                    flash("Please choose a location with available scooters", 'danger')
                    logger.info("booking not made: no available scooters at " + str(form.location_id.data))
                    exists = models.card_details.query.filter_by(user_id = current_user.id).first() is not None
                    if(exists):
                        return render_template('booking1_user.html',
                                                title='Choose a Location',
                                                form = form,
                                                 hire_periods = hire_periods,
                                                 data = data,
                                                 card_found=True)

                    else:
                        return render_template('booking1_user.html',
                                                title='Choose a Location',
                                                form = form,
                                                hire_periods = hire_periods,
                                                card_found=False)

                #check that they actually put a start date
                if form.start_date.data == None:
                    flash("Please enter a valid date", 'danger')
                    logger.info("booking not made: invalid date " + str(form.start_date.data))
                    exists = models.card_details.query.filter_by(user_id = current_user.id).first() is not None
                    if(exists):
                        return render_template('booking1_user.html',
                                                title='Choose a Location',
                                                form = form,
                                                hire_periods = hire_periods,
                                                data = data,
                                                card_found=True)
                    else:
                        return render_template('booking1_user.html',
                                                title='Choose a Location',
                                                form = form,
                                                hire_periods = hire_periods,
                                                card_found=False)

                #check if the start date further in the past than now, with a grace period of 5 minutes
                if form.start_date.data < datetime.utcnow() + timedelta(minutes = -5):
                    flash("The start date can't be in the past", 'danger')
                    logger.info("booking not made: invalid date " + str(form.start_date.data))
                    exists = models.card_details.query.filter_by(user_id = current_user.id).first() is not None
                    if(exists):
                        return render_template('booking1_user.html',
                                                title='Choose a Location',
                                                form = form,
                                                hire_periods = hire_periods,
                                                data = data,
                                                card_found=True)

                    else:
                        return render_template('booking1_user.html',
                                                title='Choose a Location',
                                                form = form,
                                                hire_periods = hire_periods,
                                                card_found=False)
                #convert the option selected in the SelectField into a cost and the number of hours
                if form.hire_period.data == '1':
                    cost = models.pricing.query.filter_by(id = 1).first().price
                    hours = 1
                elif form.hire_period.data == '2':
                    cost = models.pricing.query.filter_by(id = 2).first().price
                    hours = 4
                elif form.hire_period.data == '3':
                    cost = models.pricing.query.filter_by(id = 3).first().price
                    hours = 24
                elif form.hire_period.data == '4':
                    cost = models.pricing.query.filter_by(id = 4).first().price
                    hours = 168
                else:
                    cost = 10.00
                    hours = 1

                #if the user is a student or a senior apply the discount
                if current_user.user_type == "senior" or current_user.user_type == "student":
                    flash("you are eligible for a student/senior discount", "info")
                    logger.info("(user " + str(current_user.id) + ") eligible for discount")
                    cost = cost * (0.8)

                else :
                    bookings =  models.booking.query.filter_by(email = current_user.email, status = "expired") # expired user booking
                    total_hours = 0 # total hours in the past week

                    #find the datetime a week ago
                    today_date = datetime.now()
                    days = timedelta(days = 7)
                    week_date = today_date - days

                    #check if they are a frequent user
                    for b in bookings :
                        if (b.initial_date_time > week_date):
                            total_hours += b.duration
                            if (total_hours > 8):
                                break

                    if (total_hours >= 8) :
                        flash("you are eligible for a frequent user discount", "info")
                        logger.info("(user " + str(current_user.id) + ") eligible for discount")
                        cost = cost * (0.8)


                #check every booking made with this scooter
                #make sure that the currently selected start date & end date DO NOT fall within start and end of any the bookings
                #only check currently "upcoming" or "active" bookings
                current_active_bookings = models.booking.query.filter_by(scooter_id = form.scooter_id.data, status = "active")
                current_upcoming_bookings = models.booking.query.filter_by(scooter_id = form.scooter_id.data, status = "upcoming")
                #check active bookings
                for booking in current_active_bookings:
                    #check that the selected start date doesn't fall during a booking
                    if form.start_date.data >= booking.initial_date_time and form.start_date.data <= booking.final_date_time:
                        flash("The scooter is unavailable for that start time", 'danger')
                        logger.info("booking not made: scooter " +
                                        str(form.scooter_id.data) +
                                        " unavailable at " +
                                        str(form.start_date.data))
                        exists = models.card_details.query.filter_by(user_id = current_user.id).first() is not None
                        if(exists):
                            return render_template('booking1_user.html',
                                                    title='Choose a Location',
                                                    form = form,
                                                    hire_periods = hire_periods,
                                                    data = data,
                                                    card_found=True)

                        else:
                            return render_template('booking1_user.html',
                                                    title='Choose a Location',
                                                    form = form,
                                                    hire_periods = hire_periods,
                                                    card_found=False)

                    #check that the projected end date doesn't fall during a booking
                    if form.start_date.data + timedelta(hours = hours) >= booking.initial_date_time and form.start_date.data + timedelta(hours = hours) <= booking.final_date_time:
                        flash("The projected end time falls within a pre-existing booking", 'danger')
                        logger.info("booking not made: pre-existing booking for scooter " +
                                        str(form.scooter_id.data) +
                                        " within range " +
                                        str(form.start_date.data) +
                                        " - " +
                                        str(form.start_date.data + timedelta(hours = hours)))
                        exists = models.card_details.query.filter_by(user_id = current_user.id).first()
                        if(exists):
                            return render_template('booking1_user.html',
                                                    title='Choose a Location',
                                                    form = form,
                                                    hire_periods = hire_periods,
                                                    data = data,
                                                    card_found=True)

                        else:
                            return render_template('booking1_user.html',
                                                    title='Choose a Location',
                                                    form = form,
                                                    hire_periods = hire_periods,
                                                    card_found=False)

                    #check that the current booking doesn't completely overlap a booking
                    #if the start time for a booking is during the current booking attempt
                    if form.start_date.data <= booking.initial_date_time and booking.initial_date_time <= form.start_date.data + timedelta(hours = hours):
                        flash("The current booking conflicts with an existing booking", 'danger')
                        logger.info("booking not made: pre-existing booking for scooter " +
                                        str(form.scooter_id.data) +
                                        " within range " +
                                        str(form.start_date.data) +
                                        " - " +
                                        str(form.start_date.data + timedelta(hours = hours)))
                        exists = models.card_details.query.filter_by(user_id = current_user.id).first() is not None
                        if(exists):
                            return render_template('booking1_user.html',
                                                    title='Choose a Location',
                                                    form = form,
                                                    hire_periods = hire_periods,
                                                    data = data,
                                                    card_found=True)

                        else:
                            return render_template('booking1_user.html',
                                                    title='Choose a Location',
                                                    form = form,
                                                    hire_periods = hire_periods,
                                                    card_found=False)
                #check upcoming bookings
                for booking in current_upcoming_bookings:
                    #check that the selected start date doesn't fall during a booking
                    if form.start_date.data >= booking.initial_date_time and form.start_date.data <= booking.final_date_time:
                        flash("The scooter is unavailable for that start time", 'danger')
                        logger.info("booking not made: scooter " +
                                        str(form.scooter_id.data) +
                                        " unavailable at " +
                                        str(form.start_date.data))
                        exists = models.card_details.query.filter_by(user_id = current_user.id).first() is not None
                        if(exists):
                            return render_template('booking1_user.html',
                                                    title='Choose a Location',
                                                    form = form,
                                                    hire_periods = hire_periods,
                                                    data = data,
                                                    card_found=True)

                        else:
                            return render_template('booking1_user.html',
                                                    title='Choose a Location',
                                                    form = form,
                                                    hire_periods = hire_periods,
                                                    card_found=False)

                    #check that the projected end date doesn't fall during a booking
                    if form.start_date.data + timedelta(hours = hours) >= booking.initial_date_time and form.start_date.data + timedelta(hours = hours) <= booking.final_date_time:
                        flash("The projected end time falls within a pre-existing booking", 'danger')
                        logger.info("booking not made: pre-existing booking for scooter " +
                                        str(form.scooter_id.data) +
                                        " within range " +
                                        str(form.start_date.data) +
                                        " - " +
                                        str(form.start_date.data + timedelta(hours = hours)))
                        exists = models.card_details.query.filter_by(user_id = current_user.id).first()
                        if(exists):
                            return render_template('booking1_user.html',
                                                    title='Choose a Location',
                                                    form = form,
                                                    hire_periods = hire_periods,
                                                    data = data,
                                                    card_found=True)

                        else:
                            return render_template('booking1_user.html',
                                                    title='Choose a Location',
                                                    form = form,
                                                    hire_periods = hire_periods,
                                                    card_found=False)

                    #check that the current booking doesn't completely overlap a booking
                    #if the start time for a booking is during the current booking attempt
                    if form.start_date.data <= booking.initial_date_time and booking.initial_date_time <= form.start_date.data + timedelta(hours = hours):
                        flash("The current booking conflicts with an existing booking", 'danger')
                        logger.info("booking not made: pre-existing booking for scooter " +
                                        str(form.scooter_id.data) +
                                        " within range " +
                                        str(form.start_date.data) +
                                        " - " +
                                        str(form.start_date.data + timedelta(hours = hours)))
                        exists = models.card_details.query.filter_by(user_id = current_user.id).first() is not None
                        if(exists):
                            return render_template('booking1_user.html',
                                                    title='Choose a Location',
                                                    form = form,
                                                    hire_periods = hire_periods,
                                                    data = data,
                                                    card_found=True)

                        else:
                            return render_template('booking1_user.html',
                                                    title='Choose a Location',
                                                    form = form,
                                                    hire_periods = hire_periods,
                                                    card_found=False)

                #store the booking details as a session to be used on successful payment
                session['booking_duration'] = hours
                session['booking_cost'] = cost
                session['booking_initial'] = form.start_date.data
                session['booking_final'] = form.start_date.data + timedelta(hours = hours)
                session['booking_user_id'] = current_user.id
                session['booking_email'] = current_user.email
                session['booking_scooter_id'] = int(form.scooter_id.data)
                session['booking_collection_id'] = int(form.location_id.data)

                #check if the booking should be currently active or upcoming
                if session.get('booking_initial', None) < datetime.utcnow():
                    #if the start time is before now, it's currently active
                    session['booking_status'] = "active"
                else:
                    #else it must be in the future
                    session['booking_status'] = "upcoming"

                #card details do not exist, send to payment page
                exists = models.card_details.query.filter_by(user_id = current_user.id).first() is not None
                if(exists):
                    #card details exist, book then send to confirmation page straight away
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


                    # add new transaction to the transaction table- used on the metrics page
                    new_transaction = models.transactions(hire_period = session.get('booking_duration', None),
                                                        booking_time = datetime.utcnow(),
                                                        transaction_cost = session.get('booking_cost', None),
                                                        user_id = session.get('booking_user_id', None),
                                                        booking_id = session.get('booking_id', None),)
                    db.session.add(new_transaction)
                    try:
                        db.session.commit()
                    except:
                        db.session.rollback()



                    session['booking_id'] = booking.id

                    msg = Message('Booking Confirmation',
                                    sender='scootersleeds@gmail.com',
                                    recipients=[current_user.email])

                    msg.body = (f'Thank You, your booking has been confirmed. \nStart Date and Time: ' + str(booking.initial_date_time) +
                    '\nEnd Date and Time: ' + str(booking.final_date_time) +
                    '\nScooter ID: ' + str(booking.scooter_id) +
                    '\nReference Number: ' + str(booking.id))
                    mail.send(msg)

                    logger.info("(user " + str(current_user.id) + "): booking " + str(booking.id) + " created")

                    return redirect("/booking2") #send to booking confirmation
                else:
                    #user does not have existing
                    return redirect("/card")

            #send the current user to the user version of the booking1 page
            return render_template('booking1_user.html',
                                    title='Choose a Location',
                                    form=form,
                                    data=data,
                                    card_found=card_found,
                                    hire_periods = hire_periods)

        #if the current user is an employee or manager
        elif current_user.account_type == "employee" or current_user.account_type == "manager":
            #Employee or Manager booking
            form = AdminBookingForm()

            #fill the location field with the locations in the table
            form.location_id.choices = [(collection_point.id, collection_point.location)
                                        for collection_point in models.collection_point.query.all()]

            #initialises the start date with the current time
            if form.start_date.data == None:
                form.start_date.data = datetime.utcnow()
            #initialise the location field with the first location_id in the table
            if form.location_id.data == None:
                form.location_id.data = '1'

            #initialise the scooter field with the scooters inside the first location_id
            form.scooter_id.choices = [(scooter.id, "Scooter ID: " + str(scooter.id))
                                        for scooter in models.scooter.query.filter_by(collection_id = form.location_id.data, availability = 1).all()]

            #as long as the submit button is pressed
            if form.is_submitted():
                #checks that the user didn't try to book when location is empty of scooters
                if form.scooter_id.data == "0":
                    flash("Please choose a location with available scooters", 'danger')
                    logger.info("booking not made: no available scooters at " + str(form.location_id.data))
                    return render_template('booking1_admin.html',
                                            title='Choose a Location',
                                            form = form,
                                            hire_periods = hire_periods)

                #check that they actually put a start date
                if form.start_date.data == None:
                    flash("Please enter a valid date", 'danger')
                    logger.info("booking not made: invalid date " + str(form.start_date.data))
                    return render_template('booking1_admin.html',
                                            title='Choose a Location',
                                            form = form,
                                            hire_periods = hire_periods)

                #check if the start date further in the past than now, with a grace period of 5 minutes
                if form.start_date.data < datetime.utcnow() + timedelta(minutes = -5):
                    flash("The start date can't be in the past", 'danger')
                    logger.info("booking not made: invalid date " + str(form.start_date.data))
                    return render_template('booking1_admin.html',
                                            title='Choose a Location',
                                            form = form,
                                            hire_periods = hire_periods)

                #convert the option selected in the SelectField into a cost and the number of hours
                if form.hire_period.data == '1':
                    cost = models.pricing.query.filter_by(id = 1).first().price
                    hours = 1
                elif form.hire_period.data == '2':
                    cost = models.pricing.query.filter_by(id = 2).first().price
                    hours = 4
                elif form.hire_period.data == '3':
                    cost = models.pricing.query.filter_by(id = 3).first().price
                    hours = 24
                elif form.hire_period.data == '4':
                    cost = models.pricing.query.filter_by(id = 4).first().price
                    hours = 168
                else:
                    cost = 10.00
                    hours = 1

                #check every booking made with this scooter
                #make sure that the currently selected start date & end date DO NOT fall within start and end of any the bookings
                #only check currently "upcoming" or "active" bookings
                current_active_bookings = models.booking.query.filter_by(scooter_id = form.scooter_id.data, status = "active")
                current_upcoming_bookings = models.booking.query.filter_by(scooter_id = form.scooter_id.data, status = "upcoming")
                #check active bookings
                for booking in current_active_bookings:
                    #check that the selected start date doesn't fall during a booking
                    if form.start_date.data >= booking.initial_date_time and form.start_date.data <= booking.final_date_time:
                        flash("The scooter is unavailable for that start time", 'danger')
                        logger.info("booking not made: scooter " +
                                        str(form.scooter_id.data) +
                                        " unavailable at " +
                                        str(form.start_date.data))
                        return render_template('booking1_admin.html',
                                                title='Choose a Location',
                                                form = form,
                                                hire_periods = hire_periods)
                    #check that the projected end date doesn't fall during a booking
                    if form.start_date.data + timedelta(hours = hours) >= booking.initial_date_time and form.start_date.data + timedelta(hours = hours) <= booking.final_date_time:
                        flash("The projected end time falls within a pre-existing booking", 'danger')
                        logger.info("booking not made: pre-existing booking for scooter " +
                                        str(form.scooter_id.data) +
                                        " within range " +
                                        str(form.start_date.data) +
                                        " - " +
                                        str(form.start_date.data + timedelta(hours = hours)))
                        return render_template('booking1_admin.html',
                                                title='Choose a Location',
                                                form = form,
                                                hire_periods = hire_periods)

                    #check that the current booking doesn't completely overlap a booking
                    #if the start time for a booking is during the current booking attempt
                    if form.start_date.data <= booking.initial_date_time and booking.initial_date_time <= form.start_date.data + timedelta(hours = hours):
                        flash("The current booking conflicts with an existing booking", 'danger')
                        logger.info("booking not made: pre-existing booking for scooter " +
                                        str(form.scooter_id.data) +
                                        " within range " +
                                        str(form.start_date.data) +
                                        " - " +
                                        str(form.start_date.data + timedelta(hours = hours)))
                        return render_template('booking1_admin.html',
                                                title='Choose a Location',
                                                form = form,
                                                hire_periods = hire_periods)
                #check upcoming bookings
                for booking in current_upcoming_bookings:
                    #check that the selected start date doesn't fall during a booking
                    if form.start_date.data >= booking.initial_date_time and form.start_date.data <= booking.final_date_time:
                        flash("The scooter is unavailable for that start time", 'danger')
                        logger.info("booking not made: scooter " +
                                        str(form.scooter_id.data) +
                                        " unavailable at " +
                                        str(form.start_date.data))
                        return render_template('booking1_admin.html',
                                                title='Choose a Location',
                                                form = form,
                                                hire_periods = hire_periods)
                    #check that the projected end date doesn't fall during a booking
                    if form.start_date.data + timedelta(hours = hours) >= booking.initial_date_time and form.start_date.data + timedelta(hours = hours) <= booking.final_date_time:
                        flash("The projected end time falls within a pre-existing booking", 'danger')
                        logger.info("booking not made: pre-existing booking for scooter " +
                                        str(form.scooter_id.data) +
                                        " within range " +
                                        str(form.start_date.data) +
                                        " - " +
                                        str(form.start_date.data + timedelta(hours = hours)))
                        return render_template('booking1_admin.html',
                                                title='Choose a Location',
                                                form = form,
                                                hire_periods = hire_periods)

                    #check that the current booking doesn't completely overlap a booking
                    #if the start time for a booking is during the current booking attempt
                    if form.start_date.data <= booking.initial_date_time and booking.initial_date_time <= form.start_date.data + timedelta(hours = hours):
                        flash("The current booking conflicts with an existing booking", 'danger')
                        logger.info("booking not made: pre-existing booking for scooter " +
                                        str(form.scooter_id.data) +
                                        " within range " +
                                        str(form.start_date.data) +
                                        " - " +
                                        str(form.start_date.data + timedelta(hours = hours)))
                        return render_template('booking1_admin.html',
                                                title='Choose a Location',
                                                form = form,
                                                hire_periods = hire_periods)

                #store the booking details as a session to be used on successful payment
                session['booking_duration'] = hours
                session['booking_cost'] = cost
                session['booking_initial'] = form.start_date.data
                session['booking_final'] = form.start_date.data + timedelta(hours = hours)
                session['booking_user_id'] = 0
                session['booking_email'] = form.email.data
                session['booking_scooter_id'] = int(form.scooter_id.data)
                session['booking_collection_id'] = int(form.location_id.data)

                #check if the booking should be currently active or upcoming
                if session.get('booking_initial', None) < datetime.utcnow():
                    #if the start time is before now, it's currently active
                    session['booking_status'] = "active"
                else:
                    #else it must be in the future
                    session['booking_status'] = "upcoming"

                #send admin user to payment page
                return redirect("/card")

            #send current_user to the admin version of the booking1 page
            return render_template('booking1_admin.html',
                                    title='Choose a Location',
                                    form = form,
                                    hire_periods = hire_periods)
    except Exception as e:
        logger.error(e)
        if current_user.is_anonymous:
            return redirect('/')
            # str(current_user.id)
        elif current_user.account_type == "employee" or current_user.account_type == "manager":
            return redirect('/admin_dashboard')
        else:
            return redirect("/user_dashboard")

@app.route('/booking1/<location_id>')
@login_required
def booking1_location(location_id):
    scooters = models.scooter.query.filter_by(collection_id = location_id, availability = 1).all()

    scooterArray = []

    for scooter in scooters:
        scooterObj = {}
        scooterObj['id'] = scooter.id
        scooterArray.append(scooterObj)

    return jsonify({'scooters' : scooterArray})


@app.route('/booking2')
@login_required
def booking2():
    try:
        logPage()
        booking = models.booking.query.filter_by(id = session.get('booking_id', None)).first()

        location = models.collection_point.query.filter_by(id = booking.collection_id).first().location

        # user is a customer
        if not current_user.account_type == "employee" and not current_user.account_type == "manager":
            email = current_user.email
            isCustomer = True
        else:
            email = session.get('booking_email', None)
            isCustomer = False


        if session.get('booking_duration', None) == 1:
            session['booking_period'] = "1 Hour"
        elif session.get('booking_duration', None) == 4:
            session['booking_period'] = "4 Hours"
        elif session.get('booking_duration', None) == 24:
            session['booking_period'] = "1 Day"
        elif session.get('booking_duration', None) == 168:
            session['booking_period'] = "1 Week"

        return render_template('booking2.html',
                                title='Booking Confirmation',
                                email = email,
                                isCustomer = isCustomer,
                                booking=booking,
                                location=location)
    except Exception as e:
        logger.error(e)
        if current_user.is_anonymous:
            return redirect('/')
            # str(current_user.id)
        elif current_user.account_type == "employee" or current_user.account_type == "manager":
            return redirect('/admin_dashboard')
        else:
            return redirect("/user_dashboard")


#intermediary page for cancelling booking
@app.route('/cancel_this_booking/<booking_id>')
@login_required
def cancel_this_booking(booking_id):
    if current_user.account_type != 'customer': # Check if the logged in user is a customer or admin (True if employee/manager, False if customer)
        return redirect('/admin_dashboard') # Redirect any non-customer users to the admin dashboard

    session['booking_id'] = booking_id

    return redirect(url_for('cancel_booking'))


@app.route('/cancel_booking', methods=('GET', 'POST'))
@login_required
def cancel_booking():
    if current_user.account_type != 'customer': # Check if the logged in user is a customer or admin (True if employee/manager, False if customer)
        return redirect('/admin_dashboard') # Redirect any non-customer users to the admin dashboard

    try:
        logPage()

        booking = models.booking.query.filter_by(id = session.get('booking_id', None)).first()
        collection_points = models.collection_point

        #if the confirm cancellation button is pressed
        if request.method == 'POST':
            #delete the transaction only if it is an upcoming booking
            #we do this by deleting the first transaction with that hire_period, and that user_id
            #slight problem with this, because we don't store when a booking is made in the booking table, we can't tell which booking we're deleting
            #right now we're deleting all bookings that appears with this duration and ID, reason is that delete only works with queries, not single row entities
            # if booking.status == "upcoming":
            #     models.transactions.query.filter_by(hire_period = booking.duration).filter_by(user_id = booking.id).delete()

            #delete the actual booking
            models.booking.query.filter_by(id = session.get('booking_id', None)).first().status = "cancelled"

            try:
                db.session.commit()
            except:
                db.session.rollback()

            flash("Booking successfully cancelled!", "success")
            logger.info("booking " + str(session.get('booking_id')) + " cancelled")
            return redirect(url_for('profile'))

        return render_template('cancel_booking.html',
                                title='Cancel Booking',
                                booking=booking,
                                collection_points=collection_points)
    except Exception as e:
        logger.error(e)
        if current_user.is_anonymous:
            return redirect('/')
            # str(current_user.id)
        elif current_user.account_type == "employee" or current_user.account_type == "manager":
            return redirect('/admin_dashboard')
        else:
            return redirect("/user_dashboard")


#intermediary page for extending booking
@app.route('/extend_this_booking/<booking_id>')
@login_required
def extend_this_booking(booking_id):
    if current_user.account_type != 'customer': # Check if the logged in user is a customer or admin (True if employee/manager, False if customer)
        return redirect('/admin_dashboard') # Redirect any non-customer users to the admin dashboard

    logPage()
    session['booking_id'] = booking_id

    return redirect(url_for('extend_booking'))


#extend booking page that takes info from the page in between profile and extend
@app.route('/extend_booking', methods=('GET', 'POST'))
@login_required
def extend_booking():
    if current_user.account_type != 'customer': # Check if the logged in user is a customer or admin (True if employee/manager, False if customer)
        return redirect('/admin_dashboard') # Redirect any non-customer users to the admin dashboard

    try:
        logPage()
        form = ExtendBookingForm()
        booking = models.booking.query.filter_by(id = session.get('booking_id', None)).first()
        collection_points = models.collection_point

        #when the form is submitted
        if form.is_submitted():
            #convert the option selected in the SelectField into a cost and the number of hours
            if form.hire_period.data == '1':
                cost = models.pricing.query.filter_by(id = 1).first().price
                hours = 1
            elif form.hire_period.data == '2':
                cost = models.pricing.query.filter_by(id = 2).first().price
                hours = 4
            elif form.hire_period.data == '3':
                cost = models.pricing.query.filter_by(id = 3).first().price
                hours = 24
            elif form.hire_period.data == '4':
                cost = models.pricing.query.filter_by(id = 4).first().price
                hours = 168
            else:
                cost = 10.00
                hours = 1

            #check every booking made with this scooter
            #make sure that the currently selected start date & end date DO NOT fall within start and end of any the bookings
            #only check currently "upcoming" or "active" bookings
            current_active_bookings = models.booking.query.filter_by(scooter_id = booking.scooter_id, status = "active")
            current_upcoming_bookings = models.booking.query.filter_by(scooter_id = booking.scooter_id, status = "upcoming")
            #check active bookings
            for bookingA in current_active_bookings:
                #as long as the new final date time after extention has run past any other booking's start time it fails
                if booking.final_date_time + timedelta(hours = hours) >= bookingA.initial_date_time and booking.id != bookingA.id:
                    flash("The extention would conflict with and existing booking", 'danger')
                    logger.info("extention not made: scooter " +
                                    str(booking.scooter_id) +
                                    " unavailable to extend until " +
                                    str(booking.final_date_time + timedelta(hours = hours)))
                    return render_template('extend_booking.html',
                                            title='Extend Booking',
                                            booking=booking,
                                            form=form,
                                            collection_points=collection_points)
            #check upcoming bookings
            for bookingU in current_upcoming_bookings:
                #as long as the new final date time after extention has run past any other booking's start time it fails
                if booking.final_date_time + timedelta(hours = hours) >= bookingU.initial_date_time and booking.id != bookingU.id:
                    flash("The extention would conflict with and existing booking", 'danger')
                    logger.info("extention not made: scooter " +
                                    str(booking.scooter_id) +
                                    " unavailable to extend until " +
                                    str(booking.final_date_time + timedelta(hours = hours)))
                    return render_template('extend_booking.html',
                                            title='Extend Booking',
                                            booking=booking,
                                            form=form,
                                            collection_points=collection_points)

            #check if user has saved card details
            exists = models.card_details.query.filter_by(user_id = current_user.id).first() is not None
            if(exists):
                #has card details
                #extend the booking pointed to by the 'booking_id' in the session, and add to the cost
                booking.duration = booking.duration + hours

                #Check if user is a discounted user when the booking is extended
                #if the user is a student or a senior apply the discount
                if current_user.user_type == "senior" or current_user.user_type == "student":
                    flash("you are eligible for a student/senior discount", "info")
                    logger.info("(user " + str(current_user.id) + ") eligible for discount")
                    cost = cost * (0.8)

                else :
                    bookings =  models.booking.query.filter_by(email = current_user.email, status = "expired") # expired user booking
                    total_hours = 0 # total hours in the past week

                    #find the datetime a week ago
                    today_date = datetime.now()
                    days = timedelta(days = 7)
                    week_date = today_date - days

                    #check if they are a frequent user
                    for b in bookings :
                        if (b.initial_date_time > week_date):
                            total_hours += b.duration
                            if (total_hours > 8):
                                break

                    if (total_hours >= 8) :
                        logger.info("(user " + str(current_user.id) + ") eligible for discount")
                        cost = cost * (0.8)

                booking.cost = booking.cost + cost
                booking.final_date_time = booking.final_date_time + timedelta(hours = hours)

                #add a new transaction, with the date for the transaction set as now
                new_transaction = models.transactions(hire_period = hours,
                                                    booking_time = datetime.utcnow(),
                                                    transaction_cost = cost,
                                                    user_id = current_user.id,
                                                    booking_id = booking.id)
                db.session.add(new_transaction)

                try:
                    db.session.commit()
                except:
                    db.session.rollback()

                #write the email message
                msg = Message('Booking Extension Confirmation',
                                sender='scootersleeds@gmail.com',
                                recipients=[current_user.email])

                msg.body = (f'Thank You, your booking extension has been confirmed. \nStart Date and Time: ' + str(booking.initial_date_time) +
                '\nEnd Date and Time: ' + str(booking.final_date_time) +
                '\nScooter ID: ' + str(booking.scooter_id) +
                '\nReference Number: ' + str(booking.id))
                mail.send(msg)

                flash("Booking Extension Successful!", "success")
                # get correct string for printing to log
                if str(form.hire_period.data) == "1":
                    log_duration = "1 hour"
                elif str(form.hire_period.data) == "2":
                    log_duration = "4 hours"
                elif str(form.hire_period.data) == "3":
                    log_duration = "1 day"
                elif str(form.hire_period.data) == "4":
                    log_duration = "1 week"
                else:
                    log_duration = "|" + str(form.hire_period.data) + "|"
                logger.info("(user " + str(current_user.id) +
                                ") booking " +
                                str(booking.id) +
                                " extended by " +
                                log_duration)
                return redirect(url_for('profile'))
            else:
                #doesn't have card details
                #need to tell the /card page that we're extending, not booking a new booking
                session['extending'] = 'True'
                session['extend_hours'] = hours
                session['extend_cost'] = cost
                return redirect(url_for('card'))

        return render_template('extend_booking.html',
                                title='Extend Booking',
                                booking=booking,
                                form=form,
                                collection_points=collection_points)
    except Exception as e:
        logger.error(e)
        if current_user.is_anonymous:
            return redirect('/')
            # str(current_user.id)
        elif current_user.account_type == "employee" or current_user.account_type == "manager":
            return redirect('/admin_dashboard')
        else:
            return redirect("/user_dashboard")

#Admin exclusive pages
@app.route('/admin_dashboard')
@login_required
def admin_dashboard():
    if current_user.account_type not in ['employee', 'manager']: # Check if the logged in user is an admin-type or a customer
        print("not an admin user, redirect to user dashboard")
        return redirect('/user_dashboard') # Redirect and non-admin users to the user dashboard

    try:
        logPage()
        #clean up bookings table
        organise_bookings()
        return render_template('admin_dashboard.html',
                                name=current_user.name,
                                title='Admin Dashboard',
                                admin_type=current_user.account_type)
    except Exception as e:
        logger.error(e)
        if current_user.is_anonymous:
            return redirect('/')
            # str(current_user.id)
        elif current_user.account_type == "employee" or current_user.account_type == "manager":
            return redirect('/admin_dashboard')
        else:
            return redirect("/user_dashboard")


@app.route('/review_feedback', methods=('GET', 'POST'))
@login_required
def review_feedback():
    if current_user.account_type not in ['employee',
                                         'manager']:  # Check if the logged in user is an admin-type or a customer
        return redirect('/user_dashboard')  # Redirect and non-admin users to the user dashboard

    try:
        logPage()
        employee = (current_user.account_type == 'employee') # True if 'employee', False if 'manager'
        if employee:
            recs = models.feedback.query.filter_by(priority=0, resolved=0) # Employee meant to see low priority
        else:
            recs = models.feedback.query.filter_by(priority=1, resolved=0) # Manager meant to see high priority
        return render_template('review_feedback.html',
                                title='Review Customer Feedback', recs=recs)
    except Exception as e:
        logger.error(e)
        if current_user.is_anonymous:
            return redirect('/')
            # str(current_user.id)
        elif current_user.account_type == "employee" or current_user.account_type == "manager":
            return redirect('/admin_dashboard')
        else:
            return redirect("/user_dashboard")

@app.route('/edit_feedback/<id>', methods=('GET', 'POST'))
@login_required
def edit_feedback(id):
    if current_user.account_type not in ['employee',
                                         'manager']:  # Check if the logged in user is an admin-type or a customer
        return redirect('/user_dashboard')  # Redirect and non-admin users to the user dashboard

    logPage()
    form = EditFeedbackForm()
    rec = models.feedback.query.filter_by(id=id).first()

    if request.method == 'POST':
        f = models.feedback.query.filter_by(id=id).first()

        if form.priority.data:
            f.priority = (f.priority + 1) % 2 # Toggles high priority (1 goes to 0, 0 goes to 1)

        if form.resolve.data:
            f.resolved = (f.resolved + 1) % 2 # Toggles resolved (1 goes to 0, 0 goes to 1)

        try:
            db.session.commit()
        except:
            db.session.rollback()
        return redirect(url_for('review_feedback'))

    return render_template('edit_feedback.html', rec=rec, form=form)


@app.route('/view_scooters', methods=['GET', 'POST'])
@login_required
def view_scooters():
    if current_user.account_type not in ['employee',
                                         'manager']:  # Check if the logged in user is an admin-type or a customer
        return redirect('/user_dashboard')  # Redirect and non-admin users to the user dashboard

    logPage()
    #synchronise scooters and Locations
    organise_scooters()

    rec = models.scooter.query.all() # retrieve all scooters
    form = ConfigureScooterForm()

    # redirect to configure scooter page with the selected scooter
    if request.method == 'POST':
        id = request.form["edit_button"]
        u = models.scooter.query.get(id)
        session['confg_sctr_id'] = u.id
        return redirect(url_for('configure_scooter'))

    return render_template('view_scooters.html',
                            title='View Scooters', rec=rec)


@app.route('/add_scooter', methods=['GET','POST'])
@login_required
def add_scooter():
    if current_user.account_type not in ['employee',
                                         'manager']:  # Check if the logged in user is an admin-type or a customer
        return redirect('/user_dashboard')  # Redirect and non-admin users to the user dashboard

    logPage()
    form = AddScooterForm()

    if form.validate_on_submit():
        u = models.scooter(availability = form.availability.data, collection_id = form.location_id.data)
        db.session.add(u)    # add scooter to db
        try:
            db.session.commit()
        except:
            db.session.rollback()     # commit scooter to db
        now = str(datetime.now())
        logger.info("admin has added a scooter with ID: "+ str(u.id))
        return redirect('/view_scooters')
    return render_template('add_scooter.html',
                            title='Add New Scooter', form=form)


@app.route('/configure_scooter', methods=['GET', 'POST'])
@login_required
def configure_scooter():
    if current_user.account_type not in ['employee',
                                         'manager']:  # Check if the logged in user is an admin-type or a customer
        return redirect('/user_dashboard')  # Redirect and non-admin users to the user dashboard

    logPage()
    #retrieve details to display and store in form
    scooter = models.scooter.query.get(session['confg_sctr_id'])

    form = ConfigureScooterForm()
    form.scooter_id.data = session['confg_sctr_id']
    form.availability.data = scooter.availability
    form.location_id.data = scooter.collection_id

    if request.method == 'POST':
        # update details if user clicks confirm
        if request.form.get("cancel") is None:
            scooter.availability = request.form.get("availability")
            scooter.collection_id = request.form.get("location_id")
            try:
                db.session.commit()
            except:
                db.session.rollback()
            # print(models.scooter.query.all())
            flash(f'Scooter Details Updated', 'success')
            logger.info("scooter " + str(scooter.id) + " configured - availability: " + str(scooter.availability) + ", location ID: " + str(scooter.collection_id))
        return redirect(url_for('view_scooters'))
    return render_template('configure_scooter.html',
                            title='Configure A Scooter', form=form)


@app.route('/configure_costs', methods =['GET', 'POST'])
@login_required
def configure_costs():
    if current_user.account_type not in ['employee',
                                         'manager']:  # Check if the logged in user is an admin-type or a customer
        return redirect('/user_dashboard')  # Redirect and non-admin users to the user dashboard

    logPage()
    rec = models.pricing.query.all()
    form = PricesForm()

    if form.validate_on_submit():
        #assign corresponding db value based on the SelectForm value.

        if form.duration.data == "1":
            durationToCheck = "1 Hour"
        if form.duration.data == "2":
            durationToCheck = "4 Hours"
        if form.duration.data == "3":
            durationToCheck = "1 Day"
        if form.duration.data == "4":
            durationToCheck = "1 Week"

        #find record and change price.
        dur = models.pricing.query.filter_by(duration = durationToCheck).first()
        if dur:
            #need to round the price to 2 dp
            dur.price = round(form.price.data, 2)
            flash("Price updated", "success")
            logger.info("scooter costs configured: " + str(dur.id) + " set to " +  str(dur.price))
        else:
            flash("Error price not updated", 'danger')
            logger.info("scooter costs configuration failed")

        try:
            db.session.commit()
        except:
            db.session.rollback()     # commit scooter to db
    else:
        if form.price.data != None:
            flash("Invalid form data", 'danger')
            logger.info("scooter costs configuration failed")
    return render_template('configure_costs.html',
                            rec=rec, form=form)


@app.route('/sales_metrics')
@login_required
def sales_metrics():
    if current_user.account_type not in ['employee',
                                         'manager']:  # Check if the logged in user is an admin-type or a customer
        return redirect('/user_dashboard')  # Redirect and non-admin users to the user dashboard

    logPage()
    one_hour_metric, four_hour_metric, one_day_metric, one_week_metric = 0, 0, 0, 0
    # calculate the date range needed
    date = datetime.utcnow()
    week_start = date + timedelta(-date.weekday(), weeks=0)
    week_end = date + timedelta(-date.weekday() + 6, weeks=0)

    # get all the transations
    transactions = models.transactions.query.all()

    # for each transaction in if it is within the last week count it to the correct metric
    # need to multiply by the cost of each
    for transaction in transactions:
        if transaction.hire_period == 1 and transaction.booking_time > week_start and transaction.booking_time < week_end:
            one_hour_metric += transaction.transaction_cost
        elif transaction.hire_period == 4 and transaction.booking_time > week_start and transaction.booking_time < week_end:
            four_hour_metric += transaction.transaction_cost
        elif transaction.hire_period == 24 and transaction.booking_time > week_start and transaction.booking_time < week_end:
            one_day_metric += transaction.transaction_cost
        elif transaction.hire_period == 168 and transaction.booking_time > week_start and transaction.booking_time < week_end:
            one_week_metric += transaction.transaction_cost

    # Calculate the metrics
    # Graph the hire period metrics
    plt.bar([0,1,2,3], [one_hour_metric, four_hour_metric, one_day_metric, one_week_metric], tick_label=['One Hour', 'Four Hours', 'One Day', 'One Week'])
    plt.xlabel('Hire Period')
    plt.ylabel('Revenue (£)')
    plt.savefig('app/static/graphs/hireperiod.jpg')
    plt.figure().clear()
    plt.close()
    plt.cla()
    plt.clf()

    # Combined daily income metrics
    monday_metrics, tuesday_metrics, wednesday_metrics, thursday_metrics, friday_metrics, saturday_metrics, sunday_metrics = 0, 0,0,0,0,0,0

    # Get all the bookings and calculate booking metric for each day
    bookings = models.booking.query.all()
    for booking in bookings:
        if booking.status != "cancelled": # only adds booking that were not cancelled to the metrics
            # checks what day the booking was started
            if booking.initial_date_time.weekday() == 0 and booking.initial_date_time > week_start and booking.initial_date_time < week_end and booking.duration < 168: # Monday
                monday_metrics += booking.cost
            elif booking.initial_date_time.weekday() == 1 and booking.initial_date_time > week_start and booking.initial_date_time < week_end and booking.duration < 168: # Tuesday
                tuesday_metrics += booking.cost
            elif booking.initial_date_time.weekday() == 2 and booking.initial_date_time > week_start and booking.initial_date_time < week_end and booking.duration < 168: # Wednesday
                wednesday_metrics += booking.cost
            elif booking.initial_date_time.weekday() == 3 and booking.initial_date_time > week_start and booking.initial_date_time < week_end and booking.duration < 168: # Thursday
                thursday_metrics += booking.cost
            elif booking.initial_date_time.weekday() == 4 and booking.initial_date_time > week_start and booking.initial_date_time < week_end and booking.duration < 168: # Friday
                friday_metrics += booking.cost
            elif booking.initial_date_time.weekday() == 5 and booking.initial_date_time > week_start and booking.initial_date_time < week_end and booking.duration < 168: # Saturday
                saturday_metrics += booking.cost
            elif booking.initial_date_time.weekday() == 6 and booking.initial_date_time > week_start and booking.initial_date_time < week_end and booking.duration < 168: # Sunday
                sunday_metrics += booking.cost

    # Graph the daily metrics
    plt.bar([0,1,2,3,4,5,6], [monday_metrics, tuesday_metrics, wednesday_metrics, thursday_metrics, friday_metrics, saturday_metrics, sunday_metrics], tick_label=['Mon', 'Tues', 'Weds', 'Thurs', 'Fri', 'Sat', 'Sun'])
    plt.xlabel('Day of Week')
    plt.ylabel('Revenue (£)')
    plt.savefig('app/static/graphs/daily.jpg')
    plt.figure().clear()
    plt.close()
    plt.cla()
    plt.clf()

    # discounted vs undiscounted transactions made last week
    discounted_transactions, normal_transactions = 0, 0
    for transaction in transactions:
        if transaction.booking_time > week_start:
            if(transaction.user != None):
                if(transaction.user.user_type == "student" or transaction.user.user_type == "senior"): # if the transaction is a discounted transaction
                    discounted_transactions += 1
            else:
                normal_transactions += 1

    # Graph the discounted vs undiscounted transactions
    plt.bar([0,1], [discounted_transactions, normal_transactions], tick_label=['Discounted transactions', 'Normal transactions'])
    plt.xlabel('Type of transaction')
    plt.ylabel('Count')
    plt.savefig('app/static/graphs/transaction_type.jpg')
    plt.figure().clear()
    plt.close()
    plt.cla()
    plt.clf()

    logger.info("sales metrics successfully created")

    return render_template('sales_metrics.html',
                            title='View Sales Metrics',
                            one_hour_metric = one_hour_metric,
                            four_hour_metric = four_hour_metric,
                            one_day_metric = one_day_metric,
                            one_week_metric = one_week_metric,
                            week_start = week_start,
                            week_end = week_end,
                            monday_metrics = monday_metrics,
                            tuesday_metrics = tuesday_metrics,
                            wednesday_metrics = wednesday_metrics,
                            thursday_metrics = thursday_metrics,
                            friday_metrics = friday_metrics,
                            saturday_metrics = saturday_metrics,
                            sunday_metrics = sunday_metrics,
                            discounted_transactions = discounted_transactions,
                            normal_transactions = normal_transactions)
