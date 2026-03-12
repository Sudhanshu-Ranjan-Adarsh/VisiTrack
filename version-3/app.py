from flask import make_response
import smtplib
from email.mime.text import MIMEText
import random
import time
from flask import jsonify
from flask_mail import Mail, Message
import mysql.connector
import bcrypt
from flask import Flask, render_template, request, redirect, session, flash, url_for
import os
from werkzeug.utils import secure_filename



app = Flask(__name__)
app.secret_key = "visitrack_secret_key"

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'sudhanshu99964@gmail.com' 
app.config['MAIL_PASSWORD'] = 'rcqzhjfqeffxyqry' #replace with apna app password
mail = Mail(app)


# Database connection
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="sms_db"
)

# Helper function for DB cursor
def get_cursor():
    return db.cursor(dictionary=True)

# ----------------- SIGNUP ROUTE -----------------
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        # HTML ke 'name' attributes se data uthana
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('number') # HTML mein 'number' hai
        dept = request.form.get('department')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash("Passwords do not match!", "danger")
            return redirect(url_for('signup'))
        
        #TID GENERATE------------------
        name_part = name.replace(" ","").upper()[:4]
        phone_part = phone[-4:]
        generated_tid = f"{name_part}{phone_part}"

        # Password Hash karna
        hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        cursor = get_cursor()
        try:
            sql = "INSERT INTO teachers (name, email, phone, tid, department, password) VALUES (%s, %s, %s, %s, %s, %s)"
            cursor.execute(sql, (name, email, phone, generated_tid, dept, hashed_pw))
            db.commit()
            
            flash(f"Account Created! Your TID is: {generated_tid}. Use this to login.", "success")
            return redirect(url_for('login'))
        except Exception as e:
            db.rollback()
            flash("Registration failed. TID or Email might already exists!", "danger")
            return redirect(url_for('signup'))
            
    return render_template('signup.html')

# ----------------- LOGIN ROUTE -----------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        tid = request.form.get('tid')
        password = request.form.get('password').encode('utf-8')
        remember = request.form.get('remember')

        cursor = get_cursor()
        cursor.execute("SELECT * FROM teachers WHERE tid = %s", (tid,))
        user = cursor.fetchone()

        if user and bcrypt.checkpw(password, user['password'].encode('utf-8')):
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            
            resp = make_response(redirect(url_for('home')))
            if remember:
                resp.set_cookie('rem_tid', tid, max_age=30*24*60*60)
            else:
                resp.set_cookie('rem_tid', expires=0)
            
            flash("Login Successful! Redirecting to Home...", "success")
            return resp
        else:
            flash("Invalid credentials. Please try again.", "danger")
            return redirect(url_for('login'))

    return render_template('login.html')

#--------------Forgot_Password--------------------
@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        tid = request.form.get('tid')
        cursor = get_cursor()
        cursor.execute("SELECT email FROM teachers WHERE tid = %s", (tid,))
        user = cursor.fetchone()

        if user:
            otp = str(random.randint(100000, 999999))
            session['reset_otp'] = otp
            session['reset_tid'] = tid
            
            # logic to send email (Flask-Mail use)
            msg = Message('Password Reset OTP', sender='your-email@gmail.com', recipients=[user['email']])
            msg.body = f"Your OTP to reset password is {otp}"
            mail.send(msg)
            
            flash("OTP sent to your registered email.", "info")
            return redirect(url_for('reset_password'))
        else:
            flash("TID not found!", "danger")
            
    return render_template('forgot_password.html')

