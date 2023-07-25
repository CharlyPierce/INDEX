from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required
from flask import Flask, render_template, redirect, url_for, request, session, abort, flash, jsonify
from wtforms import StringField, PasswordField, SubmitField
from flask_login import current_user
from flask_wtf import FlaskForm
from forms.forms import LoginForm, User, AddForm, RegisterForm, VerifyForm, RecoveryForm, passsForm
from itsdangerous import URLSafeTimedSerializer
from sql_g.sql_cloud import register_sql, validate_email, validacion_login, change_pass
import pandas as pd
import validators
import logging
import nodos
import csv
import re
import bcrypt
import random
import smtplib
from unidecode import unidecode
from email.mime.text import MIMEText
from dotenv import load_dotenv
import os
from datetime import datetime,timedelta
from datetime import datetime
import pytz
import time


load_dotenv()  # busca automáticamente un archivo llamado .env
#Se ejecuta en el import
correo_ = os.getenv('correo')
passw_ = os.getenv('passw')

instance_connection_name = os.environ["INSTANCE_CONNECTION_NAME"]  # e.g. 'project:region:instance'
db_user = os.environ["DB_USER"]  # e.g. 'my-db-user'
db_pass = os.environ["DB_PASS"]  # e.g. 'my-db-password'
db_name = os.environ["DB_NAME"]  # e.g. 'my-database'



def clean_key(key, clave):
    # Remueve la clave y los dígitos al inicio del nombre
    return re.sub('^' + clave + '\d+', '', key)
def is_url(string):
    pattern = r"(.*?)(https?:\/\/[^\s]+)(.*)"
    match = re.search(pattern, string)
    if match:
        return [match.group(1), match.group(2), match.group(3)]
    else:
        return [string, "", ""]
def process_calificacion(calificacion_usuario):
    calificacion_usuario = str(calificacion_usuario)
    calificacion = int(calificacion_usuario[0])
    promedio = calificacion_usuario[1:2]
    usuario = calificacion_usuario[2:]
    return calificacion, promedio, usuario

#esa variable app es tu aplicación Flask
app = Flask(__name__)
app.debug = False



app.jinja_env.filters['clean_key'] = clean_key
app.jinja_env.globals.update(is_url=is_url)
app.jinja_env.globals.update(process_calificacion=process_calificacion)
app.secret_key = ''  # Necesario para mantener las sesiones seguras

#----------------------------------------logs del servidor-----------------------------------------------#
logging.basicConfig(filename='logs/myapp.log', level=logging.INFO)
# app.logger.debug('Esto es un mensaje de depuración') #Escribir en logs
app.logger.info('Esto es un mensaje informativo')
# app.logger.warning('Esto es un mensaje de advertencia')
# app.logger.error('Esto es un mensaje de error')
#---------------------------------------------------------------------------------------------------------#
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = '/'  # Esto redirige a los usuarios no autenticados a la página de inicio de sesión

# Esta es una representación muy básica de un modelo de usuario
# users = {'usuario1': {'password': 'clave1'},'invitado': {'password': 'invitado'}}


data = {"TRONCO COMÚN":"LFM_TRONCO" , "MATEMÁTICAS":"LFM_MAT" , "FÍSICA":"LFM_FISICA" , 
        "MATEMÁTICAS EDUCATIVAS":"LFM_EDUCATIVA" , "INGENIERÍA NUCLEAR":"LFM_NUCLEAR" }

def read_materias(carrera,semestre):
        #valor_si_verdadero if condicion else valor_si_falso=OTRA_CONDICION
    carpeta = "LIM" if carrera == "LIM" else "LMA" if carrera == "LMA" else "LFM"   
    data_csv = f"CSV/{carpeta}/{data.get(carrera, carrera)}.csv"

    with open(data_csv, 'r') as file:
        reader = csv.DictReader(file)
        rows = list(reader) #Lista de diccionarios
    materias_ = [row for row in rows if int(row['Semestre']) == int(semestre)]
    materias = [row['Asignatura'] for row in materias_]
    id = [row['Clave'] for row in materias_]
    return materias , id


