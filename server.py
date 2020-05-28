from flask import Flask, render_template, redirect, request, session, flash, url_for, send_from_directory, jsonify
from mysqlconn import connectToMySQL
from flask_bcrypt import Bcrypt        
from datetime import datetime
import re
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import socket
import stripe

socket.setdefaulttimeout(30)
app = Flask(__name__)
app.secret_key = 'tho'
bcrypt = Bcrypt(app)

EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')
PASSWORD_REGEX = re.compile("^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!#%*?&]{6,20}$")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/logreg')
def logreg():
    return render_template('login.html')

@app.route("/register", methods = ["POST"])
def registration():
    is_valid = True

    if len(request.form['fname']) < 1:
        is_valid = False
        flash('Please endter a valid first name')
    if len(request.form['lname']) < 1:
        is_valid = False
        flash('Please enter a valid last name')
    if not EMAIL_REGEX.match(request.form['email']):
        is_valid = False
        flash('Invalid email address')
    if not PASSWORD_REGEX.match(request.form['pword']):
        is_valid = False
        flash('Must use combination of upper case, numbers, and special characters in password.')
    if len(request.form['pword']) < 5:
        is_valid = False
        flash('Password must be at least 5 characters long')
    if request.form['cpword'] != request.form['pword']:
        is_valid = False
        flash('Passwords entered do not match. Please try again')

    if is_valid:
        pw_hash = bcrypt.generate_password_hash(request.form['pword'])
        mysql = connectToMySQL('rentals')
        query = 'INSERT INTO tenants (first_name, last_name, email, address, password, created_at, updated_at) VALUES (%(fn)s, %(ln)s, %(em)s, %(ad)s, %(pw)s, NOW(), NOW())'
        data = {
            'fn': request.form['fname'],
            'ln': request.form['lname'],
            'em': request.form['email'],
            'ad': request.form['address'],
            'pw': pw_hash,
        }
        mysql = connectToMySQL("rentals")
        user_id = mysql.query_db(query, data)
        session['user_id'] = user_id
        flash("user successfully added!")

        return redirect('/welcome')
    else:
        return redirect('/')

@app.route('/login', methods=['POST'])
def login():
    is_valid = True

    if len(request.form['email']) < 1:
        is_valid = False
        flash('Please enter your email')
    if len(request.form['pword']) < 1:
        is_valid = False
        flash('Please enter your password')
    if not EMAIL_REGEX.match(request.form['email']):
        flash('Invalid email address')

    if not is_valid:
        return redirect('/')
    else:
        query = 'SELECT * FROM tenants WHERE tenants.email = %(em)s'
        data = {'em': request.form.get('email')}
        mysql = connectToMySQL('rentals')
        tenant = mysql.query_db(query, data)
        print(tenant)

        if tenant:
            hashed_password = tenant[0]['password']
            if bcrypt.check_password_hash(hashed_password, request.form['pword']):
                print('password entered')
                session['user_id'] = tenant[0]['id']
                session['user_name'] = tenant[0]['first_name']
                return redirect('/welcome')
            else:
                flash('Password incorrect')
                return redirect('/')
@app.route('/welcome')
def welcome():
    return render_template('welcome.html')

@app.route('/apply')
def apply():
    return render_template('apply.html')

@app.route('/cancel')
def cancel():
    return redirect('/')

@app.route('/submit_apply', methods=['POST'])
def submit_apply():
    my_address = 'kelly.delrio@yahoo.com'
    my_password = 'yjcovxmwoecwpxkz'

    textfile = 'Application data goes here' 

    s = smtplib.SMTP('smtp.mail.yahoo.com', 587)
    s.starttls()
    s.login(my_address, my_password)

    msg = MIMEMultipart()
    msg['From'] = my_address
    msg['To'] = my_address
    msg['Subject'] = 'New Rental Application Received'
    msg.attach(MIMEText(textfile, 'plain'))

    s.send_message(msg)
    del msg
    s.quit()
    
    flash('Thank you for your application.  One of our agents will be contacting you shortly.')
    return redirect('/')

@app.route('/maintenance')
def maintenance():
    return render_template('maintenance.html')

@app.route('/submit_maintenance', methods=['POST'])
def submit_maintenance():
    
    my_address = 'kelly.delrio@yahoo.com'

    """ yahoo 3rd party app password """

    my_password = 'yjcovxmwoecwpxkz'

    """ info from maintenance request form """

    textfile = 'From: ' + request.form['fname'] + ' ' + request.form['lname'] + '\nPhone Number: ' + request.form['phone'] + '\nMessage: ' + request.form['message']
   
    """ connect to smtp server """

    s = smtplib.SMTP('smtp.mail.yahoo.com', 587)
    s.starttls()
    s.login(my_address, my_password)

    """ create email template """

    msg = MIMEMultipart()
    msg['From'] = my_address
    msg['To'] = my_address
    msg['Subject'] = 'Maintenance Request Submission'
    msg.attach(MIMEText(textfile, 'plain'))

    """ send email """

    s.send_message(msg)
    del msg
    s.quit()
    
    flash('Thank you.  Your maintenance request has been received and an agent will be in touch shortly.')

    return redirect ("/welcome")

@app.route('/rent')
def rent():
    return render_template('rent.html')

@app.route('/submit_rent')
def submit_rent():
    stripe.api_key = 'pk_test_5zOM70LAPc4XW8c6nQuUU0kP00ZmuVAxYW'

    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{
            'price': '{price_HIViOd3Y2JlPLs}',
            'quantity': 1,
        }],
        mode='payment',
        success_url='/payment_success, session_id={CHECKOUT_SESSION_ID}',
        cancel_url='/payment_cancel',
    )

    return redirect("/welcome")

@app.route('/payment_success')
def payment_success():
    return redirect('/welcome')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/submit_contact', methods=['POST'])
def submit_contact():
    my_address = 'kelly.delrio@yahoo.com'
    my_password = 'yjcovxmwoecwpxkz'

    textfile = 'From: ' + request.form['fname'] + ' ' + request.form['lname'] + '\nEmail address: ' + request.form['email'] + '\nMessage: ' + request.form['message'] 

    s = smtplib.SMTP('smtp.mail.yahoo.com', 587)
    s.starttls()
    s.login(my_address, my_password)

    msg = MIMEMultipart()
    msg['From'] = my_address
    msg['To'] = my_address
    msg['Subject'] = 'Contact Form Submission'
    msg.attach(MIMEText(textfile, 'plain'))

    s.send_message(msg)
    del msg
    s.quit()
    
    flash('Thank you for contacting us.  One of our agents will be contacting you shortly.')
    
    return redirect ("/")

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')
    
if __name__ == "__main__":
    app.run(debug=True)