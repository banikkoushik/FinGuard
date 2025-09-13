const express = require('express');
const cors = require('cors');
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
const { body, validationResult } = require('express-validator');

const app = express();
const PORT = process.env.PORT || 3000;
const JWT_SECRET = process.env.JWT_SECRET || 'your-secret-key';

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.static('public'));

// In-memory storage (in a real app, use a database)
const users = [];
const passwordResetTokens = {};

// Helper function to generate JWT token
function generateToken(user) {
    return jwt.sign(
        { id: user.id, email: user.email },
        JWT_SECRET,
        { expiresIn: '24h' }
    );
}

// Routes

// Login endpoint
app.post('/api/login', [
    body('email').isEmail().normalizeEmail(),
    body('password').isLength({ min: 6 })
], async (req, res) => {
    try {
        // Check for validation errors
        const errors = validationResult(req);
        if (!errors.isEmpty()) {
            return res.status(400).json({
                success: false,
                message: 'Validation failed',
                errors: errors.array()
            });
        }

        const { email, password } = req.body;

        // Find user
        const user = users.find(u => u.email === email);
        if (!user) {
            return res.status(401).json({
                success: false,
                message: 'Invalid email or password'
            });
        }

        // Check password
        const isPasswordValid = await bcrypt.compare(password, user.password);
        if (!isPasswordValid) {
            return res.status(401).json({
                success: false,
                message: 'Invalid email or password'
            });
        }

        // Generate token
        const token = generateToken(user);

        res.json({
            success: true,
            data: {
                user: {
                    id: user.id,
                    name: user.name,
                    email: user.email,
                    avatar: user.name.charAt(0).toUpperCase()
                },
                token
            }
        });
    } catch (error) {
        console.error('Login error:', error);
        res.status(500).json({
            success: false,
            message: 'Internal server error'
        });
    }
});

// Signup endpoint
app.post('/api/signup', [
    body('name').isLength({ min: 2 }).trim().escape(),
    body('email').isEmail().normalizeEmail(),
    body('password').isLength({ min: 12 })
        .matches(/^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^a-zA-Z0-9]).{12,}$/)
], async (req, res) => {
    try {
        // Check for validation errors
        const errors = validationResult(req);
        if (!errors.isEmpty()) {
            return res.status(400).json({
                success: false,
                message: 'Validation failed',
                errors: errors.array()
            });
        }

        const { name, email, password } = req.body;

        // Check if user already exists
        const existingUser = users.find(u => u.email === email);
        if (existingUser) {
            return res.status(409).json({
                success: false,
                message: 'User already exists with this email'
            });
        }

        // Hash password
        const hashedPassword = await bcrypt.hash(password, 12);

        // Create user
        const user = {
            id: users.length + 1,
            name,
            email,
            password: hashedPassword,
            createdAt: new Date()
        };

        users.push(user);

        // Generate token
        const token = generateToken(user);

        res.status(201).json({
            success: true,
            data: {
                user: {
                    id: user.id,
                    name: user.name,
                    email: user.email,
                    avatar: user.name.charAt(0).toUpperCase()
                },
                token
            }
        });
    } catch (error) {
        console.error('Signup error:', error);
        res.status(500).json({
            success: false,
            message: 'Internal server error'
        });
    }
});

// Social login endpoints
app.post('/api/auth/google', async (req, res) => {
    try {
        // In a real app, you would verify the Google token here
        // For simulation purposes, we'll create a mock user
        
        const user = {
            id: users.length + 1,
            name: 'Google User',
            email: `user-${Date.now()}@google.com`,
            password: '', // No password for social login
            createdAt: new Date()
        };

        users.push(user);

        // Generate token
        const token = generateToken(user);

        res.json({
            success: true,
            data: {
                user: {
                    id: user.id,
                    name: user.name,
                    email: user.email,
                    avatar: user.name.charAt(0).toUpperCase()
                },
                token
            }
        });
    } catch (error) {
        console.error('Google auth error:', error);
        res.status(500).json({
            success: false,
            message: 'Internal server error'
        });
    }
});

app.post('/api/auth/apple', async (req, res) => {
    try {
        // In a real app, you would verify the Apple token here
        // For simulation purposes, we'll create a mock user
        
        const user = {
            id: users.length + 1,
            name: 'Apple User',
            email: `user-${Date.now()}@apple.com`,
            password: '', // No password for social login
            createdAt: new Date()
        };

        users.push(user);

        // Generate token
        const token = generateToken(user);

        res.json({
            success: true,
            data: {
                user: {
                    id: user.id,
                    name: user.name,
                    email: user.email,
                    avatar: user.name.charAt(0).toUpperCase()
                },
                token
            }
        });
    } catch (error) {
        console.error('Apple auth error:', error);
        res.status(500).json({
            success: false,
            message: 'Internal server error'
        });
    }
});

