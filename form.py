from flask wtf import FlaskForm
from wtforms import IntegerField, BooleanField, SubmitField
from wtforms.validators import DataRequired

class IcalImportForm(FlaskForm):
    ical_url = URLField('iCal URL', validators=[DataRequired()])
    submit = SubmitField('Import')