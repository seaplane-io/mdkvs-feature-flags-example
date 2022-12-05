# -*- coding: utf-8 -*-
#imports
from scripts import tabledef
from scripts import forms
from scripts import helpers
from flask import Flask, redirect, url_for,render_template , request, session
import json
import sys
import os

# importing seaplane
from seaplanekit import sea
from seaplanekit.model import Key

# setting our API key
sea.config.set_api_key("my-api-key")

app = Flask(__name__)
app.secret_key = os.urandom(12)  # Generic key for dev purposes only

# ======== Routing =========================================================== #
# -------- Login ------------------------------------------------------------- #
@app.route('/', methods=['GET', 'POST'])
def login():

    # request all feature flags from Seaplane
    ff_add_address = sea.metadata.get(key=Key(b'sign-up-team/address-field')).value.decode()
    ff_button_blue = sea.metadata.get(key=Key(b'color-team/signup-button-blue')).value.decode()
    ff_text_dutch = sea.metadata.get(key=Key(b'translation-team/dutch')).value.decode()

    if not session.get('logged_in'):
        form = forms.LoginForm(request.form)
        if request.method == 'POST':
            username = request.form['username'].lower()
            password = request.form['password']
            if form.validate():
                if helpers.credentials_valid(username, password):
                    session['logged_in'] = True
                    session['username'] = username
                    return json.dumps({'status': 'Login successful'})
                return json.dumps({'status': 'Invalid user/pass'})
            return json.dumps({'status': 'Both fields required'})
        return render_template('login.html', form=form, ff_add_address=ff_add_address, ff_button_blue=ff_button_blue, ff_text_dutch=ff_text_dutch)
    user = helpers.get_user()

    return render_template('home.html', user=user)


@app.route("/logout")
def logout():
    session['logged_in'] = False
    return redirect(url_for('login'))


# -------- Signup ---------------------------------------------------------- #
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if not session.get('logged_in'):
        form = forms.LoginForm(request.form)
        if request.method == 'POST':
            username = request.form['username'].lower()
            password = helpers.hash_password(request.form['password'])
            email = request.form['email']
            if form.validate():
                if not helpers.username_taken(username):
                    helpers.add_user(username, password, email)
                    session['logged_in'] = True
                    session['username'] = username
                    return json.dumps({'status': 'Signup successful'})
                return json.dumps({'status': 'Username taken'})
            return json.dumps({'status': 'User/Pass required'})
        return render_template('login.html', form=form)
    return redirect(url_for('login'))


# -------- Settings ---------------------------------------------------------- #
@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if session.get('logged_in'):
        if request.method == 'POST':
            password = request.form['password']
            if password != "":
                password = helpers.hash_password(password)
            email = request.form['email']
            helpers.change_user(password=password, email=email)
            return json.dumps({'status': 'Saved'})
        user = helpers.get_user()
        return render_template('settings.html', user=user)
    return redirect(url_for('login'))


# ======== Main ============================================================== #
if __name__ == "__main__":
    app.run(debug=True, use_reloader=True, host="0.0.0.0")