app.post('/api/auth/microsoft', async (req, res) => {
    try {
        // In a real app, you would verify the Microsoft token here
        // For simulation purposes, we'll create a mock user
        
        const user = {
            id: users.length + 1,
            name: 'Microsoft User',
            email: `user-${Date.now()}@microsoft.com`,
            password: '', // No password for social login
            createdAt: new Date()
        };

        users.push(user);

        // Generate token
        const token = generateToken(user);

        res.json({
            success: true,
            data: {
                user: {
                    id: user.id,
                    name: user.name,
                    email: user.email,
                    avatar: user.name.charAt(0).toUpperCase()
                },
                token
            }
        });
    } catch (error) {
        console.error('Microsoft auth error:', error);
        res.status(500).json({
            success: false,
            message: 'Internal server error'
        });
    }
});

// Forgot password endpoint
app.post('/api/forgot-password', [
    body('email').isEmail().normalizeEmail()
], async (req, res) => {
    try {
        // Check for validation errors
        const errors = validationResult(req);
        if (!errors.isEmpty()) {
            return res.status(400).json({
                success: false,
                message: 'Validation failed',
                errors: errors.array()
            });
        }

        const { email } = req.body;

        // Check if user exists
        const user = users.find(u => u.email === email);
        if (!user) {
            // For security reasons, we don't want to reveal if an email exists or not
            return res.json({
                success: true,
                data: {
                    message: 'If this email is registered, you will receive a verification code',
                    otp: Math.floor(100000 + Math.random() * 900000).toString(),
                    expiresIn: 600
                }
            });
        }

        // Generate OTP
        const otp = Math.floor(100000 + Math.random() * 900000).toString();
        
        // Store OTP with expiration (10 minutes)
        passwordResetTokens[email] = {
            otp,
            expiresAt: Date.now() + 600000 // 10 minutes
        };

        res.json({
            success: true,
            data: {
                message: 'Verification code sent to your email',
                otp,
                expiresIn: 600
            }
        });
    } catch (error) {
        console.error('Forgot password error:', error);
        res.status(500).json({
            success: false,
            message: 'Internal server error'
        });
    }
});

// Verify OTP endpoint
app.post('/api/verify-otp', [
    body('email').isEmail().normalizeEmail(),
    body('otp').isLength({ min: 6, max: 6 })
], async (req, res) => {
    try {
        // Check for validation errors
        const errors = validationResult(req);
        if (!errors.isEmpty()) {
            return res.status(400).json({
                success: false,
                message: 'Validation failed',
                errors: errors.array()
            });
        }

        const { email, otp } = req.body;

        // Check if OTP exists and is valid
        const storedOtp = passwordResetTokens[email];
        if (!storedOtp || storedOtp.otp !== otp) {
            return res.status(400).json({
                success: false,
                message: 'Invalid or expired verification code'
            });
        }

        // Check if OTP has expired
        if (Date.now() > storedOtp.expiresAt) {
            delete passwordResetTokens[email];
            return res.status(400).json({
                success: false,
                message: 'Verification code has expired'
            });
        }

        // Generate temporary token for password reset
        const tempToken = jwt.sign(
            { email, purpose: 'password_reset' },
            JWT_SECRET,
            { expiresIn: '15m' }
        );

        res.json({
            success: true,
            data: {
                message: 'OTP verified successfully',
                token: tempToken
            }
        });
    } catch (error) {
        console.error('Verify OTP error:', error);
        res.status(500).json({
            success: false,
            message: 'Internal server error'
        });
    }
});

// Reset password endpoint
app.post('/api/reset-password', [
    body('token').notEmpty(),
    body('newPassword').isLength({ min: 12 })
        .matches(/^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^a-zA-Z0-9]).{12,}$/)
], async (req, res) => {
    try {
        // Check for validation errors
        const errors = validationResult(req);
        if (!errors.isEmpty()) {
            return res.status(400).json({
                success: false,
                message: 'Validation failed',
                errors: errors.array()
            });
        }

        const { token, newPassword } = req.body;

        // Verify token
        let decoded;
        try {
            decoded = jwt.verify(token, JWT_SECRET);
        } catch (error) {
            return res.status(400).json({
                success: false,
                message: 'Invalid or expired token'
            });
        }

        // Check if token is for password reset
        if (decoded.purpose !== 'password_reset') {
            return res.status(400).json({
                success: false,
                message: 'Invalid token'
            });
        }

        // Find user
        const user = users.find(u => u.email === decoded.email);
        if (!user) {
            return res.status(404).json({
                success: false,
                message: 'User not found'
            });
        }

        // Hash new password
        user.password = await bcrypt.hash(newPassword, 12);

        // Remove used OTP
        delete passwordResetTokens[decoded.email];

        res.json({
            success: true,
            data: {
                message: 'Password reset successfully'
            }
        });
    } catch (error) {
        console.error('Reset password error:', error);
        res.status(500).json({
            success: false,
            message: 'Internal server error'
        });
    }
});

// Start server
app.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
});