def generate_verification_code():
    correo = session.get('correo')  # Aquí obtenemos el correo electrónico de la sesión.
    verification_code = random.randint(100000, 999999)
    session['verification_code'] = verification_code
    utc_now = datetime.now(pytz.utc)
    session["code_generation_time"] = utc_now.isoformat()

    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(correo_, passw_)

    msg_content = f"CODE:\n{verification_code}"
    msg = MIMEText(msg_content)
    msg['Subject'] = 'Código de Verificación'
    msg['To'] = correo
    # print(verification_code)
    server.sendmail(correo_, correo, msg.as_string())
    server.quit()


#-----------------------------SIGIN-------------------------------------------------------------------

@app.route("/register", methods=["GET", "POST"])
def register():
    try:
        form = RegisterForm()
        user_exists = False
        nickname_exists = False
        if form.validate_on_submit():
            # Generate the salt
            salt = bcrypt.gensalt()
            # Guarda el código en la sesión del usuario 
            if(form.passwd.data==form.passwd2.data):
                try:
                    user, nick = validate_email(form.correo.data,form.nickname.data)
                    if(not user and not nick):
                        session['nick'] = form.nickname.data
                        session['correo'] = form.correo.data
                        hashed_password_str = bcrypt.hashpw(form.passwd.data.encode('utf-8'), salt)
                        session['passwd'] = hashed_password_str.decode('utf-8')
                        a = generate_verification_code()
                        form.passwd2.errors = []
                        # Envía el código al correo electrónico del usuario
                        # Redirige al usuario a la página de verificación
                        return redirect(url_for('verify'))
                    else:
                        user_exists = user
                        nickname_exists = nick
                except Exception as e:
                    app.logger.info(e)
                    abort(403)
            else:
                form.passwd2.errors.append('Las contraseñas no coinciden')

        return render_template("register/register.html", form=form,user_exists=user_exists,nickname_exists=nickname_exists)
    except Exception as e:
        app.logger.error(e)
        abort(403)
#-----------------------------validation-------------------------------------------------
@app.route('/verify', methods=['GET', 'POST'])
def verify():
    try:
        if 'verification_code' not in session:
            flash('No hay un código de verificación pendiente.')
            return redirect(url_for('register'))  # Asume que 'login' es la ruta de inicio de sesión
        very_form = VerifyForm()
        if very_form.validate_on_submit():
            # Comprueba si han pasado más de 5 minutos desde que se generó el código
            code_generation_time = datetime.fromisoformat(session['code_generation_time'])
            if datetime.now(pytz.utc) - code_generation_time > timedelta(seconds=120):
                if 'code_generation_time' in session:
                    code_generation_time = datetime.fromisoformat(session['code_generation_time'])
                else:
                    # Si 'code_generation_time' no está en la sesión, puedes mostrar un mensaje al usuario o redirigir a otra página
                    flash('El código de verificación ha caducado.')
                    del session['code_generation_time']
            # Verifica que el código introducido por el usuario sea una cadena de dígitos
            elif str(very_form.code.data).isdigit():
                # Si es así, compara el código que el usuario introdujo con el código de la sesión
                if int(very_form.code.data) == int(session['verification_code']):
                    # Si coinciden, el correo electrónico ha sido validado
                    # Aquí puedes crear el usuario y guardar sus datos en la base de datos
                    register_sql(session['correo'], session['passwd'], session['nick']) 
                    del session['verification_code']
                    del session['code_generation_time']
                    del session['passwd']
                    del session['correo']
                    return redirect(url_for('home'))
                else:
                    # Si no coinciden, muestra un mensaje de error
                    flash('El código de verificación es incorrecto')
            else:
                # Si el código introducido por el usuario no es una cadena de dígitos, muestra un mensaje de error
                flash('El código de verificación no es numerico')

        return render_template('verify/verify.html', form=very_form,session=session)
    except Exception as e:
        app.logger.error(e)
        abort(403)
