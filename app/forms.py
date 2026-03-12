from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, BooleanField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional, ValidationError
from .models import User


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Login')


class SignupForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

    def validate_username(self, username):
        if User.query.filter_by(username=username.data).first():
            raise ValidationError('Username already taken.')

    def validate_email(self, email):
        if User.query.filter_by(email=email.data).first():
            raise ValidationError('Email already registered.')


class PinForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=140)])
    description = TextAreaField('Description')
    tags = StringField('Tags (comma separated)')
    source_url = StringField('Source URL (optional)', validators=[Optional(), Length(max=500)])
    image = FileField('Pin Image', validators=[DataRequired(), FileAllowed(['jpg', 'png', 'jpeg', 'gif', 'webp'], 'Images only!')])
    submit = SubmitField('Upload Pin')


class PinEditForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=140)])
    description = TextAreaField('Description')
    tags = StringField('Tags (comma separated)')
    source_url = StringField('Source URL (optional)', validators=[Optional(), Length(max=500)])
    submit = SubmitField('Save Changes')


class CommentForm(FlaskForm):
    text = TextAreaField('Comment', validators=[DataRequired(), Length(max=500)])
    submit = SubmitField('Post')


class BoardForm(FlaskForm):
    name = StringField('Board Name', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description', validators=[Optional(), Length(max=500)])
    is_private = BooleanField('Private Board')
    submit = SubmitField('Create Board')


class EditProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=64)])
    bio = TextAreaField('About Me', validators=[Length(max=500)])
    website = StringField('Website', validators=[Optional(), Length(max=255)])
    avatar = FileField('Update Avatar', validators=[FileAllowed(['jpg', 'png', 'jpeg', 'webp'])])
    submit = SubmitField('Update Profile')


class SettingsForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    current_password = PasswordField('Current Password')
    new_password = PasswordField('New Password', validators=[Optional(), Length(min=6)])
    confirm_password = PasswordField('Confirm New Password', validators=[EqualTo('new_password', message='Passwords must match')])
    submit = SubmitField('Save Changes')
