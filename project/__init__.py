from flask import Flask,g,render_template
import os
import mysql.connector
from flask_jwt_extended import JWTManager
from datetime import datetime,timedelta
from project.authentication import authentication_bp
from project.admin import admin_bp
from project.client import client_bp
from project.escort import escort_bp
from flask_mail import Mail, Message



app=Flask(__name__, template_folder='templates')


# app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:''@localhost/task_26_4'

app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = '2@gmail.com'
app.config['MAIL_PASSWORD'] = 'sftregmvkvgvc'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail(app)
# @app.route("/")
# def hf():
#     cur = g.db.cursor()
#     cur.execute('SELECT * FROM user')
#     res = cur.fetchall()
#     print(res)
#     return "hdgvjdf"

@app.before_request
def before_request():
    g.mail = Mail(app)
    g.db = mysql.connector.connect(
        user=os.environ['MYSQL_USER'],
        password = os.environ['MYSQL_PASSWORD'],
        host = os.environ['MYSQL_HOST'],
        database = os.environ['MYSQL_DB']
    )



@app.after_request
def after_request(response):
    g.db.close()
    return response


app.config['JWT_SECRET_KEY'] = os.environ['JWT_SECRET_KEY']
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=1)

jwt = JWTManager(app)

app.register_blueprint(authentication_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(client_bp)
app.register_blueprint(escort_bp)


