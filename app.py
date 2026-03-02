import smtplib
from email.mime.text import MIMEText
import random
import time
from flask import Flask, render_template, request, redirect,session
import mysql.connector
import bcrypt

#------------------EMAIL -----------------
def send_otp_email(receiver_email,otp):
    sender_email ="yourgmail@gmail.com"
    app_password="dtvrnqeprmzlchkk"
    
    message= MIMEText("Your OTP is:{otp}")
    message["Subject"] = "Your Verification OTP"
    message["From"] = sender_email
    message["To"] =receiver_email
    
    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(sender_email, app_password)
    server.send_message(message)
    server.quit()

app = Flask(__name__)
app.secret_key = "supersecretkey"

#database connection
db = mysql.connector.connect(
    host= "localhost",
    user ="root",
    password ="",
    database ="sms_db"
)

cursor= db.cursor(dictionary=True)

#-----------------------------signup--------------------------
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        form_data ={
            "name" : request.form['name'],
            "email" : request.form['email'],
            "phone" : request.form['phone'],
            "gender" : request.form["gender"],
            "tid" : request.form['tid'],
            "department" : request.form['department'],
            "designation" : request.form['designation'],
            "subject" : request.form['subject'],
            "password": request.form['password']
        }
        
        otp = str(random.randint(100000, 999999))
        session['temp_user'] = form_data
        session['otp'] = otp
        session['otp_time'] =time.time()  #current time store
        
        send_otp_email(form_data["email"], otp)
        return redirect('/verify-otp')
    return render_template('signup.html')

#----------------------------VERIFY OTP----------------
@app.route("/verify-otp", methods=['GET', 'POST'])
def verify_otp():
    if request.method == 'POST':
        user_otp = request.form['otp']
        
        saved_otp = session.get("otp")
        otp_time= session.get("otp_time")
        
        #_______check expiry(5 min == 300sec)-------
        if not otp_time or time.time() - otp_time > 300:
            session.pop("otp", None)
            session.pop("temp_user", None)
            session.pop("otp_time", None)
            return "OTP expired.Please signup again."
        
        if user_otp == saved_otp:
            data = session.get("temp_user")
            
            hashed_password = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt())
            
        cursor.execute("INSERT INTO teachers (name, email, phone, gender, tid, department, designation, subject, password) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                       (
                           data['name'], data['email'], data['phone'], data['gender'], data['tid'], data['department'], data['designation'], data['subject'], hashed_password   
                       ))
        db.commit()
        session.clear()
        return redirect("/login")
    else:
        return "Invalid OTP"
    
    return render_template("otp.html")
    #     session.pop('temp_user', None)
        
    #     return redirect('/login')
    # else:
    #     return "Invalid OTP"
    # return render_template("otp.html")
        
    #     #------------hash password------------------
    #     hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    #     #insert into db----------
    #     try:
    #         cursor.execute("INSERT INTO teachers (name, email, phone, gender, tid, department, designation, subject, password) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
    #         (name, email, phone,gender, tid, department, designation, subject,hashed_password))
    #         db.commit()
    #         return redirect('/login')
    #     except:
    #         return "Email or TID already exists. Please try again with different credentials."
        
        
    # return render_template('signup.html')
#-------------------------LOGIN------------------------------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password'].encode('utf-8')

        cursor.execute("SELECT * FROM teachers WHERE email = %s", (email,))
        user = cursor.fetchone()

        if user and bcrypt.checkpw(password, user['password'].encode('utf-8')):
            session['user_id'] = user['id']
            return redirect('/dash')
        else:
            return "Invalid email or password. Please try again."
    return render_template('login.html')

#----------------------------DASHBOARD----------------
@app.route('/dash')
def dashboard():
    if 'teacher_id' in session:
        return render_template('dash.html')
    else:
        return redirect('/login')
    
#-----------------------LOGOUT---------------
@app.route('/logout')
def logout():
    session.pop('teacher_id', None)
    return redirect('/login')
    
if __name__ == '__main__':
    app.run(debug=True)
    
