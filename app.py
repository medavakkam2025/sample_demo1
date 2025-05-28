from flask import Flask, render_template, request, redirect, url_for, flash
from pymongo import MongoClient
import pandas as pd
from werkzeug.security import generate_password_hash, check_password_hash
import csv
from io import StringIO
from flask import Response

app = Flask(__name__)
app.secret_key = "secretkey"

# MongoDB setup
client = MongoClient("mongodb://localhost:27017/")
db = client["magicbusportal"]
worklogs = db["worklogs"]
collections = {
    "student": db["student_collection"],
    "employer": db["employers"],
    "citymanager": db["citymanagers"]
}
job_collection = db['job_postings']

@app.route('/')
def login_page():
    return render_template('login.html')
@app.route('/post-job', methods=['GET', 'POST'])
def post_job():
    if request.method == 'POST':
        job_data = {
            "title": request.form['title'],
            "company": request.form['company'],
            "location": request.form['location'],
            "description": request.form['description'],
            "salary": request.form['salary'],
        }
        job_collection.insert_one(job_data)
        flash("Job posted successfully!")
        return redirect(url_for('post_job'))
    return render_template('post-job.html')
@app.route('/job-list')
def job_list():
    jobs = job_collection.find()
    return render_template('job-list.html', jobs=jobs)

@app.route('/admin')
def signup_page():
    return render_template('Admin/signup.html')

@app.route('/signup', methods=['POST'])
def handle_signup():
    username = request.form['username'].strip()
    password = request.form['password'].strip()
    phone = request.form['phone'].strip()
    dob = request.form['dob'].strip()
    role = request.form['role'].strip()

    if role not in collections:
        flash("Invalid role selected")
        return redirect(url_for('signup_page'))

    collection = collections[role]

    # Check if username already exists
    if collection.find_one({'username': username}):
        flash("Username already exists!")
        return redirect(url_for('signup_page'))

    hashed_pw = generate_password_hash(password)

    # Insert new user
    collection.insert_one({
        "username": username,
        "phone": phone,
        "dob": dob,
        "role": role,
        "password": hashed_pw
    })

    flash("Signup successful. Please log in.")
    return redirect(url_for('login_page'))
@app.route('/login', methods=['POST'])
def handle_login():
    phone = request.form['phone'].strip()
    dob = request.form['dob'].strip()
    role = request.form['role'].strip()

    if role not in collections:
        flash("Invalid role selected")
        return redirect(url_for('login_page'))

    collection = collections[role]

    # Find user by phone, dob, and role only (NOT password)
    user = collection.find_one({
        'phone': phone,
        'dob': dob,
    })

    # Check if user exists and verify password hash
    if user:
        flash(f"Login successful! Welcome, {role}")
        if role == 'student':
            return redirect(url_for('student_dashboard'))
        elif role == 'employer':
            return redirect(url_for('employer_dashboard'))
        elif role == 'citymanager':
            return redirect(url_for('citymanager_dashboard'))
    else:
        flash("Invalid login credentials. Please check all fields.")
        return redirect(url_for('login_page'))


@app.route('/student/dashboard')
def student_dashboard():
    return render_template('student-dashboard.html')

@app.route('/employer/dashboard')
def employer_dashboard():
    return render_template('dashboard.html')

@app.route('/citymanager/dashboard')
def citymanager_dashboard():
    return render_template('citymanager-dashboard.html')

@app.route('/placement-dashboard')
def placementdashboard():
    return render_template('placement-dashboard.html')


@app.route('/upload_excel', methods=['POST'])
def upload_excel():
    if 'file' not in request.files:
        flash("No file part")
        return redirect(request.url)

    file = request.files['file']

    if file.filename == '':
        flash("No selected file")
        return redirect(request.url)

    if file and file.filename.endswith('.xlsx'):
        try:
            df = pd.read_excel(file)
            required_columns = [
                'SixerClass ID', 'Name', 'phone', 'Gender', 'Date of birth', 'Age',
                'Qualification', 'College', 'Center', 'Batch Id', 'Batch', 'City', 'Address' ,
            ]
            if not all(col in df.columns for col in required_columns):
                flash("Excel file format incorrect. Please follow the template.")
                return redirect('/')

            records = df.to_dict(orient='records')
            if records:
                collections['student'].insert_many(records)
                flash(f"{len(records)} students inserted successfully!")
            else:
                flash("Excel file is empty.")
        except Exception as e:
            flash(f"Error processing file: {e}")
    else:
        flash("Please upload a valid .xlsx file.")

    return redirect('/')
@app.route("/work-tracker", methods=["GET", "POST"])
def work_tracker():
    if request.method == "POST":
        officer = request.form["officer"]
        date = request.form["date"]
        activity = request.form["activity"]
        remarks = request.form["remarks"]

        worklogs.insert_one({
            "officer_name": officer,
            "date": date,
            "activity": activity,
            "remarks": remarks
        })
        return redirect(url_for('work_tracker'))

    all_logs = list(worklogs.find().sort("date", -1))
    return render_template("work-tracker.html", logs=all_logs)


if __name__ == '__main__':
    app.run(debug=True)
