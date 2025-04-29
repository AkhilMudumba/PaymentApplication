from flask import Flask, request, jsonify
import mysql.connector
import bcrypt
import stripe
from datetime import datetime
from flask_cors import CORS
import os
from mysql.connector import Error
from decimal import Decimal
from flask import Flask, request, jsonify
from flask_mail import Mail, Message
from decimal import Decimal
import stripe


import socket

app = Flask(__name__)
CORS(app)

# Stripe API key (use environment variable for security)
stripe.api_key = "sk_test_51QJmQoRtGFQ6ofjmEP3DciX8Xo2sJO7JnKAJSER8I5Hrd30dYD5rUkkOamzlk4WUZgrow1Yl3uu6Ef9CQ8LivZJ1007mDEhPVc"



# Database connection for banking_app
def get_banking_db_connection():
    conn_banking = mysql.connector.connect(
        host="localhost",
        user="root",  # Use actual username
        password="mathan@123",  # Use actual password
        database="banking_app"
    )
    return conn_banking


@app.route('/server-ip')
def get_server_ip():
    ip = socket.gethostbyname(socket.gethostname())  # Fetch the device's local IP address
    return jsonify({'ip': ip})


@app.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    account_number = data.get('account_number')  # New field for account number

    if not username or not password or not account_number:
        return jsonify({'message': 'Username, password, and account number are required'}), 400

    conn = get_banking_db_connection()
    cursor = conn.cursor()

    try:
        # Check if username or account number already exists in app_users
        cursor.execute(
            "SELECT * FROM app_users WHERE username = %s OR account_number = %s",
            (username, account_number)
        )
        if cursor.fetchone():
            return jsonify({'message': 'Username or account number already exists'}), 400

        # Insert new user into app_users table
        cursor.execute(
            "INSERT INTO app_users (username, password, account_number) VALUES (%s, %s, %s)",
            (username, password, account_number)
        )
        conn.commit()
        return jsonify({'message': 'User created successfully!'}), 201

    finally:
        cursor.close()
        conn.close()

        

# Login Route
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'message': 'Username and password are required'}), 400

    conn = get_banking_db_connection()
    cursor = conn.cursor()

    try:
        # Check if the user exists in app_users
        cursor.execute("SELECT * FROM app_users WHERE username = %s", (username,))
        user = cursor.fetchone()

        if not user:
            return jsonify({'message': 'User not found'}), 404

        # Verify the password
        user_id = user[0]  # Assuming user_id is the first column
        stored_password = user[2]  # Assuming password is the third column

        if password != stored_password:
            return jsonify({'message': 'Incorrect password'}), 401

        return jsonify({'message': 'Login successful!', 'user_id': user_id}), 200

    finally:
        cursor.close()
        conn.close()



@app.route('/balance/<int:user_id>', methods=['GET'])
def get_balance(user_id):
    # Validate the user_id from the URL parameter
    if not user_id:
        return jsonify({'message': 'User ID is required'}), 400

    conn = get_banking_db_connection()
    cursor = conn.cursor()

    try:
        # Fetch sender's account number from app_users table
        cursor.execute("SELECT account_number FROM app_users WHERE user_id = %s", (user_id,))
        sender_account = cursor.fetchone()

        if not sender_account:
            return jsonify({'message': 'Sender not found in app_users'}), 404

        sender_account_number = sender_account[0]

        # Fetch sender's balance from users table using the account number
        cursor.execute("SELECT balance FROM users WHERE account_number = %s", (sender_account_number,))
        sender_balance_result = cursor.fetchone()

        if not sender_balance_result:
            return jsonify({'message': 'Sender not found in users'}), 404

        sender_balance = sender_balance_result[0]

        # Return the balance as a response
        return jsonify({'account_number': sender_account_number, 'balance': str(sender_balance)}), 200

    except Exception as e:
        return jsonify({'message': str(e)}), 500

    finally:
        cursor.close()
        conn.close()

