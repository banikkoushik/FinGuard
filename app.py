from flask import Flask, request, jsonify
from flask_cors import CORS
import jwt
import datetime
import bcrypt
import sqlite3
import uuid
import smtplib
import os
import atexit
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from functools import wraps
from threading import Lock, Thread
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

app.config['SECRET_KEY'] = 'your-secret-key-here'  # Change this in production
app.config['DATABASE'] = 'mavrick.db'

# Email configuration (update with your email service details)
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME', 'your-email@gmail.com')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD', 'your-app-password')

# Database lock to prevent concurrent access issues
db_lock = Lock()

# Database initialization with connection pooling
def get_db():
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    try:
        with db_lock:
            conn = get_db()
            c = conn.cursor()
            
            # Create users table
            c.execute('''CREATE TABLE IF NOT EXISTS users
                        (id TEXT PRIMARY KEY, 
                         name TEXT NOT NULL, 
                         email TEXT UNIQUE NOT NULL, 
                         password TEXT NOT NULL,
                         created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
            
            # Create password_reset_tokens table
            c.execute('''CREATE TABLE IF NOT EXISTS password_reset_tokens
                        (id INTEGER PRIMARY KEY AUTOINCREMENT,
                         email TEXT NOT NULL,
                         token TEXT NOT NULL,
                         expires_at TIMESTAMP NOT NULL,
                         used INTEGER DEFAULT 0)''')
            
            # Create sessions table for tracking active users
            c.execute('''CREATE TABLE IF NOT EXISTS sessions
                        (id INTEGER PRIMARY KEY AUTOINCREMENT,
                         user_id TEXT NOT NULL,
                         token TEXT NOT NULL,
                         created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                         expires_at TIMESTAMP NOT NULL,
                         FOREIGN KEY (user_id) REFERENCES users (id))''')
            
            conn.commit()
            conn.close()
            print("Database initialized successfully")
    except Exception as e:
        print(f"Error initializing database: {e}")

# Token required decorator
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if not token:
            return jsonify({'message': 'Token is missing'}), 401
            
        try:
            # Remove 'Bearer ' prefix if present
            if token.startswith('Bearer '):
                token = token[7:]
                
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            
            with db_lock:
                conn = get_db()
                c = conn.cursor()
                c.execute("SELECT * FROM users WHERE id=?", (data['user_id'],))
                current_user = c.fetchone()
                conn.close()
            
            if not current_user:
                return jsonify({'message': 'Invalid token'}), 401
                
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Invalid token'}), 401
            
        return f(current_user, *args, **kwargs)
        
    return decorated

# Helper function to generate JWT token
def generate_token(user_id):
    payload = {
        'user_id': user_id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    }
    return jwt.encode(payload, app.config['SECRET_KEY'], algorithm="HS256")

# Function to send email with OTP
def send_otp_email(email, otp):
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = app.config['MAIL_USERNAME']
        msg['To'] = email
        msg['Subject'] = 'Your Mavrick Verification Code'
        
        # Email body
        body = f"""
        <html>
        <body>
            <h2>Your Mavrick Verification Code</h2>
            <p>Hello there,</p>
            <p>Your verification code for Mavrick is:</p>
            <div style="background: #f8f9fa; padding: 15px; text-align: center; font-size: 28px; 
                        font-weight: bold; letter-spacing: 5px; color: #d62246; border-radius: 8px; 
                        margin: 15px 0; border: 1px dashed #e1e5eb;">
                {otp}
            </div>
            <p>Enter this code to complete your authentication process.</p>
            <p>This code will expire in 10 minutes.</p>
            <p>If you didn't request this code, please ignore this email.</p>
            <p>Thanks,<br/>The Mavrick Team</p>
            <div style="font-size: 12px; color: #7f8c8d; text-align: center; margin-top: 15px;">
                <i class="fas fa-shield-alt"></i> Protect your verification code. Never share it with anyone.
            </div>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(body, 'html'))
        
        # Send email
        server = smtplib.SMTP(app.config['MAIL_SERVER'], app.config['MAIL_PORT'])
        server.starttls()
        server.login(app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
        server.send_message(msg)
        server.quit()
        
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

# Clean up expired tokens (run this periodically)
def cleanup_expired_tokens():
    try:
        with db_lock:
            conn = get_db()
            c = conn.cursor()
            now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            c.execute("DELETE FROM password_reset_tokens WHERE expires_at < ?", (now,))
            c.execute("DELETE FROM sessions WHERE expires_at < ?", (now,))
            conn.commit()
            conn.close()
        print("Expired tokens cleaned up successfully")
    except Exception as e:
        print(f"Error cleaning up expired tokens: {e}")

# Routes
@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({'success': False, 'message': 'Email and password are required'}), 400
            
        with db_lock:
            conn = get_db()
            c = conn.cursor()
            c.execute("SELECT * FROM users WHERE email=?", (email,))
            user = c.fetchone()
            conn.close()
        
        if not user:
            return jsonify({'success': False, 'message': 'Invalid email or password'}), 401
            
        # Verify password
        if bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
            token = generate_token(user['id'])
            
            # Store session
            with db_lock:
                conn = get_db()
                c = conn.cursor()
                expires_at = (datetime.datetime.now() + datetime.timedelta(hours=24)).strftime('%Y-%m-%d %H:%M:%S')
                c.execute("INSERT INTO sessions (user_id, token, expires_at) VALUES (?, ?, ?)",
                         (user['id'], token, expires_at))
                conn.commit()
                conn.close()
            
            return jsonify({
                'success': True,
                'data': {
                    'user': {
                        'id': user['id'],
                        'name': user['name'],
                        'email': user['email']
                    },
                    'token': token
                }
            })
        else:
            return jsonify({'success': False, 'message': 'Invalid email or password'}), 401
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/signup', methods=['POST'])
def signup():
    try:
        data = request.get_json()
        name = data.get('name')
        email = data.get('email')
        password = data.get('password')
        
        if not name or not email or not password:
            return jsonify({'success': False, 'message': 'All fields are required'}), 400
            
        # Validate password strength
        if len(password) < 12:
            return jsonify({'success': False, 'message': 'Password must be at least 12 characters'}), 400
            
        # Check for uppercase, lowercase, number, and special character
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(not c.isalnum() for c in password)
        
        if not (has_upper and has_lower and has_digit and has_special):
            return jsonify({'success': False, 'message': 'Password does not meet complexity requirements'), 400
            
        # Check if user already exists
        with db_lock:
            conn = get_db()
            c = conn.cursor()
            c.execute("SELECT * FROM users WHERE email=?", (email,))
            existing_user = c.fetchone()
            
            if existing_user:
                conn.close()
                return jsonify({'success': False, 'message': 'User already exists with this email'}), 409
                
            # Hash password
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            # Create user
            user_id = str(uuid.uuid4())
            
            c.execute("INSERT INTO users (id, name, email, password) VALUES (?, ?, ?, ?)",
                     (user_id, name, email, hashed_password))
            
            conn.commit()
            conn.close()
        
        token = generate_token(user_id)
        
        # Store session
        with db_lock:
            conn = get_db()
            c = conn.cursor()
            expires_at = (datetime.datetime.now() + datetime.timedelta(hours=24)).strftime('%Y-%m-%d %H:%M:%S')
            c.execute("INSERT INTO sessions (user_id, token, expires_at) VALUES (?, ?, ?)",
                     (user_id, token, expires_at))
            conn.commit()
            conn.close()
        
        return jsonify({
            'success': True,
            'data': {
                'user': {
                    'id': user_id,
                    'name': name,
                    'email': email
                },
                'token': token
            }
        }), 201
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/auth/<provider>', methods=['POST'])
def social_login(provider):
    try:
        # In a real implementation, you would verify the social provider token here
        # For this example, we'll simulate the process
        
        # Generate a mock user based on the provider
        user_id = str(uuid.uuid4())
        name = f"{provider.capitalize()} User"
        email = f"user_{user_id[:8]}@{provider}.com"
        
        # Check if user already exists
        with db_lock:
            conn = get_db()
            c = conn.cursor()
            c.execute("SELECT * FROM users WHERE email=?", (email,))
            user = c.fetchone()
            
            if not user:
                # Create a new user for social login (no password)
                c.execute("INSERT INTO users (id, name, email, password) VALUES (?, ?, ?, ?)",
                         (user_id, name, email, ''))
                conn.commit()
            else:
                user_id = user['id']
                name = user['name']
                email = user['email']
            
            conn.close()
        
        token = generate_token(user_id)
        
        # Store session
        with db_lock:
            conn = get_db()
            c = conn.cursor()
            expires_at = (datetime.datetime.now() + datetime.timedelta(hours=24)).strftime('%Y-%m-%d %H:%M:%S')
            c.execute("INSERT INTO sessions (user_id, token, expires_at) VALUES (?, ?, ?)",
                     (user_id, token, expires_at))
            conn.commit()
            conn.close()
        
        return jsonify({
            'success': True,
            'data': {
                'user': {
                    'id': user_id,
                    'name': name,
                    'email': email
                },
                'token': token
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/forgot-password', methods=['POST'])
def forgot_password():
    try:
        data = request.get_json()
        email = data.get('email')
        
        if not email or '@' not in email:
            return jsonify({'success': False, 'message': 'Valid email is required'}), 400
            
        # Check if user exists
        with db_lock:
            conn = get_db()
            c = conn.cursor()
            c.execute("SELECT * FROM users WHERE email=?", (email,))
            user = c.fetchone()
            
            if not user:
                # For security reasons, don't reveal if the email exists or not
                conn.close()
                return jsonify({
                    'success': True,
                    'data': {
                        'message': 'If this email is registered, you will receive a verification code'
                    }
                })
            
            # Generate OTP
            otp = str(uuid.uuid4())[:6].upper()
            expires_at = (datetime.datetime.now() + datetime.timedelta(minutes=10)).strftime('%Y-%m-%d %H:%M:%S')
            
            # Store OTP in database
            c.execute("INSERT INTO password_reset_tokens (email, token, expires_at) VALUES (?, ?, ?)",
                     (email, otp, expires_at))
            
            conn.commit()
            conn.close()
        
        # Send OTP via email
        email_sent = send_otp_email(email, otp)
        
        if not email_sent:
            return jsonify({'success': False, 'message': 'Failed to send verification email'}), 500
        
        return jsonify({
            'success': True,
            'data': {
                'message': 'Verification code sent to your email',
                'expiresIn': 600
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/verify-otp', methods=['POST'])
def verify_otp():
    try:
        data = request.get_json()
        email = data.get('email')
        otp = data.get('otp')
        
        if not otp or len(otp) != 6:
            return jsonify({'success': False, 'message': 'Valid OTP is required'}), 400
            
        with db_lock:
            conn = get_db()
            c = conn.cursor()
            
            # Check if OTP is valid and not expired
            now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            c.execute("SELECT * FROM password_reset_tokens WHERE email=? AND token=? AND expires_at > ? AND used=0",
                     (email, otp, now))
            token_data = c.fetchone()
            
            if not token_data:
                conn.close()
                return jsonify({'success': False, 'message': 'Invalid or expired OTP'}), 400
                
            # Mark OTP as used
            c.execute("UPDATE password_reset_tokens SET used=1 WHERE id=?", (token_data['id'],))
            conn.commit()
            conn.close()
        
        # Generate a temporary token for password reset
        temp_token = jwt.encode(
            {'email': email, 'purpose': 'password_reset', 'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=15)},
            app.config['SECRET_KEY'],
            algorithm="HS256"
        )
        
        return jsonify({
            'success': True,
            'data': {
                'message': 'OTP verified successfully',
                'token': temp_token
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/reset-password', methods=['POST'])
def reset_password():
    try:
        data = request.get_json()
        token = data.get('token')
        new_password = data.get('newPassword')
        
        if not token:
            return jsonify({'success': False, 'message': 'Token is required'}), 400
            
        if not new_password or len(new_password) < 12:
            return jsonify({'success': False, 'message': 'New password must be at least 12 characters'}), 400
            
        # Verify token
        try:
            payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            
            if payload.get('purpose') != 'password_reset':
                return jsonify({'success': False, 'message': 'Invalid token'}), 400
                
            email = payload.get('email')
            
            if not email:
                return jsonify({'success': False, 'message': 'Invalid token'}), 400
                
        except jwt.ExpiredSignatureError:
            return jsonify({'success': False, 'message': 'Token has expired'}), 400
        except jwt.InvalidTokenError:
            return jsonify({'success': False, 'message': 'Invalid token'}), 400
            
        # Hash new password
        hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Update password
        with db_lock:
            conn = get_db()
            c = conn.cursor()
            c.execute("UPDATE users SET password=? WHERE email=?", (hashed_password, email))
            
            if c.rowcount == 0:
                conn.close()
                return jsonify({'success': False, 'message': 'User not found'}), 404
                
            conn.commit()
            conn.close()
        
        return jsonify({
            'success': True,
            'data': {
                'message': 'Password reset successfully'
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/user', methods=['GET'])
@token_required
def get_user(current_user):
    try:
        return jsonify({
            'success': True,
            'data': {
                'user': {
                    'id': current_user['id'],
                    'name': current_user['name'],
                    'email': current_user['email']
                }
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/logout', methods=['POST'])
@token_required
def logout(current_user):
    try:
        token = request.headers.get('Authorization')
        if token and token.startswith('Bearer '):
            token = token[7:]
            
            with db_lock:
                conn = get_db()
                c = conn.cursor()
                c.execute("DELETE FROM sessions WHERE token=?", (token,))
                conn.commit()
                conn.close()
        
        return jsonify({'success': True, 'message': 'Logged out successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# Health check endpoint
@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'timestamp': datetime.datetime.now().isoformat()})

# Initialize database and start cleanup scheduler
def initialize_app():
    init_db()
    
    # Schedule token cleanup to run every hour
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=cleanup_expired_tokens, trigger="interval", hours=1)
    scheduler.start()
    
    # Shut down the scheduler when exiting the app
    atexit.register(lambda: scheduler.shutdown())

# Initialize the application
initialize_app()

if __name__ == '__main__':
    app.run(debug=True, port=5000, threaded=True)