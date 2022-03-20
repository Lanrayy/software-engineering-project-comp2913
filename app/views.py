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
import logging
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
            booking.status = "past"

    #finalise changes
    db.session.commit()
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
    db.session.commit()
    return 0

#Unregistered user exclusive pages
@app.route('/')
def index():
    return render_template('landing_page.html',
                            title='Home')


@app.route('/info')
def info():
    return render_template('info.html',
                            title='How it Works')

global now

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
        u = models.user(password = hashed_password, email = form.email.data, account_type = "customer", user_type = form.user_type.data, name = form.name.data)
        db.session.add(u)    # add user to db
        db.session.commit()     # commit user to db

        now = str(datetime.now())
        app.logger.info(u.email+" Created an account at "+ now)
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
        if u:
            if bcrypt.check_password_hash(u.password, form.password.data):
                login_user(u)
                flash('Login Successful!', 'success')
                now = str(datetime.now())
                app.logger.info(u.email+"logged in at "+ now)
                if(u.account_type == "employee" or u.account_type == "manager"):
                    return redirect(url_for('admin_dashboard'))
                else:
                    return redirect(url_for('user_dashboard'))
            else:
                now = str(datetime.now())
                app.logger.info(u.email + " unsuccesfull login at "+ now)
        else:
            now = str(datetime.now())
            app.logger.info("unsuccesfull login at " + now)

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
        #if the card details check out
        if form.validate_on_submit():
            app.logger.info("Card form successfully submitted")
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
                db.session.commit()
                flash("Card details saved")
                app.logger.info("Card details saved")

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
                                                        user_id = current_user.id)
                    db.session.add(new_transaction)
                    db.session.commit()
                    app.logger.info("New transaction added to transaction table")

                    #write the email message
                    msg = Message('Booking Extension Confirmation',
                                    sender='scootersleeds@gmail.com',
                                    recipients=[current_user.email])

                    msg.body = (f'Thank You, your booking extension has been confirmed. \nStart Date and Time: ' + str(booking.initial_date_time) +
                    '\nEnd Date and Time: ' + str(booking.final_date_time) +
                    '\nScooter ID: ' + str(booking.scooter_id) +
                    '\nReference Number: ' + str(booking.id))
                    mail.send(msg)
                    app.logger.info("Email sent to user successfully")

                    flash("Booking Extension Successful!")
                    app.logger.info("Booking Extension Successful!")

                    return redirect("/profile")
            else:
                # not extending, so booking
                # if admin is is making a booking, the booking_user_id = 0
                if session.get('booking_user_id') == 0:
                    #admin is making the booking
                    app.logger.info("Admin user is making a booking on behalf of a customer")
                    booking = models.booking(duration = session.get('booking_duration', None),
                                             status= session.get('booking_status', None),
                                             cost = session.get('booking_cost', None),
                                             initial_date_time = session.get('booking_initial', None),
                                             final_date_time = session.get('booking_final', None),
                                             email = session.get('booking_email', None),
                                             scooter_id = session.get('booking_scooter_id', None),
                                             collection_id = session.get('booking_collection_id', None))
                    db.session.add(booking)
                    # add new transaction to the transaction table- used on the metrics page, no user id
                    new_transaction = models.transactions(hire_period = session.get('booking_duration', None),
                                                        booking_time = datetime.utcnow())
                    db.session.add(new_transaction)
                    #set the specified email to recipient
                    recipients=[session.get('booking_email', None)]
                else:
                    #user is making the booking
                    app.logger.info("Customer is making a booking")
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
                    # add new transaction to the transaction table- used on the metrics page, with user id
                    new_transaction = models.transactions(hire_period = session.get('booking_duration', None),
                                                        booking_time = datetime.utcnow(),
                                                        user_id = session.get('booking_user_id', None))
                    db.session.add(new_transaction)
                    app.logger.info("New transaction added to transaction table")
                    #set user to recipient
                    recipients=[current_user.email]

                db.session.commit()

                msg = Message('Booking Confirmation',
                                sender='scootersleeds@gmail.com',
                                recipients=recipients)

                msg.body = (f'Thank You, your booking has been confirmed. \nStart Date and Time: ' + str(booking.initial_date_time) +
                '\nEnd Date and Time: ' + str(booking.final_date_time) +
                '\nScooter ID: ' + str(booking.scooter_id) +
                '\nReference Number: ' + str(booking.id))
                mail.send(msg)

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
    #clean up bookings table
    organise_bookings()
    return render_template('user_dashboard.html',
                            name=current_user.name,
                            title='User Dashboard')


@app.route('/pricing')
def pricing():
    return render_template('pricing.html',
                            title='Our Prices')

