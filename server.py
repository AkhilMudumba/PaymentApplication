from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_mail import Mail, Message
from datetime import datetime, timedelta
import random
import mysql.connector
from decimal import Decimal

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

otp_dict = {}

# Stripe test card numbers
stripe_test_cards = [
    "4242424242424242", "5555555555554444", "4000056655665556",
    "5200828282828210", "378282246310005"
]

# Flask-Mail configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = 'cnproject73@gmail.com'  # Replace with your email
app.config['MAIL_PASSWORD'] = 'owpr jzyi xdak nuaq'  # Use an app-specific password if 2FA is enabled
app.config['MAIL_DEFAULT_SENDER'] = 'cnproject73@gmail.com'

mail = Mail(app)

# Function to get database connection
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="mathan@123",
        database="banking_app"
    )


def generate_expiry_date():
    current_date = datetime.now()
    expiry_date = current_date + timedelta(days=365 * 5)  # 5 years from now
    return expiry_date.strftime('%m/%y')

def generate_cvc():
    return str(random.randint(100, 999))

def generate_account_number():
    return str(random.randint(100000000000, 999999999999))


# Endpoint to send OTP to email
@app.route('/send_otp', methods=['POST'])
def send_otp():
    data = request.get_json()
    email = data.get('email')
    
    if email:
        otp = random.randint(100000, 999999)  # Generate a 6-digit OTP
        otp_dict[email] = otp  # Store the OTP temporarily
        
        # Send OTP email
        try:
            msg = Message('Your OTP Code', recipients=[email])
            msg.body = f'Your OTP code is: {otp}'
            mail.send(msg)
            return jsonify({"message": "OTP sent successfully. Please verify."}), 200
        except Exception as e:
            return jsonify({"error": f"Error sending OTP: {e}"}), 500
    
    return jsonify({"error": "Email is required"}), 400

# Endpoint to verify OTP
@app.route('/verify_otp', methods=['POST'])
def verify_otp():
    data = request.get_json()
    email = data.get('email')
    otp = data.get('otp')
    
    if otp_dict.get(email) == int(otp):
        return jsonify({"message": "OTP verified successfully"}), 200
    return jsonify({"error": "Invalid OTP"}), 400

@app.route('/create_account', methods=['POST'])
def create_account():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    email = data.get('email')  # Added email field to be passed in the request

    # Ensure username, password, and email are provided
    if not username or not password or not email:
        return jsonify({"error": "Username, password, and email are required"}), 400

    # Check if OTP is verified using the email
    if email not in otp_dict:  # Ensure OTP verification is done via email
        return jsonify({"error": "OTP not verified"}), 400

    # Generate random card details and account number
    card_number = random.choice(stripe_test_cards)
    expiry_date = generate_expiry_date()
    cvc = generate_cvc()
    account_number = generate_account_number()
    balance = 100.00  # Default balance

    db = get_db_connection()
    cursor = db.cursor()

    try:
        # Insert the user data into the database, including email
        cursor.execute(""" 
            INSERT INTO users (username, password, email, card_number, expiry_date, cvc, account_number, balance)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (username, password, email, card_number, expiry_date, cvc, account_number, balance))
        db.commit()

        return jsonify({
            "message": "Account created successfully",
            "card_number": card_number,
            "expiry_date": expiry_date,
            "cvc": cvc,
            "account_number": account_number,
            "balance": balance
        })

    except mysql.connector.Error as err:
        print("Error:", err)
        return jsonify({"error": "Failed to create account"}), 500

    finally:
        cursor.close()  # Ensure cursor is closed
        db.close()  # Ensure database connection is closed


@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    db = get_db_connection()
    cursor = db.cursor()

    try:
        cursor.execute("SELECT * FROM users WHERE username = %s AND password = %s", (username, password))
        user = cursor.fetchone()

        if user:
            return jsonify({
                "message": "Login successful!",
                "user_id": user[0],  # Assuming the ID is in the first column
            })
        else:
            return jsonify({"message": "Invalid username or password"}), 401

    except mysql.connector.Error as err:
        print("Error:", err)
        return jsonify({"error": "Database error during login"}), 500

    finally:
        cursor.close()  # Ensure cursor is closed
        db.close()  # Ensure database connection is closed


@app.route('/account_balance/<int:user_id>', methods=['GET'])
def check_balance(user_id):
    db = get_db_connection()
    cursor = db.cursor()

    try:
        cursor.execute("SELECT balance FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()

        if user:
            return jsonify({"balance": user[0]})
        else:
            return jsonify({"error": "User not found"}), 404

    except mysql.connector.Error as err:
        print("Error:", err)
        return jsonify({"error": "Database error during balance check"}), 500

    finally:
        cursor.close()  # Ensure cursor is closed
        db.close()  # Ensure database connection is closed


@app.route('/withdraw/<int:user_id>', methods=['POST'])
def withdraw(user_id):
    data = request.json
    amount = Decimal(data.get('amount'))  # Convert amount to Decimal

    if amount <= 0:
        return jsonify({"error": "Invalid amount"}), 400

    db = get_db_connection()
    cursor = db.cursor()

    try:
        cursor.execute("SELECT balance FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()

        if user:
            current_balance = user[0]
            if current_balance >= amount:
                new_balance = current_balance - amount
                cursor.execute("UPDATE users SET balance = %s WHERE id = %s", (new_balance, user_id))
                db.commit()
                return jsonify({"message": f"Withdrawal successful! New balance: ${new_balance}"})
            else:
                return jsonify({"error": "Insufficient funds"}), 400
        else:
            return jsonify({"error": "User not found"}), 404

    except mysql.connector.Error as err:
        print("Error:", err)
        return jsonify({"error": "Database error during withdrawal"}), 500

    finally:
        cursor.close()  # Ensure cursor is closed
        db.close()  # Ensure database connection is closed


@app.route('/deposit/<int:user_id>', methods=['POST'])
def deposit(user_id):
    data = request.json
    amount = Decimal(data.get('amount'))  # Convert amount to Decimal

    if amount <= 0:
        return jsonify({"error": "Invalid amount"}), 400

    db = get_db_connection()
    cursor = db.cursor()

    try:
        cursor.execute("SELECT balance FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()

        if user:
            current_balance = user[0]
            new_balance = current_balance + amount
            cursor.execute("UPDATE users SET balance = %s WHERE id = %s", (new_balance, user_id))
            db.commit()
            return jsonify({"message": f"Deposit successful! New balance: ${new_balance}"})
        else:
            return jsonify({"error": "User not found"}), 404

    except mysql.connector.Error as err:
        print("Error:", err)
        return jsonify({"error": "Database error during deposit"}), 500

    finally:
        cursor.close()  # Ensure cursor is closed
        db.close()  # Ensure database connection is closed


@app.route('/account_details/<int:user_id>', methods=['GET'])
def account_details(user_id):
    db = get_db_connection()
    cursor = db.cursor()

    try:
        cursor.execute("SELECT username, email, card_number, account_number, balance FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()

        if user:
            return jsonify({
                "username": user[0],
                "email": user[1],
                "card_number": user[2],
                "account_number": user[3],
                "balance": user[4]
            })
        else:
            return jsonify({"error": "User not found"}), 404

    except mysql.connector.Error as err:
        print("Error:", err)
        return jsonify({"error": "Database error during account details retrieval"}), 500

    finally:
        cursor.close()  # Ensure cursor is closed
        db.close()  # Ensure database connection is closed


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5001)
