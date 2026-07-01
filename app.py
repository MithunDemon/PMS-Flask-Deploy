from flask import Flask, render_template, request, redirect
import mysql.connector
import os
from flask import request, render_template
from werkzeug.utils import secure_filename
from datetime import datetime
import random


app = Flask(__name__, template_folder='mian')

# Database Connection
def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="msr",
        database="pm",
        port=3309,
        use_pure=True,
        charset="utf8"
    )

# Home Page

# Paste here 👇
UPLOAD_LICENSE = "uploads/license"
UPLOAD_CERTIFICATE = "uploads/certificate"
UPLOAD_SHOP = "uploads/shop"

app.config["UPLOAD_LICENSE"] = UPLOAD_LICENSE
app.config["UPLOAD_CERTIFICATE"] = UPLOAD_CERTIFICATE
app.config["UPLOAD_SHOP"] = UPLOAD_SHOP


@app.route('/')
def home():
    return render_template('home.html')

    

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        pharmacy_name = request.form["pharmacy_name"]
        owner_name = request.form["owner_name"]
        username = request.form["username"]
        password = request.form["password"]
        mobile = request.form["mobile"]
        email = request.form["email"]
        license_no = request.form["license_no"]
        gst = request.form["gst"]
        address = request.form["address"]

        license_file = request.files["license_file"]
        certificate_file = request.files["certificate_file"]
        shop_photo = request.files["shop_photo"]

        license_name = secure_filename(license_file.filename)
        certificate_name = secure_filename(certificate_file.filename)
        shop_name = secure_filename(shop_photo.filename)

        license_file.save(os.path.join(app.config["UPLOAD_LICENSE"], license_name))
        certificate_file.save(os.path.join(app.config["UPLOAD_CERTIFICATE"], certificate_name))
        shop_photo.save(os.path.join(app.config["UPLOAD_SHOP"], shop_name))

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
        INSERT INTO pharmacy_requests
        (pharmacy_name, owner_name, username, password,
        mobile, email, drug_license_no, gst_number,
        address, license_file, certificate_file, shop_photo, status)

        VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'Pending')
        """,(pharmacy_name, owner_name, username, password,
             mobile, email, license_no, gst,
             address, license_name, certificate_name, shop_name))

        conn.commit()

        cursor.close()
        conn.close()

        return "Registration Request Submitted Successfully!"

    return render_template("register.html")


@app.route("/admin", methods=["GET", "POST"])
def admin():

    message = ""

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        if username == "admin" and password == "admin123":
            return redirect("/admin_dashboard")
    
        else:
            message = "Invalid Admin Login"

    return render_template("admin_login.html", message=message)



@app.route("/admin_dashboard")
def admin_dashboard():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM pharmacy_requests")
    users = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("admin_dashboard.html", users=users)

@app.route("/dashboard")
def dashboard():
    return render_template("index.html")
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM pharmacy_requests
            WHERE username=%s AND password=%s
        """, (username, password))

        user = cursor.fetchone()

        if user:
            if user[13] == "Approved":   # Status column
                return redirect("/dashboard")
            elif user[13] == "Pending":
                return "Your account is waiting for admin approval."
            else:
                return "Your account has been rejected."

        return "Invalid Username or Password."

    return render_template("pharmacy_login.html")

@app.route("/approve/<int:id>")
def approve(id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE pharmacy_requests SET status='Approved' WHERE id=%s",
        (id,)
    )

    conn.commit()

    cursor.close()
    conn.close()

    return redirect("/admin_dashboard")
@app.route("/reject/<int:id>")
def reject(id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE pharmacy_requests SET status='Rejected' WHERE id=%s",
        (id,)
    )

    conn.commit()

    cursor.close()
    conn.close()

    return redirect("/admin_dashboard")
@app.route('/create_account', methods=['POST'])
def create_account():
    try:
        account_name = request.form['account_name'].strip()

        conn = get_connection()
        cursor = conn.cursor()

        sql = f"""
        CREATE TABLE {account_name} (
            bid VARCHAR(100),
            name VARCHAR(100),
            company VARCHAR(100),
            price VARCHAR(100),
            stock VARCHAR(100),
            date VARCHAR(100)
        )
        """

        cursor.execute(sql)
        conn.commit()

        return f"Table {account_name} created successfully"

    except Exception as e:
        return str(e)

@app.route("/add")
def add():
    return render_template("add.html")

