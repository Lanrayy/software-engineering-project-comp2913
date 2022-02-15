from flask_wtf import Form
from wtforms import TextField
from wtforms.validators import DataRequired

class TestForm(Form):
    string1 = TextField('string1', validators=[DataRequired()])
