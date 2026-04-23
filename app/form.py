from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, URLField, DateField, TimeField
from wtforms.validators import InputRequired

class LoginForm(FlaskForm):
    username = StringField(validators=[InputRequired()])
    password = StringField(validators=[InputRequired()])
    submit = SubmitField('Login')

class IcalImportForm(FlaskForm):
    ical_url = URLField('iCal URL', validators=[InputRequired()])
    submit = SubmitField('Import')

class EventForm(FlaskForm):
    title = StringField(validators=[InputRequired()])
    date = DateField(validators=[InputRequired()])
    start_time = TimeField(validators=[InputRequired()])
    end_time = TimeField(validators=[InputRequired()])
    location = StringField()
    description = StringField()
    color = StringField()