@app.route('/delete/<int:id>', methods=['GET', 'POST'])
def delete(id):
    #to_complete is a variable to get the id passed by pressing the complete button
    to_delete=models.cards.query.get_or_404(id)

    try:
        #change the status value of this id into complete and commit to the database
        db.session.delete(to_delete)
        db.session.commit()

        return redirect('/profile')

    except:
        return 'there was an error'


@app.route('/profile', methods=['GET', 'POST'])
def profile():
    #clean up bookings table
    organise_bookings()

    #filter the query into the bookings and card
    #cards = models.card_details.query.filter_by(user_id = current_user.id)  #FOREIGN KEY
    cards = models.card_details.query.all()
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


@app.route('/send_feedback', methods=('GET', 'POST'))
def send_feedback():
    form = FeedbackForm()

    if request.method == 'POST':
        f = models.feedback(message=form.feedback.data, priority=0, resolved=0)
        db.session.add(f)
        db.session.commit()
        flash(f'Feedback Submitted', 'success')
        return redirect(url_for('send_feedback'))
    return render_template('send_feedback.html',
                            title='Send Us Your Feedback',
                            form=form)


@app.route('/locations')
def locations():
    return render_template('locations.html',
                            title='Pickup Locations')




@app.route('/booking1', methods=['GET', 'POST'])
def booking1():
    #clean up bookings table
    organise_bookings()
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
                flash("Please choose a location with available scooters")
                return render_template('booking1_user.html',
                                        title='Choose a Location',
                                        form = form)

            #check that they actually put a start date
            if form.start_date.data == None:
                flash("Please enter a valid date")
                return render_template('booking1_user.html',
                                        title='Choose a Location',
                                        form = form)

            #check if the start date further in the past than now, with a grace period of 5 minutes
            if form.start_date.data < datetime.utcnow() + timedelta(minutes = -5):
                flash("The start date can't be in the past")
                return render_template('booking1_user.html',
                                        title='Choose a Location',
                                        form = form)

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
                flash("you are eligible for a student/senior discount")
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
                    flash("you are eligible for a frequent user discount")
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
                    flash("The scooter is unavailable for that start time")
                    return render_template('booking1_user.html',
                                            title='Choose a Location',
                                            form = form)
                #check that the projected end date doesn't fall during a booking
                if form.start_date.data + timedelta(hours = hours) >= booking.initial_date_time and form.start_date.data + timedelta(hours = hours) <= booking.final_date_time:
                    flash("The projected end time falls within a pre-existing booking")
                    return render_template('booking1_user.html',
                                            title='Choose a Location',
                                            form = form)
            #check upcoming bookings
            for booking in current_upcoming_bookings:
                #check that the selected start date doesn't fall during a booking
                if form.start_date.data >= booking.initial_date_time and form.start_date.data <= booking.final_date_time:
                    flash("The scooter is unavailable for that start time")
                    return render_template('booking1_user.html',
                                            title='Choose a Location',
                                            form = form)
                #check that the projected end date doesn't fall during a booking
                if form.start_date.data + timedelta(hours = hours) >= booking.initial_date_time and form.start_date.data + timedelta(hours = hours) <= booking.final_date_time:
                    flash("The projected end time falls within a pre-existing booking")
                    return render_template('booking1_user.html',
                                            title='Choose a Location',
                                            form = form)

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
                                                    user_id = session.get('booking_user_id', None))
                db.session.add(new_transaction)

                db.session.commit()



                session['booking_id'] = booking.id

                msg = Message('Booking Confirmation',
                                sender='scootersleeds@gmail.com',
                                recipients=[current_user.email])

                msg.body = (f'Thank You, your booking has been confirmed. \nStart Date and Time: ' + str(booking.initial_date_time) +
                '\nEnd Date and Time: ' + str(booking.final_date_time) +
                '\nScooter ID: ' + str(booking.scooter_id) +
                '\nReference Number: ' + str(booking.id))
                mail.send(msg)

                flash("Booking Successful!")
                return redirect("/booking2") #send to booking confirmation
            else:
                #user does not have existing
                return redirect("/card")

        #send the current user to the user version of the booking1 page
        return render_template('booking1_user.html',
                                title='Choose a Location',
                                form=form,
                                data=data,
                                card_found=card_found)

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
                flash("Please choose a location with available scooters")
                return render_template('booking1_admin.html',
                                        title='Choose a Location',
                                        form = form)

            #check that they actually put a start date
            if form.start_date.data == None:
                flash("Please enter a valid date")
                return render_template('booking1_admin.html',
                                        title='Choose a Location',
                                        form = form)

            #check if the start date further in the past than now, with a grace period of 5 minutes
            if form.start_date.data < datetime.utcnow() + timedelta(minutes = -5):
                flash("The start date can't be in the past")
                return render_template('booking1_admin.html',
                                        title='Choose a Location',
                                        form = form)

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

            #**************************************************************************
            #**********************APPLY DISCOUNT**************************************
            #**************************************************************************

            #if the user is a student or a senior apply the discount
            if current_user.user_type == "senior" or current_user.user_type == "student":
                flash("you are eligible for a student/senior discount")
                cost = cost * (0.8)

            else :
                bookings =  models.booking.query.filter_by(email = current_user.email, status = "expired") # expired user booking
                total_hours = 0 # total hours in the past week

                #find the datetime a week ago
                today_date = datetime.now()
                days = timedelta(days = 7)
                week_date = today_date - days

                for b in bookings :
                    if (b.initial_date_time > week_date):
                        total_hours += b.duration
                        if (total_hours > 8):
                            break

                if (total_hours >= 8) :
                    flash("you are eligible for a frequent user discount")
                    cost = cost * (0.8)

            #**************************************************************************
            #**************************************************************************

            #check every booking made with this scooter
            #make sure that the currently selected start date & end date DO NOT fall within start and end of any the bookings
            #only check currently "upcoming" or "active" bookings
            current_active_bookings = models.booking.query.filter_by(scooter_id = form.scooter_id.data, status = "active")
            current_upcoming_bookings = models.booking.query.filter_by(scooter_id = form.scooter_id.data, status = "upcoming")
            #check active bookings
            for booking in current_active_bookings:
                #check that the selected start date doesn't fall during a booking
                if form.start_date.data >= booking.initial_date_time and form.start_date.data <= booking.final_date_time:
                    flash("The scooter is unavailable for that start time")
                    return render_template('booking1_admin.html',
                                            title='Choose a Location',
                                            form = form)
                #check that the projected end date doesn't fall during a booking
                if form.start_date.data + timedelta(hours = hours) >= booking.initial_date_time and form.start_date.data + timedelta(hours = hours) <= booking.final_date_time:
                    flash("The projected end time falls within a pre-existing booking")
                    return render_template('booking1_admin.html',
                                            title='Choose a Location',
                                            form = form)
            #check upcoming bookings
            for booking in current_upcoming_bookings:
                #check that the selected start date doesn't fall during a booking
                if form.start_date.data >= booking.initial_date_time and form.start_date.data <= booking.final_date_time:
                    flash("The scooter is unavailable for that start time")
                    return render_template('booking1_admin.html',
                                            title='Choose a Location',
                                            form = form)
                #check that the projected end date doesn't fall during a booking
                if form.start_date.data + timedelta(hours = hours) >= booking.initial_date_time and form.start_date.data + timedelta(hours = hours) <= booking.final_date_time:
                    flash("The projected end time falls within a pre-existing booking")
                    return render_template('booking1_admin.html',
                                            title='Choose a Location',
                                            form = form)

            #store the booking details as a session to be used on successful payment
            session['booking_duration'] = hours
            session['booking_cost'] = cost
            session['booking_initial'] = form.start_date.data
            session['booking_final'] = form.start_date.data + timedelta(hours = hours)
            session['booking_user_id'] = 0
            session['booking_email'] = form.email.data
            session['booking_scooter_id'] = int(form.scooter_id.data)
            session['booking_collection_id'] = int(form.location_id.data)

            #send admin user to payment page
            return redirect("/card")

        #send current_user to the admin version of the booking1 page
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

    location = models.collection_point.query.filter_by(id = booking.collection_id).first().location

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
                            booking=booking,
                            location=location)


