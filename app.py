from flask import Flask, render_template, request
from pymysql import connections
import os
import boto3
from config import *

app = Flask(__name__)

bucket = custombucket
region = customregion

db_conn = connections.Connection(
    host=customhost,
    port=3306,
    user=customuser,
    password=custompass,
    db=customdb

)
output = {}
table = 'users'


#changes made

var =12345


@app.route("/", methods=['GET', 'POST'])
def home():
    return render_template('Login_page.html')



@app.route("/createaccount", methods=['POST'])
def CreateAccount():
    username = request.form['username']
    password = request.form['password']
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    location = request.form['location']
    role = request.form['role']
    job= request.form['job']
    user_photo_file = request.files['user_photo_file']

    insert_sql = "INSERT INTO "+table+ " VALUES (%s, %s, %s, %s, %s, %s, %s)"
    cursor = db_conn.cursor()

    if user_photo_file.filename == "":
        return "Please select a file"

    try:

        cursor.execute(insert_sql, (username, password, first_name, last_name, location, role, job))
        db_conn.commit()
        

        user_image_file_name_in_s3 = "username-" + str(username) + "_photo_file"
        s3 = boto3.resource('s3')

        try:
            print("Data inserted in MySQL RDS... uploading image to S3...")
            s3.Bucket(custombucket).put_object(Key=user_image_file_name_in_s3, Body=user_photo_file)
            bucket_location = boto3.client('s3').get_bucket_location(Bucket=custombucket)
            s3_location = (bucket_location['LocationConstraint'])

            if s3_location is None:
                s3_location = ''
            else:
                s3_location = '-' + s3_location

            object_url = "https://s3{0}.amazonaws.com/{1}/{2}".format(
                s3_location,
                custombucket,
                user_image_file_name_in_s3)

        except Exception as e:
            return str(e)

    finally:
        cursor.close()

    print("all modification done...")
    return render_template('Dashboard.html', name=username,fname=first_name, lname=last_name, location=location, role=role, job=job)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        query = "SELECT COUNT(*) FROM users WHERE username =%s AND password = %s"
        cursor = db_conn.cursor()
        try:
            cursor.execute(query, (username, password))
            query = cursor.fetchone()
            check = query[0]
            if check == 1:
                query1 = "SELECT * FROM users WHERE username =%s AND password = %s"
                cursor1 = db_conn.cursor()
                query2="SELECT username, location, role, job FROM users;"
                try:
                    cursor1.execute(query1, (username, password))
                    query1 = cursor1.fetchone()
                    if query1:
                        uname, password, fname, lname, location, role, job = query1
                    else:
                        print("No user found")
                    cursor1.execute(query2)
                    query2 = cursor1.fetchall()
                finally:
                    cursor1.close()
                return render_template('Dashboard.html', name=uname,fname=fname, lname=lname, location=location, role=role, job=job, query2=query2)
            else:
                return "Invalid username or password"
        finally:
            cursor.close()
        
    return render_template('Login_page.html')


@app.route('/gotoCreateAccount', methods=['GET', 'POST'])
def gotoCreateAccount():
    return render_template('CreateAccount.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