@app.route('/save_medicine', methods=['POST','GET'])
def save_medicine():

    account_name = request.form['account_name']
    bid = request.form['bid']
    name = request.form['name']
    company = request.form['company']
    stock = request.form['stock']
    price = request.form['price']
    date = request.form['date']

    conn = get_connection()
    cursor = conn.cursor(buffered=True)

    # Check account exists or not
    cursor.execute("SHOW TABLES LIKE %s", (account_name,))
    result = cursor.fetchone()

    if result is None:
        cursor.close()
        conn.close()
        return "Account Name Not Found! Please Create Account First."

    check_sql = f"SELECT stock FROM {account_name} WHERE name=%s"
    cursor.execute(check_sql, (name,))
    data = cursor.fetchone()

    
    if data:

        current_stock = int(data[0])
        total_stock = current_stock + int(stock)

        update_sql = f"""
    UPDATE {account_name}
    SET stock=%s,
        company=%s,
        price=%s,
        date=%s
    WHERE name=%s
    """

        cursor.execute(update_sql,
                   (total_stock, company, price, date, name))

    else:

        insert_sql = f"""
    INSERT INTO {account_name}
    (bid, name, company, price, stock, date)
    VALUES (%s,%s,%s,%s,%s,%s)
    """

        cursor.execute(insert_sql,
                   (bid, name, company, price, stock, date))
    conn.commit()

    cursor.close()
    conn.close()

    return """
<script>
alert('Medicine Saved Successfully');
window.location.href='/add';
</script>
"""


@app.route('/searchmedicine', methods=['GET', 'POST'])
def searchmedicine():

    result = ""

    if request.method == 'POST':

        account_name = request.form['account_name']
        medicine_name = request.form['medicine_name']

        conn = get_connection()
        cursor = conn.cursor(buffered=True)

        cursor.execute("SHOW TABLES LIKE %s", (account_name,))
        table = cursor.fetchone()

        if table is None:
            result = "Account Name Not Found!"
        else:
            sql = f"SELECT * FROM {account_name} WHERE name=%s"
            cursor.execute(sql, (medicine_name,))
            medicine = cursor.fetchone()

            if medicine:
                result = f"""
                B.NO : {medicine[0]}<br>
                Name : {medicine[1]}<br>
                Company : {medicine[2]}<br>
                Price : {medicine[3]}<br>
                Stock : {medicine[4]}<br>
                Date : {medicine[5]}
                """
            else:
                result = "Medicine Not Found!"

        cursor.close()
        conn.close()
        
    return render_template("searchmedicine.html", result=result)



@app.route('/update', methods=['GET', 'POST'])
def update():

    resul = ""

    if request.method == 'POST':

        account_name = request.form['account_name']
        medicine_name = request.form['medicine_name']
        new_stock = request.form['stock']

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SHOW TABLES LIKE %s", (account_name,))
        table = cursor.fetchone()

        if table is None:
            resul = "Account Name Not Found!"

        else:
            sql = f"UPDATE {account_name} SET stock=%s WHERE name=%s"
            cursor.execute(sql, (new_stock, medicine_name))
            conn.commit()

            if cursor.rowcount > 0:
                resul = "Stock Updated Successfully"
            else:
                resul = "Medicine Not Found"

        cursor.close()
        conn.close()

    return render_template("searchmedicine.html", resul=resul)


@app.route('/view', methods=['GET', 'POST'])
def view():

    medicines = []

    if request.method == 'POST':

        account_name = request.form['account_name']

        conn = get_connection()
        cursor = conn.cursor()

        # Check account exists
        cursor.execute("SHOW TABLES LIKE %s", (account_name,))
        table = cursor.fetchone()

        if table is None:
            return render_template("view.html",
                                   medicines=[],
                                   message="Account Name Not Found!")

        sql = f"SELECT * FROM {account_name}"
        cursor.execute(sql)

        medicines = cursor.fetchall()

        cursor.close()
        conn.close()

        return render_template("view.html",
                               medicines=medicines,
                               message="")

    return render_template("view.html",
                           medicines=[],
                           message="")


@app.route('/delete', methods=['GET', 'POST'])
def delete():

    messag = ""

    if request.method == "POST":

        account_name = request.form["account_name"]
        medicine_name = request.form["medicine_name"]

        conn = get_connection()
        cursor = conn.cursor()

        # Check account table exists
        cursor.execute("SHOW TABLES LIKE %s", (account_name,))
        table = cursor.fetchone()

        if table is None:
            message = "Account Name Not Found!"

        else:
            sql = f"DELETE FROM {account_name} WHERE name=%s"
            cursor.execute(sql, (medicine_name,))
            conn.commit()

            if cursor.rowcount > 0:
                message = "Medicine Deleted Successfully!"
            else:
                message = "Medicine Not Found!"

        cursor.close()
        conn.close()

    return render_template("view.html", messag=messag)