#intermediary page for cancelling booking
@app.route('/cancel_this_booking/<booking_id>')
def cancel_this_booking(booking_id):
    session['booking_id'] = booking_id

    return redirect(url_for('cancel_booking'))


@app.route('/cancel_booking', methods=('GET', 'POST'))
def cancel_booking():

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

        db.session.commit()

        flash("Booking successfully cancelled!")

        return redirect(url_for('profile'))

    return render_template('cancel_booking.html',
                            title='Cancel Booking',
                            booking=booking,
                            collection_points=collection_points)


#intermediary page for extending booking
@app.route('/extend_this_booking/<booking_id>')
def extend_this_booking(booking_id):
    session['booking_id'] = booking_id

    return redirect(url_for('extend_booking'))


#extend booking page that takes info from the page in between profile and extend
@app.route('/extend_booking', methods=('GET', 'POST'))
def extend_booking():
    form = ExtendBookingForm()
    booking = models.booking.query.filter_by(id = session.get('booking_id', None)).first()
    collection_points = models.collection_point

    #when the form is submitted
    if form.validate_on_submit():
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



        #check if user has saved card details
        exists = models.card_details.query.filter_by(user_id = current_user.id).first() is not None
        if(exists):
            #has card details
            #extend the booking pointed to by the 'booking_id' in the session, and add to the cost
            booking.duration = booking.duration + hours
            booking.cost = booking.cost + cost
            booking.final_date_time = booking.final_date_time + timedelta(hours = hours)

            #add a new transaction, with the date for the transaction set as now
            new_transaction = models.transactions(hire_period = hours,
                                                booking_time = datetime.utcnow(),
                                                user_id = current_user.id)
            db.session.add(new_transaction)

            db.session.commit()

            #write the email message
            msg = Message('Booking Extension Confirmation',
                            sender='scootersleeds@gmail.com',
                            recipients=[current_user.email])

            msg.body = (f'Thank You, your booking extension has been confirmed. \nStart Date and Time: ' + str(booking.initial_date_time) +
            '\nEnd Date and Time: ' + str(booking.final_date_time) +
            '\nScooter ID: ' + str(booking.scooter_id) +
            '\nReference Number: ' + str(booking.id))
            mail.send(msg)

            flash("Booking Extension Successful!")

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


