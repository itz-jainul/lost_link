from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, SelectField, DateField
from wtforms.validators import DataRequired, Email, Length, Optional

class RegisterForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(max=120)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    phone = StringField('Phone (optional)', validators=[Optional(), Length(max=30)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    submit = SubmitField('Register')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class ResetRequestForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Request Password Reset')

class ResetPasswordForm(FlaskForm):
    password = PasswordField('New Password', validators=[DataRequired(), Length(min=6)])
    submit = SubmitField('Reset Password')

class ItemForm(FlaskForm):
    title = StringField('Item title', validators=[DataRequired(), Length(max=200)])
    category = SelectField('Category', choices=[('Electronics','Electronics'), ('ID','ID Card'), ('Books','Books'), ('Clothing','Clothing'), ('Other','Other')])
    location = StringField('Location', validators=[DataRequired(), Length(max=200)])
    date_lost_found = DateField('Date (YYYY-MM-DD)', validators=[Optional()], format='%Y-%m-%d')
    description = TextAreaField('Description', validators=[Optional(), Length(max=1000)])
    contact_details = StringField('Contact details (phone/email)', validators=[Optional(), Length(max=300)])
    submit = SubmitField('Submit')

class ClaimForm(FlaskForm):
    message = TextAreaField('Message', validators=[DataRequired(), Length(max=1000)])
    proof = TextAreaField('Proof (serial number or description)', validators=[Optional(), Length(max=1000)])
    submit = SubmitField('Request Claim')

class ChatMessageForm(FlaskForm):
    body = StringField('Message', validators=[DataRequired(), Length(max=1000)])
    submit = SubmitField('Send')
