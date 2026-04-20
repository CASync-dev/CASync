from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, URLField, DateField, IntegerField, TimeField, SelectField
from wtforms.validators import InputRequired

class IcalImportForm(FlaskForm):
    ical_url = URLField('iCal URL', validators=[InputRequired()])
    user_id = IntegerField('User ID', validators=[InputRequired()])
    submit = SubmitField('Import')

class EventForm(FlaskForm):
    title = StringField(validators=[InputRequired()])
    date = DateField(validators=[InputRequired()])
    start_time = TimeField(validators=[InputRequired()])
    end_time = TimeField(validators=[InputRequired()])
    location = StringField()
    description = StringField()
    color = StringField()

# TODO: Login Form, Registtration form.