#Admin exclusive pages
@app.route('/admin_dashboard')
def admin_dashboard():
    #clean up bookings table
    organise_bookings()
    return render_template('admin_dashboard.html',
                            name=current_user.name,
                            title='Admin Dashboard')


@app.route('/review_feedback', methods=('GET', 'POST'))
def review_feedback():
    employee = (current_user.account_type == 'employee') # True if 'employee', False if 'manager'
    if employee:
        recs = models.feedback.query.filter_by(priority=0, resolved=0) # Employee meant to see low priority
    else:
        recs = models.feedback.query.filter_by(priority=1, resolved=0) # Manager meant to see high priority
    return render_template('review_feedback.html',
                            title='Review Customer Feedback', recs=recs)


@app.route('/edit_feedback/<id>', methods=('GET', 'POST'))
def edit_feedback(id):
    form = EditFeedbackForm()
    rec = models.feedback.query.filter_by(id=id).first()

    if request.method == 'POST':
        f = models.feedback.query.filter_by(id=id).first()

        if form.priority.data:
            f.priority = (f.priority + 1) % 2 # Toggles high priority (1 goes to 0, 0 goes to 1)

        if form.resolve.data:
            f.resolved = (f.resolved + 1) % 2 # Toggles resolved (1 goes to 0, 0 goes to 1)

        db.session.commit()
        return redirect(url_for('review_feedback'))

    return render_template('edit_feedback.html', rec=rec, form=form)


@app.route('/view_scooters', methods=['GET', 'POST'])
def view_scooters():
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
def add_scooter():
    form = AddScooterForm()

    if form.validate_on_submit():
        u = models.scooter(availability = form.availability.data, collection_id = form.location_id.data)
        db.session.add(u)    # add scooter to db
        db.session.commit()     # commit scooter to db
        now = str(datetime.now())
        app.logger.info("Admin has added a scooter with ID: "+ u.id + "at "+ now)
    return render_template('add_scooter.html',
                            title='Add New Scooter', form=form)


@app.route('/configure_scooter', methods=['GET', 'POST'])
def configure_scooter():
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
            db.session.commit()
            # print(models.scooter.query.all())
            now = str(datetime.now())
            app.logger.info("Scooter configured:  "+ scooter.id +" " + scooter.availability + " "+ scooter.collection_id + " at " + now)
            flash(f'Scooter Details Updated', 'success')
        return redirect(url_for('view_scooters'))
    return render_template('configure_scooter.html',
                            title='Configure A Scooter', form=form)


@app.route('/configure_costs', methods =['GET', 'POST'])
def configure_costs():
    rec = models.pricing.query.all()
    form = PricesForm()

    if form.validate_on_submit():
        #assign corresponding db value based on the SelectForm value.

        if form.duration.data == "1":
            durationToCheck = "1 hour"
        if form.duration.data == "2":
            durationToCheck = "4 hour"
        if form.duration.data == "3":
            durationToCheck = "1 day"
        if form.duration.data == "4":
            durationToCheck = "1 week"

        #find record and change price.
        dur = models.pricing.query.filter_by(duration = durationToCheck).first()

        if dur:
            dur.price = form.price.data
            now = str(datetime.now())
            app.logger.info("Scooter costs configured:  "+ dur.id +" " +  dur.price + " at " + now)

            flash("Price updated")
        else:
            app.logger.info("Scooter costs configuration failed at " + now)
            flash("Error price not updated")

        db.session.commit()     # commit scooter to db
    return render_template('configure_costs.html',
                            rec=rec, form=form)