@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        user_otp = request.form.get('otp')
        new_pw = request.form.get('new_password')
        
        if user_otp == session.get('reset_otp'):
            hashed_pw = bcrypt.hashpw(new_pw.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            tid = session.get('reset_tid')
            
            cursor = get_cursor()
            cursor.execute("UPDATE teachers SET password = %s WHERE tid = %s", (hashed_pw, tid))
            db.commit()
            
            session.pop('reset_otp', None)
            flash("Password updated successfully! Please login.", "success")
            return redirect(url_for('login'))
        else:
            flash("Invalid OTP!", "danger")
            
    return render_template('reset_password.html') # Isme OTP aur New Password field honge


# ----------------- HOME PAGE ----------------->
@app.route('/home')
def home():
    if 'user_id' in session:
        cursor = get_cursor()
        cursor.execute("SELECT*FROM teachers WHERE id = %s", (session['user_id'],))
        user_data = cursor.fetchone()
        return render_template('home_page.html', user = user_data)
    return redirect(url_for('login'))

#---------------ANALYSIS PAGE-----------------
@app.route('/analysis')
def analysis():
    if 'user_id' in session:
        cursor = get_cursor()
        cursor.execute("SELECT*FROM teachers WHERE id = %s", (session['user_id'],))
        user_data = cursor.fetchone()
        return render_template('analysis.html', user = user_data)
    return redirect(url_for('login'))

#---------------RECORDS PAGE-----------------
@app.route('/records')
def records():
    if 'user_id' in session:
        cursor = get_cursor()
        cursor.execute("SELECT*FROM teachers WHERE id = %s", (session['user_id'],))
        user_data = cursor.fetchone()
        return render_template('records.html', user = user_data)
    return redirect(url_for('login'))

#---------------ATTENDANCE PAGE-----------------
@app.route('/attendance')
def attendance():
    if 'user_id' in session:
        return render_template('mark_attendance.html')
    return redirect(url_for('login'))

#---------------SETTING PAGE-----------------
@app.route('/setting')
def setting():
    if 'user_id' in session:
        cursor = get_cursor()
        cursor.execute("SELECT*FROM teachers WHERE id = %s", (session['user_id'],))
        user_data = cursor.fetchone()
        return render_template('setting.html', user = user_data)
    return redirect(url_for('login'))


#----------------User profile icon-------------------
@app.route('/logout')
def logout():
    # Session se user data remove karna
    session.clear() 
    flash("You have been logged out successfully.", "info")
    # Login page par redirect karna
    return redirect(url_for('login'))

@app.route('/log')
def log():
    return render_template('login.html')

#-----------------ABOUT PAgE -----------------
@app.route('/add_student')
def add_student():
    if 'user_id' in session:
        return render_template('add_student.html')
    return redirect(url_for('login'))


#------------------GALLERY PAGE---------------
@app.route('/gallery')
def gallery():
    if 'user_id' in session:
        return render_template('gallery.html')
    return redirect(url_for('login'))

#-------add student db conn----------

@app.route('/student', methods=['GET', 'POST'])
def student():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        # Form data fetch karna
        full_name = request.form.get('full_name')
        father_name = request.form.get('father_name')
        dob = request.form.get('dob')
        mobile = request.form.get('mobile')
        email = request.form.get('email')
        program = request.form.get('program')
        branch = request.form.get('branch')
        semester = request.form.get('semester')
        section = request.form.get('section')
        roll_no = request.form.get('roll_no')
        subject = request.form.get('subject') # New subject field
        username = request.form.get('username')
        temp_pw = request.form.get('temp_password')

        # Face Image handling (Base64 data handling - Javascript se aayega)
        # Abhi ke liye hum ise blank ya file path ki tarah treat karenge
        # face_img_name = f"{roll_no}.jpg"
        # # face_path = os.path.join(UPLOAD_FOLDER, face_img_name)

        cursor = get_cursor()
        try:
            sql = """INSERT INTO students 
                     (full_name, father_name, dob, mobile, email, program, branch, semester, section, roll_no, subject, face_data_path, username, password) 
                     VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
            
            # Temporary password ko bhi hash karna better rahega
            hashed_temp_pw = bcrypt.hashpw(temp_pw.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            cursor.execute(sql, (full_name, father_name, dob, mobile, email, program, branch, semester, section, roll_no, subject, username, hashed_temp_pw))
            db.commit()
            
            flash(f"Student {full_name} Registered Successfully!", "success")
            return redirect(url_for('student'))
        except Exception as e:
            db.rollback()
            flash(f"Error: {str(e)}", "danger")
            return redirect(url_for('student'))

    return render_template('add_student.html')

#---------card folder------------------------
# Image upload folder setup
app.config['UPLOAD_FOLDER_PROFILE'] = 'static/profiles'
if not os.path.exists(app.config['UPLOAD_FOLDER_PROFILE']):
    os.makedirs(app.config['UPLOAD_FOLDER_PROFILE'])

@app.route('/update_profile', methods=['POST'])
def update_profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    name = request.form.get('name')
    dept = request.form.get('department')
    phone = request.form.get('phone')
    address = request.form.get('address')
    desc = request.form.get('description')
    fb = request.form.get('facebook')
    tw = request.form.get('twitter')
    inst = request.form.get('instagram')

    cursor = get_cursor()
    
    # Handle Profile Image Upload
    file = request.files.get('profile_img')
    if file and file.filename != '':
        filename = secure_filename(f"user_{user_id}.jpg")
        file.save(os.path.join(app.config['UPLOAD_FOLDER_PROFILE'], filename))
        cursor.execute("UPDATE teachers SET profile_img = %s WHERE id = %s", (filename, user_id))

    # Update Text Data
    sql = """UPDATE teachers SET name=%s, department=%s, phone=%s, 
             office_address=%s, description=%s, facebook_url=%s, 
             twitter_url=%s, instagram_url=%s WHERE id=%s"""
    cursor.execute(sql, (name, dept, phone, address, desc, fb, tw, inst, user_id))
    db.commit()
    
    session['user_name'] = name # Update session name
    flash("Profile Updated Successfully!", "success")
    return redirect(url_for('setting'))

#-----------------support form-------------------
@app.route('/contact_support', methods=['POST'])
def contact_support():
    name = request.form.get('user_name')
    email = request.form.get('user_email')
    subject = request.form.get('subject')
    message_body = request.form.get('message')

    try:
        # for send message Message object
        msg = Message(subject=f"Support Request: {subject}",
                      sender=app.config['MAIL_USERNAME'],
                      recipients=['sudhanshu99964@gmail.com']) 
        
        msg.body = f"New Message from {name} ({email}):\n\n{message_body}"
        
        mail.send(msg)
        flash("Thank you! Your message has been sent to our support team successfully.", "success")
    except Exception as e:
        flash(f"Something went wrong when sending message: {str(e)}", "danger")

    return redirect(url_for('support'))


#---------------------Footer Route-------------------
@app.route('/terms')
def terms():
    return render_template('terms.html')

@app.route('/privacy')
def privacy():
    return render_template('privacy.html')

@app.route('/disclaimer')
def disclaimer():
    return render_template('disclaimer.html')

@app.route('/security')
def security():
    return render_template('security.html')

@app.route('/user')
def user():
    return render_template('user_manual.html')

@app.route('/brand')
def brand():
    return render_template('brand.html')

@app.route('/notes')
def notes():
    return render_template('release_notes.html')

@app.route('/support')
def support():
    return render_template('support.html')

@app.route('/feedback')
def feedback():
    return render_template('feedback.html')

@app.route('/story')
def story():
    return render_template('story.html')


# --- OTP Send Route -----------------------
@app.route('/send_otp', methods=['POST'])
def send_otp():
    email = request.json.get('email')
    if not email:
        return jsonify({"message": "Email is required"}), 400

    otp = str(random.randint(100000, 999999))
    session['otp'] = otp
    session['otp_expiry'] = time.time() + 40  # 40 Seconds expiry

    try:
        msg = Message('Your OTP for VisiTrack', sender=app.config['MAIL_USERNAME'], recipients=[email])
        msg.body = f"Your OTP is {otp}. Valid for 40 seconds only."
        mail.send(msg)
        return jsonify({"message": "OTP Sent Successfully!"}), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 500

# --- OTP Verify Route -------------same--------------------
@app.route('/verify_otp', methods=['POST'])
def verify_otp():
    user_otp = request.json.get('otp')
    
    stored_otp = session.get('otp')
    expiry = session.get('otp_expiry')

    if not stored_otp or not expiry:
        return jsonify({"message": "Please send OTP first"}), 400

    if time.time() > expiry:
        session.pop('otp', None)
        return jsonify({"message": "OTP Expired! (40s limit)"}), 400

    if user_otp == stored_otp:
        session['email_verified'] = True
        return jsonify({"message": "Verified Successfully!"}), 200
    else:
        return jsonify({"message": "Invalid OTP"}), 400

# ----------------- LOGOUT -----------------
# @app.route('/logout')
# def logout():
#     session.clear()
#     return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)