#-----------------------------resend-------------------------------------------------
@app.route('/resend_code', methods=['GET'])
def resend_code():
    try:
        generate_verification_code()  # Re-generamos y re-enviamos el código.
        return redirect(url_for('verify'))  # Redirigimos al usuario de nuevo a la página de verificación.
    except Exception as e:
        app.logger.error(e)
        abort(403)
#-----------------------------LOGIN NECESARY-------------------------------------------------------------------
@login_manager.user_loader
def load_user(user_id):
    user_exists = True
    # user_exists = llamada a base de datos para verificar usuario
    return User(user_id) if user_exists else None
#----------------------------------LOGIN--------------------------------------------------------------------#
@app.route('/login', methods=['GET', 'POST'])
@app.route('/', methods=['GET', 'POST'])
def home():
    try:
        form = LoginForm()
        if form.validate_on_submit():  # Esto también verifica el token CSRF
            app.logger.error("error0")
            username = form.username.data
            password = form.password.data
            app.logger.error("erro1")
            user , username = validacion_login(username,password)
            app.logger.error("error2")
            if user:
                user = User(username)
                login_user(user)
                return redirect(url_for('start'))
            else:
                flash("Datos Invalidos")
        return render_template('login/login.html', form=form)  # Pasa el formulario a la plantilla
    except Exception as e:
        print(e)
        app.logger.error(e)
        abort(403)
#----------------------------------recovery--------------------------------------------------------------------#


def get_token(email, expiration=600):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    return serializer.dumps(email)

def confirm_token(token, expiration=600):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    try:
        email = serializer.loads(
            token,
            max_age=expiration
        )
    except:
        return False
    return email


def recover(mail):
    token = get_token(mail)

    # Generate URL
    recover_url = url_for('reset_with_token', token=token, _external=True)

    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(correo_, passw_)

    msg_content = f"Haga click en el siguiente enlace para restablecer su contraseña: {recover_url}"
    msg = MIMEText(msg_content)
    msg['Subject'] = 'Recovery'
    msg['To'] = mail
    # print(msg_content)
    server.sendmail(correo_, mail, msg.as_string())
    server.quit()

@app.route('/recovery', methods=['GET','POST'])
def recovery():
    try:
        form = RecoveryForm()
        if form.validate_on_submit():  # Esto también verifica el token CSRF
            recover(form.correo.data)
            session['reset_email'] = form.correo.data
            return redirect(url_for('start'))
        else:
            flash('Hay un problema con el formulario. Por favor, inténtalo de nuevo.') # Esto mostrará un mensaje de error si el formulario no se valida
        return render_template('recovery/recovery.html', form=form)  # Pasa el formulario a la plantilla
    except Exception as e:
        print(e)
        app.logger.error(e)
        flash('Ha ocurrido un error. Por favor, inténtalo de nuevo más tarde.') # Esto mostrará un mensaje de error si ocurre una excepción
        return redirect(url_for('start')) # Esto redirigirá a 'start' si ocurre una excepción


@app.route('/reset/<token>', methods=['GET', 'POST'])
def reset_with_token(token):
    try:
        email = confirm_token(token)
        if email:  # Si el token es válido y se puede obtener un correo electrónico
            form = passsForm()
            if form.validate_on_submit():
                if(form.passwd.data == form.passwd2.data ):
                    salt = bcrypt.gensalt()
                    mail = session.get('reset_email')
                    hashed_password_str = bcrypt.hashpw(form.passwd.data.encode('utf-8'), salt)
                    hashed_password_str = hashed_password_str.decode('utf-8')
                    change_pass(mail,hashed_password_str)
                    # Aquí va el código para cambiar la contraseña y procesarla
                    flash('Contraseña cambiada exitosamente', 'success')
                    return redirect(url_for('login'))
                else:
                    flash("Las Contraseñas deben coincidir")
            return render_template('recovery/reset.html', form=form)
        else:  
            # Si no se pudo obtener un correo electrónico del token, asumimos que el token no es válido.
            flash('El enlace de restablecimiento de contraseña es inválido o ha expirado.', 'error')
            return redirect(url_for('start'))
    except Exception as e:
        print(e)
        flash('Ha ocurrido un error. Por favor, inténtalo de nuevo más tarde.', 'error')
        return redirect(url_for('start'))