@app.route('/sales_metrics')
def sales_metrics():
    one_hour_price, four_hour_price, one_day_price, one_week_price = 0, 0, 0, 0
    one_hour_metric, four_hour_metric, one_day_metric, one_week_metric = 0, 0, 0, 0
    date = datetime.utcnow()
    week_start = date + timedelta(-date.weekday(), weeks=-1)
    week_end = date + timedelta(-date.weekday() + 6, weeks=-1)

    # get all the transations
    data = models.transactions.query.all()

    # get the current prices from the database
    pricings = models.pricing.query.all()

    # for each transaction in if it is within the last week count it to the correct metric
    # need to multiply by the cost of each
    for transaction in data:
        if transaction.hire_period == 1 and transaction.booking_time > week_start and transaction.booking_time < week_end:
            one_hour_metric += 1
        elif transaction.hire_period == 4 and transaction.booking_time > week_start and transaction.booking_time < week_end:
            four_hour_metric += 1
        elif transaction.hire_period == 24 and transaction.booking_time > week_start and transaction.booking_time < week_end:
            one_day_metric += 1
        elif transaction.hire_period == 168 and transaction.booking_time > week_start and transaction.booking_time < week_end:
            one_week_metric += 1

    # get all the current pricings for each hire period in the pricing table
    for pricing in pricings:
        if pricing.duration == "1 Hour":
            one_hour_price = pricing.price
        if pricing.duration == "4 Hours":
            four_hour_price = pricing.price
        if pricing.duration == "1 Day":
            one_day_price = pricing.price
        if pricing.duration == "1 Week":
            one_week_price = pricing.price

    # Update the income amount
    one_hour_metric *= one_hour_price
    four_hour_metric *= four_hour_price
    one_day_metric *= one_day_price
    one_week_metric *= one_week_price

    # Graph the hire period metrics
    plt.bar([0,1,2,3], [one_hour_metric, four_hour_metric, one_day_metric, one_week_metric], tick_label=['One Hour', 'Four Hours', 'One Day', 'One Week'])
    plt.xlabel('Hire Period')
    plt.ylabel('Revenue (£)')
    plt.savefig('app/graphs/hireperiod.jpg')

    # Weekly income metrics
    monday_metrics = 0
    tuesday_metrics = 0
    wednesday_metrics = 0
    thursday_metrics = 0
    friday_metrics = 0
    saturday_metrics = 0
    sunday_metrics = 0

    # Get all the bookings
    bookings = models.booking.query.all()

    # calculate booking metric for each day
    for booking in bookings:
        if booking.status != "cancelled": # only adds booking that were not cancelled to the metrics
            # checks what day the booking was started
            if booking.initial_date_time.weekday() == 0 and transaction.booking_time > week_start and transaction.booking_time < week_end: # Monday
                monday_metrics += booking.cost
            elif booking.initial_date_time.weekday() == 1 and transaction.booking_time > week_start and transaction.booking_time < week_end: # Tuesday
                tuesday_metrics += booking.cost
            elif booking.initial_date_time.weekday() == 2 and transaction.booking_time > week_start and transaction.booking_time < week_end: # Wednesday
                wednesday_metrics += booking.cost
            elif booking.initial_date_time.weekday() == 3 and transaction.booking_time > week_start and transaction.booking_time < week_end: # Thursday
                thursday_metrics += booking.cost
            elif booking.initial_date_time.weekday() == 4 and transaction.booking_time > week_start and transaction.booking_time < week_end: # Friday
                friday_metrics += booking.cost
            elif booking.initial_date_time.weekday() == 5 and transaction.booking_time > week_start and transaction.booking_time < week_end: # Saturday
                saturday_metrics += booking.cost
            elif booking.initial_date_time.weekday() == 6 and transaction.booking_time > week_start and transaction.booking_time < week_end: # Sunday
                sunday_metrics += booking.cost

    # Graph the daily metrics
    plt.bar([0,1,2,3,4,5,6], [monday_metrics, tuesday_metrics, wednesday_metrics, thursday_metrics, friday_metrics, saturday_metrics, sunday_metrics], tick_label=['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'])
    plt.xlabel('Day of Week')
    plt.ylabel('Revenue (£)')
    plt.savefig('app/graphs/daily.jpg')

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
                            sunday_metrics = sunday_metrics)
