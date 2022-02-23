from flask import render_template, flash
from app import app, db, bcrypt, models
from .forms import LoginForm, SignUpForm
from flask import request, redirect, url_for, abort, make_response
from flask_login import login_user, current_user, logout_user, login_required
import os

@app.route('/')
def index():
    return render_template('home.html',
                            title='Home')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:   # if current user is logged in
        return redirect(url_for('index'))

    form = SignUpForm()

    # if form is submitted

    if form.validate_on_submit():
        
        #encrypt password
        hashed_password= bcrypt.generate_password_hash(form.password1.data)

        u = models.user(password = hashed_password, email = form.email.data , status="normal" , name = form.name.data)

        db.session.add(u)    # add user to db
        db.session.commit()     # commit user to db
        flash(f'Account Created! Please Log In', 'success')

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

    # if form is submitted
    if form.validate_on_submit():

        ##flash('Succesfully received form data. %s %s %s'%(form.username.data, form.password.data, form.remember.data))

        # get first instance of user in db
        u = models.user.query.filter_by(email = form.email.data).first()

        # check username and password
        if u and bcrypt.check_password_hash(u.password, form.password.data):
            login_user(u)
            flash('Login Successful!', 'success')
            return redirect(url_for('user_login'))
        else:
            flash(f'Login unsuccessful. Please check email and password', 'error')


    return render_template('user_login.html',
                           title='User Login',
                           form=form)


# only logout if user is logged in
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logout Successful!', 'info')
    # redirect to home page
    return redirect(url_for('index'))


#Guest exclusive pages
@app.route('/info')
def info():
    return render_template('info.html',
                            title='How it Works')


#User exclusive pages
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
                            status=current_user.status)


@app.route('/send_feedback')
def send_feedback():
    return render_template('send_feedback.html',
                            title='Send Us Your Feedback')


#Admin exclusive pages
@app.route('/review_feedback')
def review_feedback():
    return render_template('review_feedback.html',
                            title='Review Customer Feedback')


@app.route('/configure_scooters')
def configure_scooters():
    return render_template('configure_scooters.html',
                            title='Configure Scooters')


@app.route('/sales_metrics')
def sales_metrics():
    return render_template('sales_metrics.html',
                            title='View Sales Metrics')


#Guest + user shared pages
@app.route('/locations')
def locations():
    return render_template('locations.html',
                            title='Pickup Locations')


@app.route('/locations_LRIH')
def locations_LRIH():
    return render_template('locations_LRIH.html',
                            title='Location: LRI Hostpital')


@app.route('/locations_LTS')
def locations_LTS():
    return render_template('locations_LTS.html',
                            title='Location: Leeds Train Station')


@app.route('/locations_MC')
def locations_MC():
    return render_template('locations_MC.html',
                            title='Location: Merrion Centre')


@app.route('/locations_TC')
def locations_TC():
    return render_template('locations_TC.html',
                            title='Location: Trinity Centre')


@app.route('/locations_UoLESC')
def locations_UoLESC():
    return render_template('locations_UoLESC.html',
                            title='Location: UoL Edge Sports Centre')


#Admin + User shared pages
@app.route('/booking')
def booking():
    return render_template('booking.html',
                            title='Make a Booking')