#----------------------------------LICENCIATURAS--------------------------------------------------------------------#
@app.route('/start')
@login_required
def start():            #Aqui estas dentro de templates como raiz # minusculas name carptas
    try:
        return render_template('html_p1/index.html')
    except Exception as e:
        app.logger.error(e)
        abort(403)
#----------------------------------SEMESTRES--------------------------------------------------------------------#
@app.route('/<carrera>')
@login_required
def mostrar_pagina(carrera):
    try:
        if(carrera=="LIM"):
            c = "LIM"#Ingeniería Matemática
        elif(carrera=="LFM"):
            c = "LFM"#Licenciatura en Física y Matemáticas
        else:
            c = "LMA"#Licenciatura en Matemática Algorítmica
        return render_template('html_p2/semestre.html',carrera=c)
    except Exception as e:
        app.logger.error(e)
        abort(403)
#----------------------------------MATERIAS--------------------------------------------------------------------#
@app.route('/<carrera>/<semestre>') #param is id[n]
@login_required
def pagina(carrera,semestre): 
    try:
        semestre_v = any([re.match(r'^OXX\d{4}$', semestre),re.match(r'^OXX\d{4}$', semestre), re.match(r'^\d{1,5}$', semestre), re.match(r'sns', semestre)])
        carrera_v = carrera in ["MATEMÁTICAS EDUCATIVAS", "MATEMÁTICAS", "FÍSICA", "INGENIERÍA NUCLEAR","otro","LFM","LIM","LMA"]


        if carrera_v and semestre_v:
            if(carrera=="otro"):  #muestra materias de otro
                df = pd.read_csv("CSV/OTRO/OTRO.csv")
                materias, id = map(list, df[['Asignatura', 'Clave']].values.T)
                return render_template('html_p3/other.html', materia=list(zip(materias,id)))
            elif(carrera=="LFM"):
                if(int(semestre) <= 3):
                    materias, id = read_materias("TRONCO COMÚN",semestre)
                    return render_template('html_p3/materias.html',carrera=carrera,semestre=semestre, materia=list(zip(materias,id)) )
                else:
                    materias = ["MATEMÁTICAS", "FÍSICA", "MATEMÁTICAS EDUCATIVAS", "INGENIERÍA NUCLEAR"]
                    return render_template('html_p2/LFM_ESPECIALIDAD.html', materia=materias,semestre=semestre,c=carrera)
            elif(carrera=="LIM" or carrera=="LMA"):
                materias, id = read_materias(carrera,semestre)
                return render_template('html_p3/materias.html',carrera=carrera,semestre=semestre, materia=list(zip(materias,id)) )
            else:
                materias, id = read_materias(carrera,semestre)
                return render_template('html_p3/materias.html',carrera=carrera,semestre=semestre, materia=list(zip(materias,id)) )
        else:
            abort(403)
    except Exception as e:
        app.logger.error(e)
        abort(403)
#----------------------------------FUNCTION TO RENDERICE ALL--------------------------------------------------------------------#
def link_call(clave):
    # Abre el archivo CSV
    with open('CSV/global_with_links.csv', 'r') as file:
        reader = csv.DictReader(file)
        # Busca la fila con la clave dada
        for row in reader:
            if row['Clave'] == clave:
                # Devuelve el link de esa fila
                return row['Link']
    # Si no se encuentra la clave, devuelve 'None'
    return None

