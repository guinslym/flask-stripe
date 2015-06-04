import sqlite3
from flask import (Flask, request, session, g,
    redirect, url_for, abort, render_template, flash)
from pymongo import MongoClient


app = Flask(__name__)
app.config.from_object('config')


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/items/create')
def create_item():
    return render_template('create_item.html')


def connect_db(database_name='rmotr_store', host='localhost', port=27017):
    return (MongoClient(host, port), MongoClient(host, port)[database_name])


@app.before_request
def before_request():
    g.connection, g.db = connect_db(
        database_name=app.config.get('DATABASE_NAME'),
        host=app.config.get('DATABASE_HOST'),
        port=app.config.get('DATABASE_PORT'))


@app.teardown_request
def teardown_request(exception):
    g.connection.close()


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['username'] != app.config['USERNAME']:
            error = 'Invalid username'
        elif request.form['password'] != app.config['PASSWORD']:
            error = 'Invalid password'
        else:
            session['logged_in'] = True
            flash('You were successfully logged in', 'success')
            return redirect(url_for('index'))
    if error:
        flash('An error ocurred while trying to log you in', 'error')
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You were successfully logged out', 'success')
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)
