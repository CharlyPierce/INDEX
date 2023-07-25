from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, HiddenField, ValidationError, IntegerField
from wtforms.validators import DataRequired, Email
from flask_login import UserMixin
import re

class User(UserMixin):
    def __init__(self, id):
        self.id = id

class LoginForm(FlaskForm):
    message='Debe ser una dirección de correo electrónico válida'
    username = StringField('Username', validators=[DataRequired(),Email(message)])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')
    

class AddForm(FlaskForm):
    subtema = StringField('Subtema')
    padre = HiddenField('Padre')
    tema = HiddenField('Tema')
    submit = SubmitField('Submit')
    eliminar = SubmitField('Eliminar')

class PasswordCheck:
    def __init__(self, message=None):
        if not message:
            message = 'La contraseña debe tener al menos 8 caracteres, una mayúscula, una minúscula y un carácter especial.'
        self.message = message

    def __call__(self, form, field):
        password = field.data
        if len(password) < 8 or not re.search(r'[A-Z]', password) or not re.search(r'[a-z]', password) or not re.search(r'\W', password):
            raise ValidationError(self.message)

class RegisterForm(FlaskForm):
    message='Debe ser una dirección de correo electrónico válida'
    correo = StringField('correo', validators=[DataRequired(), Email(message)])
    nickname = StringField('Nick', validators=[DataRequired()])
    passwd = PasswordField('contraseña', validators=[DataRequired(), PasswordCheck()])
    passwd2 = PasswordField('confirmar contraseña', validators=[DataRequired()])
    submit = SubmitField('Submit')

class VerifyForm(FlaskForm):
    code = StringField('Código de Verificación', validators=[DataRequired()])
    submit = SubmitField('Verificar')

class RecoveryForm(FlaskForm):
    message='Debe ser una dirección de correo electrónico válida'
    correo = StringField('correo', validators=[DataRequired(), Email(message)])
    submit = SubmitField('Submit')

class passsForm(FlaskForm):
    passwd = PasswordField('contraseña', validators=[DataRequired(), PasswordCheck()])
    passwd2 = PasswordField('confirmar contraseña', validators=[DataRequired()])
    submit = SubmitField('Submit')