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
        user_name = "" + first_name + " " + last_name
        # Uplaod image file in S3 #
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
    return render_template('CreateAccountOutput.html', name=user_name)


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
                return "Login successful"
            else:
                return "Invalid username or password"
        finally:
            cursor.close()
        
    return render_template('Login_page.html')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
