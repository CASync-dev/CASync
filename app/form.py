from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, URLField, DateField, TimeField, EmailField
from wtforms.validators import EqualTo, InputRequired, Regexp, Length, ValidationError
import re
from app.models import User

# Custom validator to check for a strong password
def strong_password(form, field):
    password = field.data
    errors = []

    if len(password) < 8:
        errors.append("at least 8 characters")
    if not re.search(r'[A-Z]', password):
        errors.append("one uppercase letter")
    if not re.search(r'[a-z]', password):
        errors.append("one lowercase letter")
    if not re.search(r'\d', password):
        errors.append("one number")
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        errors.append("one special character")

    if errors:
        raise ValidationError(f"Password must contain: {', '.join(errors)}.")



class LoginForm(FlaskForm):
    username = StringField(validators=[InputRequired()])
    password = StringField(validators=[InputRequired()])
    submit = SubmitField('Login')

class RegisterForm(FlaskForm):
    email = EmailField(validators=[InputRequired(message="All fields are required.")])
    username = StringField(validators=[InputRequired(message="All fields are required."), Regexp('^[A-Za-z0-9_]+$', message="Username must contain only letters, numbers, and underscores.")])
    password = StringField(validators=[InputRequired(message="All fields are required."),strong_password])
    repeat_password = StringField(validators=[InputRequired(message="All fields are required."), EqualTo('password', message='Passwords must match')])
    submit = SubmitField('Register')

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('Username already taken.')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('Email already registered.')
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

# I've only done this for changing passwords since other changing fields shouldn't need validation (ie. current pass) ?
class changePassword(FlaskForm):
    current_password = StringField(validators=[InputRequired()])
    new_password = StringField(validators=[InputRequired(message="All fields are required."),strong_password])
