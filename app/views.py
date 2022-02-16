from flask import render_template, flash
from app import app
from .forms import LoginForm, SignUpForm

@app.route('/')
def index():
        return render_template('home.html',
                               title='Home')

@app.route('/user_login', methods=['GET', 'POST'])
def userLoginForm():
    form = LoginForm()
    if form.validate_on_submit():
        flash('Succesfully received form data. %s %s %s'%(form.username.data, form.password.data, form.remember.data))
    return render_template('user_login.html',
                           title='User Login',
                           form=form)

@app.route('/register', methods=['GET', 'POST'])
def registerForm():
    form = SignUpForm()
    if form.validate_on_submit():
        flash('Succesfully received form data. %s %s %s %s %s'%(form.name.data, form.username.data, form.email.data, form.password1.data, form.password2.data))
    return render_template('register.html',
                           title='Sign Up',
                           form=form)
