from app import app

@app.route('/')
def index():
    return "Hello World!"
=======
from flask import render_template, flash
from app import app
from .forms import TestForm

@app.route('/')
def index():
        return render_template('home.html',
                               title='Home')

@app.route('/testform', methods=['GET', 'POST'])
def testform():
    form = TestForm()
    if form.validate_on_submit():
        flash('Succesfully received form data. %s'%(form.string1.data))
    return render_template('testform.html',
                           title='Test Form',
                           form=form)