def check_card_number(user_id, provided_card_number):
    conn = get_banking_db_connection()
    cursor = conn.cursor()
    try:
        # Fetch the stored card number from the users table based on user_id
        cursor.execute("SELECT card_number FROM users WHERE id = %s", (user_id,))
        stored_card_number_result = cursor.fetchone()
        
        if not stored_card_number_result:
            return False, 'User not found'
        
        stored_card_number = stored_card_number_result[0]
        # Extract the last 4 digits of the stored card number
        stored_card_number_last4 = stored_card_number[-4:]
        
        print(f"Stored Last 4 Digits: {stored_card_number_last4}")
        print(f"Provided Card Number: {provided_card_number}")
        
        # Check if the provided card number matches the stored card number's last 4 digits
        if stored_card_number_last4 != provided_card_number:
            return False, 'Card number does not match our records'
        
        return True, None

    finally:
        cursor.close()
        conn.close()



# Flask-Mail configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'cnproject73@gmail.com'  # Replace with your email
app.config['MAIL_PASSWORD'] = 'owpr jzyi xdak nuaq'  # Use an app-specific password if 2FA is enabled
app.config['MAIL_DEFAULT_SENDER'] = 'cnproject73@gmail.com'


mail = Mail(app)

@app.route('/pay', methods=['POST'])
def pay():
    data = request.get_json()
    user_id = data.get('user_id')
    amount = data.get('amount')
    token = data.get('token')
    recipient_name = data.get('recipient_name')
    provided_card_number = data.get('card_number')

    if not all([user_id, amount, token, recipient_name, provided_card_number]):
        return jsonify({'message': 'User ID, amount, token, recipient name, and card number are required'}), 400

    # Check card validity and handle database connection
    is_valid_card, error_message = check_card_number(user_id, provided_card_number)
    if not is_valid_card:
        return jsonify({'message': error_message}), 400

    conn = get_banking_db_connection()
    cursor = conn.cursor()
    
    try:
        # Fetch sender's details
        cursor.execute("SELECT account_number, username FROM app_users WHERE user_id = %s", (user_id,))
        sender_info = cursor.fetchone()
        


        if not sender_info:
            return jsonify({'message': 'User not found in app_users'}), 404

        sender_account_number, sender_name = sender_info

        cursor.execute("SELECT email FROM users WHERE account_number = %s", (sender_account_number,))
        sender_email = cursor.fetchone()[0]



        # Fetch sender's balance
        cursor.execute("SELECT balance FROM users WHERE account_number = %s", (sender_account_number,))
        sender_balance_result = cursor.fetchone()

        if not sender_balance_result:
            return jsonify({'message': 'Sender not found in users'}), 404

        sender_balance = sender_balance_result[0]
        amount_decimal = Decimal(amount)

        if sender_balance < amount_decimal:
            return jsonify({'message': 'Insufficient balance'}), 400

        # Fetch recipient's details
        cursor.execute("SELECT id, balance, email FROM users WHERE username = %s", (recipient_name,))
        recipient = cursor.fetchone()

        if not recipient:
            return jsonify({'message': 'Recipient not found'}), 404

        recipient_id, recipient_balance, recipient_email = recipient
        try:
            # Process payment using Stripe
            charge = stripe.Charge.create(
                amount=int(amount_decimal * 100),  # Convert to cents
                currency="usd",
                description=f"Payment from {sender_name} to {recipient_name}",
                source=token
            )

            if charge.status == 'succeeded':
                # Update balances in the database
                new_sender_balance = sender_balance - amount_decimal
                new_recipient_balance = recipient_balance + amount_decimal

                cursor.execute("UPDATE users SET balance = %s WHERE account_number = %s", (new_sender_balance, sender_account_number))
                cursor.execute("UPDATE users SET balance = %s WHERE id = %s", (new_recipient_balance, recipient_id))

                # Record the transaction
                cursor.execute(
                    """
                    INSERT INTO transactions (user_id, amount, status, recipient_name, sender_name)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (user_id, amount_decimal, charge.status, recipient_name, sender_name)
                )

                conn.commit()

                # Send emails
                with mail.connect() as email_conn:
                    sender_msg = Message(
                        subject="Payment Sent Successfully",
                        recipients=[sender_email],
                        body=f"Hi {sender_name},\n\nYou have successfully sent ${amount_decimal} to {recipient_name}.\n\nTransaction ID: {charge.id}\n\nThank you!"
                    )
                    recipient_msg = Message(
                        subject="Payment Received",
                        recipients=[recipient_email],
                        body=f"Hi {recipient_name},\n\nYou have received ${amount_decimal} from {sender_name}.\n\nThank you!"
                    )
                    try:
                        email_conn.send(sender_msg)
                        email_conn.send(recipient_msg)
                    except Exception as e:
                        # Log the email error
                        app.logger.error(f"Error sending email: {str(e)}")
                        return jsonify({'message': f"Payment successful, but email sending failed: {str(e)}"}), 500

                return jsonify({
                    'message': 'Payment successful',
                    'status': charge.status,
                    'transaction_id': charge.id
                }), 200

            else:
                return jsonify({'message': 'Payment failed'}), 400

        except stripe.error.CardError as e:
            conn.rollback()
            return jsonify({'message': f'Payment failed: {e.user_message}'}), 400

    except Exception as e:
        conn.rollback()
        # Log the error
        app.logger.error(f"Unexpected error: {str(e)}")
        return jsonify({'message': f'Payment failed: {str(e)}'}), 500

    finally:
        # Close cursor and connection in correct order
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@app.route('/transactions/<int:user_id>', methods=['GET'])
def get_transactions(user_id):
    conn = get_banking_db_connection()  # Use banking_app database
    cursor = conn.cursor()

    try:
        # Fetch username associated with the user_id from app_users
        cursor.execute("SELECT username FROM app_users WHERE user_id = %s", (user_id,))
        user_info = cursor.fetchone()

        if not user_info:
            return jsonify({'message': 'User not found'}), 404

        username = user_info[0]

        # Fetch all transactions where the user is either the sender or recipient
        cursor.execute(
            """
            SELECT sender_name, recipient_name, amount, status, transaction_date
            FROM transactions
            WHERE sender_name = %s OR recipient_name = %s
            """,
            (username, username)
        )
        transactions = cursor.fetchall()

        # Initialize totals
        total_sent = Decimal('0.0')
        total_received = Decimal('0.0')

        transaction_data = []
        for txn in transactions:
            sender_name, recipient_name, amount, status, transaction_date = txn
            transaction_data.append({
                'sender_name': sender_name,
                'recipient_name': recipient_name,
                'amount': str(amount),
                'status': status,
                'transaction_date': transaction_date.strftime('%Y-%m-%d %H:%M:%S')
            })

            # Update total sent and received
            if sender_name == username:
                total_sent += amount
            elif recipient_name == username:
                total_received += amount

        return jsonify({
            'transactions': transaction_data,
            'total_sent': str(total_sent),
            'total_received': str(total_received)
        }), 200

    finally:
        cursor.close()
        conn.close()

@app.route('/check-bank-account', methods=['POST'])
def check_bank_account():
    data = request.json
    bank_account_number = data.get('bank_account_number')
    bank_password = data.get('bank_password')

    if not bank_account_number or not bank_password:
        return jsonify({'message': 'Bank account number and password are required'}), 400

    try:
        conn = mysql.connector.connect(
            host="localhost",           # Database server host
            user="root",                # Datazbase user
            password="mathan@123",      # Database password
            database="banking_app"      # Database name
        )
        cursor = conn.cursor()

        # Query to find the bank account
        cursor.execute("SELECT password FROM users WHERE account_number = %s", (bank_account_number,))
        result = cursor.fetchone()

        if result:
            stored_password = result[0]
            # Check if the entered password matches the stored hashed password
            if (stored_password==bank_password):
                return jsonify({'message': 'Bank account verified'}), 200
            else:
                return jsonify({'message': 'Invalid password'}), 401
        else:
            return jsonify({'message': 'Bank account not found'}), 404

    except Error as e:
        print("Database connection or query error:", e)
        return jsonify({'message': 'An error occurred while checking the bank account'}), 500

    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()




if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

