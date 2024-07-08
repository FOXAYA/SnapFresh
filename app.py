import os
import re
from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.utils import secure_filename
from flask_mysqldb import MySQL
import MySQLdb.cursors
import numpy as np
from tensorflow.keras.preprocessing import image
from tensorflow.keras.models import load_model
from PIL import Image, ImageFile
import my_tf_mod
from io import BytesIO
import matplotlib.pyplot as plt
import base64

# Initialize the Flask application
app = Flask(__name__)

# Configuration for MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'medhat2030'
app.config['MYSQL_DB'] = 'UserAuthentication'
app.config['MYSQL_UNIX_SOCKET'] = '/var/run/mysqld/mysqld.sock'

# Initialize MySQL
mysql = MySQL(app)

# Secret key for session management
app.secret_key = 'your_secret_key'

# Force TensorFlow to use CPU only
os.environ['CUDA_VISIBLE_DEVICES'] = '-1'

@app.route('/register', methods=['GET', 'POST'])
def register():
    msg = ''
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']

        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * FROM accounts WHERE username = %s', (username,))
        account = cursor.fetchone()

        if account:
            msg = 'Account already exists!'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address!'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'Username must contain only characters and numbers!'
        elif not username or not password or not email:
            msg = 'Please fill out the form!'
        else:
            cursor.execute('INSERT INTO accounts (username, password, email) VALUES (%s, %s, %s)', (username, password, email))
            mysql.connection.commit()
            msg = 'You have successfully registered!'
            return redirect(url_for('login'))  # Redirect to login after successful registration

    return render_template('register.html', msg=msg)

@app.route('/login', methods=['GET', 'POST'])
def login():
    msg = ''
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * FROM accounts WHERE username = %s AND password = %s', (username, password))
        account = cursor.fetchone()

        if account:
            session['loggedin'] = True
            session['id'] = account[0]
            session['username'] = account[1]
            msg = 'Logged in successfully!'
            return redirect(url_for('home'))  # Redirect to home after successful login
        else:
            msg = 'Incorrect username / password! Please try again.'

    return render_template('login.html', msg=msg)


@app.route('/')
def home():
    if 'loggedin' in session:
        return render_template('home.html')
    return redirect(url_for('login'))  # Redirect to login if not logged in

@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/Prediction', methods=['GET', 'POST'])
def pred():
    if request.method == 'POST':
        file = request.files['file']
        org_img, img = my_tf_mod.preprocess(file)

        print(img.shape)
        fruit_dict = my_tf_mod.classify_fruit(img)
        rotten = my_tf_mod.check_rotten(img)

        img_x = BytesIO()
        plt.imshow(org_img / 255.0)
        plt.savefig(img_x, format='png')
        plt.close()
        img_x.seek(0)
        plot_url = base64.b64encode(img_x.getvalue()).decode('utf8')

        return render_template('Pred3.html', fruit_dict=fruit_dict, rotten=rotten, plot_url=plot_url)
    return render_template('Pred3.html')

if __name__ == '__main__':
    app.run(debug=True)