@app.route('/billing', methods=['GET', 'POST'])
def billing():

    
    messa = ""

    if request.method == "POST":

        account_name = request.form["account_name"]
        customer_name = request.form["customer_name"]
        customer_mobile = request.form["customer_mobile"]

        medicine_names = request.form.getlist("medicine_name[]")
        quantities = request.form.getlist("quantity[]")

        
        payment = request.form["payment"]

        discount = float(request.form["discount"])
        gst = float(request.form["gst"])

        conn = get_connection()
        cursor = conn.cursor(buffered=True)

        # Check pharmacy account
        cursor.execute("SHOW TABLES LIKE %s", (account_name,))
        table = cursor.fetchone()

        if table is None:

            messa = "Account Name Not Found!"

        else:

            grand_total = 0
            invoice = ""

            bill_no = "BILL" + str(random.randint(1000, 9999))
            today = datetime.now().strftime("%d-%m-%Y")
            current_time = datetime.now().strftime("%I:%M %p")

            for i in range(len(medicine_names)):

                medicine = medicine_names[i].strip()
                qty = int(quantities[i])

                sql = f"""
                SELECT company, price, stock
                FROM {account_name}
                WHERE name=%s
                """

                cursor.execute(sql, (medicine,))
                data = cursor.fetchone()

                if data:

                    company = data[0]
                    price = int(data[1])
                    stock = int(data[2])

                    if qty > stock:

                        messa = f"{medicine} stock is not available."
                        break

                    total = price * qty

                    grand_total += total

                    new_stock = stock - qty

                    update = f"""
                    UPDATE {account_name}
                    SET stock=%s
                    WHERE name=%s
                    """

                    cursor.execute(update, (new_stock, medicine))

                    invoice += f"""
                    <tr>
                        <td>{medicine}</td>
                        <td>{company}</td>
                        <td>{qty}</td>
                        <td>₹{price}</td>
                        <td>₹{total}</td>
                        <td>{new_stock}</td>
                    </tr>
                    """

                else:

                    messa = f"{medicine} not found."
                    break

            conn.commit()
            if messa == "":



                # Discount & GST
                discount_amount = grand_total * discount / 100

                subtotal = grand_total - discount_amount

                gst_amount = subtotal * gst / 100

                final_total = subtotal + gst_amount

                messa = f"""

                        <center>

                        <h1>{customer_name} MEDICAL STORE</h1>

                        <h3>PHARMACY BILL</h3>

                    </center>

                    <hr>

                    <b>Bill No :</b> {bill_no}<br>
                    <b>Date :</b> {today}<br>
                    <b>Time :</b> {current_time}<br><br>

                    <b>Customer Name :</b> {customer_name}<br>
                    <b>Customer Mobile :</b> {customer_mobile}<br>
                   
                    <b>Payment :</b> {payment}<br>

                    <hr>

                    <table border="1" width="100%" cellpadding="8">

                    <tr style="background:#0d6efd;color:white;">

                    <th>Medicine</th>
                    <th>Company</th>
                    <th>Qty</th>
                    <th>Price</th>
                    <th>Total</th>
                    <th>Stock Left</th>

                    </tr>

                    {invoice}

                </table>

                <br>

                <table width="40%" align="right">

                <tr>
                    <td><b>Subtotal</b></td>
                        <td>₹{grand_total}</td>
                </tr>

                <tr>
                        <td><b>Discount ({discount}%)</b></td>
                        <td>₹{discount_amount:.2f}</td>
                </tr>

                <tr>
                        <td><b>GST ({gst}%)</b></td>
                        <td>₹{gst_amount:.2f}</td>
                </tr>

                <tr>
                        <td><h3>Grand Total</h3></td>
                        <td><h3>₹{final_total:.2f}</h3></td>
                </tr>

                </table>

                <br><br><br><br><br><br>

                <center>

                <button onclick="window.print()"
                style="padding:12px 30px;
                background:green;
                color:white;
                border:none;
                border-radius:8px;
                font-size:18px;
                cursor:pointer;">

                Print Bill

                </button>

                <br><br>

                <h3 style="color:green;">
                Thank You! Visit Again
                </h3>

                </center>

                """

        cursor.close()
        conn.close()

    return render_template("billing.html", messa=messa)
if __name__ == '__main__':
    app.run(debug=True)