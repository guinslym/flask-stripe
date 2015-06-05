from datetime import datetime
from flask import (Flask, request, session, g,
                   redirect, url_for, abort, render_template, flash)

from pymongo import MongoClient
from bson.objectid import ObjectId

import stripe
import secrets
stripe.api_key = secrets.STRIPE_SECRET_KEY


app = Flask(__name__)
app.config.from_object('config')


@app.route('/')
def index():
    items = g.db['items'].find()
    return render_template('index.html', items=items)

from forms import CreateItemForm


@app.route('/items/create', methods=['GET', 'POST'])
def create_item():
    form = CreateItemForm(request.form)
    if request.method == 'POST' and form.validate():
        items = g.db['items']
        items.insert_one({
            'name': form.item_name.data,
            'price': float(form.price.data),
            'description': form.description.data,
            'created': datetime.utcnow()
        })
        flash('The item was successfully created!', 'success')
        return redirect(url_for('index'))
    return render_template('create_item.html', form=form)


def get_stripe_customer(token, email):
    customers = g.db['customers']
    query = {'email': email}
    if customers.count(query) > 0:
        customer = customers.find_one(query)
        return stripe.Customer.retrieve(customer['stripe_id'])

    stripe_customer = stripe.Customer.create(email=email, source=token)
    customers.insert_one({
        'email': email,
        'stripe_id': stripe_customer.id
    })
    return stripe_customer


@app.route('/buy/<item_id>', methods=['GET', 'POST'])
def buy_item(item_id):
    item = g.db['items'].find_one({'_id': ObjectId(item_id)})

    if request.method == 'POST':
        email = request.form['email']
        token = request.form['stripeToken']
        stripe_customer = get_stripe_customer(token, email)
        stripe.Charge.create(
            amount=int(item['price'] * 100),
            currency='usd',
            customer=stripe_customer.id
        )
        flash(
            "You've successfully bough this item. "
            "Your CC was charged {}".format(item['price']), 'success')
        return redirect(url_for('index'))

    return render_template('buy_item.html', item=item)


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
        flash(error, 'error')
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You were successfully logged out', 'success')
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)