def node_call(clave):
    try:
        form = AddForm()
        user = current_user.id
        n = nodos.tree(clave,user)
        first_item = list(n.items())[0]
        link=link_call(clave)
        return render_template('html_p4/index.html', tree=n, PADRE=first_item[0], CLAVE = clave, form = form,url=link)
    except Exception as e:
        app.logger.error(e)
        abort(403)
#----------------------------------TEMARIO--------------------------------------------------------------------#
@app.route('/page4/<clave>')
@login_required
def temario(clave):
    try:
        if(re.match(r'^OccX\d{4}$', clave) or re.match(r'^AL\d{3,4}$', clave) or re.match(r'^M\d{3}$', clave) or re.match(r'^LFM\d{3}$', clave)  ):
            return node_call(clave)
        else:
            abort(403)
    except Exception as e:
        app.logger.error(e)
        abort(403)
#----------------------------------ADD TEMAS--------------------------------------------------------------------#
@app.route('/page5/<clave>', methods=['POST'])
@login_required
def add_temario(clave):
    try:
        if(re.match(r'^OccX\d{4}$', clave) or re.match(r'^AL\d{3,4}$', clave) or re.match(r'^M\d{3}$', clave) or re.match(r'^LFM\d{3}$', clave)  ):
            form = AddForm(request.form)
            if form.validate_on_submit():
                _tema = form.tema.data
                _subtema = form.subtema.data
                user = current_user.id
                # AGREGAR NODO
                if _subtema: nodos.agregar(clave,_tema,_subtema,user)
                return redirect(url_for('temario', clave=clave))
            else:
                abort(403)
        else:
            abort(403)
    except Exception as e:
        app.logger.error(e)
        abort(403)
#----------------------------------Delete TEMAS--------------------------------------------------------------------#
@app.route('/page6/<clave>', methods=['POST'])
@login_required
def delete_temario(clave):
    try:
        if(re.match(r'^OccX\d{4}$', clave) or re.match(r'^AL\d{3,4}$', clave) or re.match(r'^M\d{3}$', clave) or re.match(r'^LFM\d{3}$', clave)  ):
            form = AddForm(request.form)
            if form.validate_on_submit():
                _padre = form.padre.data
                _tema = form.tema.data
                user = current_user.id
                if user=="eyes": nodos.delete(clave,_padre,_tema,user)
                return redirect(url_for('temario', clave=clave))
            else:
                abort(403)
        else:
            abort(403)
    except Exception as e:
        app.logger.error(e)
        abort(403)
#-------------------------------ADD METRICS-----------------------------------------------------------
@app.route('/page7/<clave>', methods=['GET', 'POST'])
@login_required
def metric(clave):
    try:
        if(re.match(r'^OccX\d{4}$', clave) or re.match(r'^AL\d{3,4}$', clave) or re.match(r'^M\d{3}$', clave) or re.match(r'^LFM\d{3}$', clave)  ):
            if request.method == 'POST':
                data = request.get_json()  # obtener datos como JSON
                _tema = data.get('tema')
                _calificacion = data.get('calificacion')
                _usuario = current_user.id
                # Aquí puedes hacer lo que necesites con los datos
                nodos.calificacion(clave=clave,tema=_tema, usuario=_usuario, calificacion=_calificacion)
            return node_call(clave)
        else:
            abort(403)
    except Exception as e:
        app.logger.error(e)
        abort(403)
#----------------------------------LOGOUT--------------------------------------------------------------------
@app.route('/logout')
@login_required
def logout():
    try:
        logout_user()
        return redirect(url_for('logout'))  # Redirecciona al usuario a la página de inicio de sesión después de cerrar sesión
    except Exception as e:
        app.logger.error(e)
        abort(403)

if __name__ == "__main__":
    print("En Servidor Flask")
    app.run(host='0.0.0.0', debug=True, port=5000)
    app.logger.info('En Servidor Flask ')
