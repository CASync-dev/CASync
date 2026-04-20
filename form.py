from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, URLField
from wtforms.validators import InputRequired

class IcalImportForm(FlaskForm):
    ical_url = URLField('iCal URL', validators=[InputRequired()])
    user_id = StringField('User ID', validators=[InputRequired()])
    submit = SubmitField('Import')
