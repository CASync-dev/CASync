from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, URLField, DateField, TimeField, EmailField
from wtforms.validators import EqualTo, InputRequired

class LoginForm(FlaskForm):
    username = StringField(validators=[InputRequired()])
    password = StringField(validators=[InputRequired()])
    submit = SubmitField('Login')

class RegisterForm(FlaskForm):
    email = EmailField(validators=[InputRequired(message="All fields are required.")])
    username = StringField(validators=[InputRequired(message="All fields are required.")])
    password = StringField(validators=[InputRequired(message="All fields are required.")])
    repeat_password = StringField(validators=[InputRequired(message="All fields are required."), EqualTo('password', message='Passwords must match')])
    submit = SubmitField('Register')

    # Override the validate method to ensure that duplicate error messages are not added to the form
    def validate(self, extra_validators=None):
        result = super().validate(extra_validators)
        seen = set()
        for field in self:
            unique = []
            for error in field.errors:
                if error not in seen:
                    seen.add(error)
                    unique.append(error)
            field.errors[:] = unique
        return result

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

