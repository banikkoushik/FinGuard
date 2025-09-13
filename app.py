from flask import Flask, request, jsonify
from flask_cors import CORS
import jwt
import datetime
import bcrypt
import sqlite3
import uuid
from functools import wraps

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

app.config['SECRET_KEY'] = 'your-secret-key-here'  # Change this in production

# Database initialization
def init_db():
    conn = sqlite3.connect('mavrick.db')
    c = conn.cursor()
    
    # Create users table
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id TEXT PRIMARY KEY, 
                  name TEXT NOT NULL, 
                  email TEXT UNIQUE NOT NULL, 
                  password TEXT NOT NULL,
                  avatar TEXT,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    # Create password_reset_tokens table
    c.execute('''CREATE TABLE IF NOT EXISTS password_reset_tokens
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  email TEXT NOT NULL,
                  token TEXT NOT NULL,
                  expires_at TIMESTAMP NOT NULL,
                  used INTEGER DEFAULT 0)''')
    
    conn.commit()
    conn.close()

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
            conn = sqlite3.connect('mavrick.db')
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

# Routes
@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({'success': False, 'message': 'Email and password are required'}), 400
            
        conn = sqlite3.connect('mavrick.db')
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE email=?", (email,))
        user = c.fetchone()
        conn.close()
        
        if not user:
            return jsonify({'success': False, 'message': 'Invalid email or password'}), 401
            
        # Verify password
        if bcrypt.checkpw(password.encode('utf-8'), user[3].encode('utf-8')):
            token = generate_token(user[0])
            return jsonify({
                'success': True,
                'data': {
                    'user': {
                        'id': user[0],
                        'name': user[1],
                        'email': user[2],
                        'avatar': user[4] or user[1][0].upper()
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
            return jsonify({'success': False, 'message': 'Password does not meet complexity requirements'}), 400
            
        # Check if user already exists
        conn = sqlite3.connect('mavrick.db')
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
        avatar = name[0].upper()
        
        c.execute("INSERT INTO users (id, name, email, password, avatar) VALUES (?, ?, ?, ?, ?)",
                  (user_id, name, email, hashed_password, avatar))
        
        conn.commit()
        conn.close()
        
        token = generate_token(user_id)
        
        return jsonify({
            'success': True,
            'data': {
                'user': {
                    'id': user_id,
                    'name': name,
                    'email': email,
                    'avatar': avatar
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
        avatar = provider[0].upper()
        
        # Check if user already exists
        conn = sqlite3.connect('mavrick.db')
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE email=?", (email,))
        user = c.fetchone()
        
        if not user:
            # Create a new user for social login (no password)
            c.execute("INSERT INTO users (id, name, email, avatar) VALUES (?, ?, ?, ?)",
                      (user_id, name, email, avatar))
            conn.commit()
        else:
            user_id = user[0]
            name = user[1]
            email = user[2]
            avatar = user[4]
        
        conn.close()
        
        token = generate_token(user_id)
        
        return jsonify({
            'success': True,
            'data': {
                'user': {
                    'id': user_id,
                    'name': name,
                    'email': email,
                    'avatar': avatar
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
        conn = sqlite3.connect('mavrick.db')
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE email=?", (email,))
        user = c.fetchone()
        
        if not user:
            # For security reasons, don't reveal if the email exists or not
            conn.close()
            return jsonify({
                'success': True,
                'data': {
                    'message': 'If this email is registered, you will receive a verification code',
                    'otp': str(uuid.uuid4())[:6].upper()
                }
            })
        
        # Generate OTP
        otp = str(uuid.uuid4())[:6].upper()
        expires_at = datetime.datetime.utcnow() + datetime.timedelta(minutes=10)
        
        # Store OTP in database
        c.execute("INSERT INTO password_reset_tokens (email, token, expires_at) VALUES (?, ?, ?)",
                  (email, otp, expires_at))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'data': {
                'message': 'Verification code sent to your email',
                'otp': otp,
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
            
        conn = sqlite3.connect('mavrick.db')
        c = conn.cursor()
        
        # Check if OTP is valid and not expired
        c.execute("SELECT * FROM password_reset_tokens WHERE email=? AND token=? AND expires_at > datetime('now') AND used=0",
                  (email, otp))
        token_data = c.fetchone()
        
        if not token_data:
            conn.close()
            return jsonify({'success': False, 'message': 'Invalid or expired OTP'}), 400
            
        # Mark OTP as used
        c.execute("UPDATE password_reset_tokens SET used=1 WHERE id=?", (token_data[0],))
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
        conn = sqlite3.connect('mavrick.db')
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
                    'id': current_user[0],
                    'name': current_user[1],
                    'email': current_user[2],
                    'avatar': current_user[4]
                }
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)