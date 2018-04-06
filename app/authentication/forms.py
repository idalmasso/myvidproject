from app.usermodel import User
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, ValidationError,EqualTo


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember me')
    submit = SubmitField('Log in')


class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField('Repeat password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Request registration')

    def validate_username(self, username):
        u = User.find_user(username.data)
        if u is not None:
            raise ValidationError('Username already exists!')
        u = User.find_user_request(username.data)
        if u is not None:
            raise ValidationError('Username already requested registration!')


class AcceptRequestForm(FlaskForm):
    username = StringField('username')
    submit = SubmitField('Accept')
