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

        flash('Succesfully received form data. %s %s %s %s'%(form.name.data, form.email.data, form.password1.data, form.password2.data))

        # set user = current user

        #encrypt password
        hashed_password= bcrypt.generate_password_hash(form.password1.data)


        u = models.user(password = hashed_password, email = form.email.data , status="normal" , name = form.name.data)

        db.session.add(u)    # add user to db
        db.session.commit()     # commit user to db
        flash('Account Created! Please Log In', 'success')

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
        if u:
            if bcrypt.check_password_hash(u.password, form.password.data):
                login_user(u)
                flash('Login Successful!', 'success')
                return redirect(url_for('user_login'))
            else:
                flash('Wrong Password!')
        else:
            flash('Login unsuccessful. Please check email and password', 'danger')


    return render_template('user_login.html',
                           title='User Login',
                           form=form)


# only logout if user is logged in
@app.route ('/logout')
@login_required
def logout():
    logout_user()
    flash('Logout Successful!', 'info')
    # redirect to home page
    return redirect(url_for('index'))
