from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField
from wtforms.validators import DataRequired,Email,Length,EqualTo
from flask_wtf.file import FileField,FileAllowed,FileRequired

class ContactForm(FlaskForm):
    screenshot = FileField('upload screenshot', validators=[FileRequired(),FileAllowed(['pnj','jpeg','jpg'],'Ensure you upload the right extension')])

    email = StringField("Your Email: ", validators=[Email(message='Your email should be valid'),DataRequired(message='We will need to have your email address inorder to get back to you')])

    confirm_email = StringField('Confirm Email', validators=[EqualTo('email')])
    message = TextAreaField("Message: ", validators=[DataRequired(),Length(min=10,message='The text message is too small')])
    submit = SubmitField("Send Message")