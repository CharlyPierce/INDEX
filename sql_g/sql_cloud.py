from google.cloud.sql.connector import Connector, IPTypes
import sqlalchemy
import re, os
from dotenv import load_dotenv
import pymysql
import bcrypt

load_dotenv(".env")
instance_connection_name = os.environ["INSTANCE_CONNECTION_NAME"]  # e.g. 'project:region:instance'
db_user = os.environ["DB_USER"]  # e.g. 'my-db-user'
db_pass = os.environ["DB_PASS"]  # e.g. 'my-db-password'
db_name = os.environ["DB_NAME"]  # e.g. 'my-database'
db_table = os.environ["DB_TABLE"]  # e.g. 'my-database'



def connect_with_connector() -> sqlalchemy.engine.base.Engine:

    ip_type = IPTypes.PRIVATE if os.environ.get("PRIVATE_IP") else IPTypes.PUBLIC
    connector = Connector(ip_type)

    def getconn() -> pymysql.connections.Connection:
        conn: pymysql.connections.Connection = connector.connect(
            instance_connection_name,
            "pymysql",
            user=db_user,
            password=db_pass,
            db=db_name,
        )
        return conn

    pool = sqlalchemy.create_engine(
        "mysql+pymysql://",
        creator=getconn,
        pool_size=5,
        max_overflow=2,
        pool_timeout=30,  # 30 seconds
        pool_recycle=1800,  # 30 minutes
    )
    return pool

sql_conn = None
def conection():
    global sql_conn
    sql_conn = sql_conn if sql_conn else connect_with_connector()
    return sql_conn


def register_sql(correo, passwd, nick):
    db =  conection()
    with db.connect() as conn:
        # Create your SQL INSERT statement with placeholders for parameters
        query = sqlalchemy.text(f"INSERT INTO {db_name}.{db_table} (nick, email, password_hash) VALUES (:nick, :email, :password)") 
        # Create a dictionary with the values for the placeholders
        params = {'nick':nick, 'email': correo, 'password': passwd}
        # Execute the query, passing in the values for the placeholders
        conn.execute(query, params)
        conn.commit()
    
def validate_email(correo,nick):
    db = conection()
    with db.connect() as conn:
        query_email = sqlalchemy.text(f"SELECT email FROM {db_name}.{db_table} WHERE email=:correo") 
        query_nick = sqlalchemy.text(f"SELECT nick FROM {db_name}.{db_table} WHERE nick=:nick") 

        result_email = conn.execute(query_email, {'correo': correo}).fetchone()
        result_nick = conn.execute(query_nick, {'nick': nick}).fetchone()

    # If the query returned a result, the email or nick exists in the database
    email_exists = result_email is not None
    nick_exists = result_nick is not None

    return email_exists, nick_exists


def validacion_login(correo,password):
    db = conection()
    with db.connect() as conn:
        # Create your SQL SELECT statement with a placeholder for the parameter
        query = sqlalchemy.text(f"SELECT nick, password_hash FROM {db_name}.{db_table} WHERE email=:correo") 
        # Execute the query, passing in the value for the placeholder
        result = conn.execute(query, {'correo': correo}).fetchone()

    # If the query returned a result, the email exists in the database
    if result is not None:
        hashed_password_str = bcrypt.checkpw(password.encode('utf-8'), result[1].encode('utf-8'))
        if(hashed_password_str):
            return True, result[0]  # return True and the nick
        else:
            return False, None
    else:
        return False, None

def change_pass(correo, hashed_password_str):
    db = conection()
    with db.connect() as conn:
        query = sqlalchemy.text(f"UPDATE {db_name}.{db_table} SET password_hash = :new_password WHERE email = :correo")
        params = {'correo': correo, 'new_password': hashed_password_str}
        result = conn.execute(query, params )
        
