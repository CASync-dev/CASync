from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, EmailField, URLField, TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo, Length, URL, Optional

# # What login form may look like
# class LoginForm(FlaskForm):
#     username = StringField('Username', validators=[DataRequired()])
#     password = PasswordField('Password', validators=[DataRequired()])
#     remember_me = BooleanField('Remember Me')
#     submit = SubmitField('Log In')

# # What registration form may look like
# class RegisterForm(FlaskForm):
#     email = EmailField('Email', validators=[DataRequired(), Email()])
#     username = StringField('Username', validators=[
#         DataRequired(),
#         Length(min=3, max=64)
#     ])
#     password = PasswordField('Password', validators=[
#         DataRequired(),
#         Length(min=8)
#     ])
#     password2 = PasswordField('Re-enter Password', validators=[
#         DataRequired(),
#         EqualTo('password', message='Passwords must match.')
#     ])
#     submit = SubmitField('Register')

class ICalImportForm(FlaskForm):
    ical_url = URLField('iCal URL', validators=[DataRequired(), URL()])

class EventForm(FlaskForm):
    # Fields match the inputs already in schedule.html.
    # These are not rendered by WTForms — they are only used to generate
    # the CSRF hidden field via form.hidden_tag().
    title    = StringField('Title',       validators=[DataRequired()])
    date     = StringField('Date',        validators=[DataRequired()])
    start_time = StringField('Start',     validators=[DataRequired()])
    end_time   = StringField('End',       validators=[DataRequired()])
    location   = StringField('Location',  validators=[Optional()])
    description = TextAreaField('Description', validators=[Optional()])
    color      = StringField('Color',     validators=[Optional()])