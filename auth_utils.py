"""
Authentication utilities for Marivor
Handles OTP generation, SMS sending, and user verification
"""

import os
import random
import hashlib
import sqlite3
from datetime import datetime, timedelta
from twilio.rest import Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Twilio configuration
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')

# OTP configuration
OTP_EXPIRY_MINUTES = int(os.getenv('OTP_EXPIRY_MINUTES', 5))
MAX_OTP_ATTEMPTS = int(os.getenv('MAX_OTP_ATTEMPTS', 3))
OTP_LENGTH = int(os.getenv('OTP_LENGTH', 6))

# Database configuration
DATABASE = os.getenv('DATABASE_URL', 'sqlite:///marivor.db').replace('sqlite:///', '')

class AuthService:
    def __init__(self):
        self.twilio_client = None
        if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN:
            self.twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

    def get_db_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row
        return conn

    def generate_otp(self):
        """Generate a random OTP code"""
        return ''.join([str(random.randint(0, 9)) for _ in range(OTP_LENGTH)])

    def hash_otp(self, otp_code):
        """Hash OTP code for secure storage"""
        return hashlib.sha256(otp_code.encode()).hexdigest()

    def format_phone_number(self, phone_number):
        """Format phone number to Philippine format (+63XXXXXXXXXX)"""
        # Remove any non-digit characters
        digits_only = ''.join(filter(str.isdigit, phone_number))
        
        # Handle different input formats
        if digits_only.startswith('63') and len(digits_only) == 12:
            # Already in +63 format (without +)
            return f"+{digits_only}"
        elif digits_only.startswith('0') and len(digits_only) == 11:
            # Format: 09171234567 -> +639171234567
            return f"+63{digits_only[1:]}"
        elif len(digits_only) == 10:
            # Format: 9171234567 -> +639171234567
            return f"+63{digits_only}"
        else:
            raise ValueError("Invalid phone number format")

    def send_sms_otp(self, phone_number, otp_code):
        """Send OTP code via SMS using Twilio"""
        if not self.twilio_client:
            raise Exception("Twilio client not configured")

        try:
            # Format phone number
            formatted_phone = self.format_phone_number(phone_number)
            
            # Create SMS message
            message_body = f"Your Marivor verification code is: {otp_code}\n\nThis code expires in {OTP_EXPIRY_MINUTES} minutes. Don't share this code with anyone."
            
            # Send SMS
            message = self.twilio_client.messages.create(
                body=message_body,
                from_=TWILIO_PHONE_NUMBER,
                to=formatted_phone
            )
            
            return {
                'success': True,
                'message_sid': message.sid,
                'formatted_phone': formatted_phone
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def store_otp(self, phone_number, otp_code):
        """Store OTP in database with expiration"""
        conn = self.get_db_connection()
        try:
            # Format phone number
            formatted_phone = self.format_phone_number(phone_number)
            
            # Hash the OTP
            otp_hash = self.hash_otp(otp_code)
            
            # Calculate expiration time
            expiry_time = datetime.now() + timedelta(minutes=OTP_EXPIRY_MINUTES)
            
            # Delete any existing OTPs for this phone number
            conn.execute(
                "DELETE FROM otp_codes WHERE phone_number = ?",
                (formatted_phone,)
            )
            
            # Insert new OTP
            conn.execute(
                """INSERT INTO otp_codes 
                   (phone_number, otp_code_hash, expires_at, attempts, is_used) 
                   VALUES (?, ?, ?, 0, 0)""",
                (formatted_phone, otp_hash, expiry_time)
            )
            
            conn.commit()
            return {'success': True, 'formatted_phone': formatted_phone}
            
        except Exception as e:
            conn.rollback()
            return {'success': False, 'error': str(e)}
        finally:
            conn.close()

    def verify_otp(self, phone_number, otp_code):
        """Verify OTP code against stored hash"""
        conn = self.get_db_connection()
        try:
            # Format phone number
            formatted_phone = self.format_phone_number(phone_number)
            
            # Get OTP record
            otp_record = conn.execute(
                """SELECT * FROM otp_codes 
                   WHERE phone_number = ? AND is_used = 0 
                   ORDER BY created_at DESC LIMIT 1""",
                (formatted_phone,)
            ).fetchone()
            
            if not otp_record:
                return {'success': False, 'error': 'No valid OTP found'}
            
            # Check if OTP is expired
            expiry_time = datetime.fromisoformat(otp_record['expires_at'])
            if datetime.now() > expiry_time:
                return {'success': False, 'error': 'OTP has expired'}
            
            # Check attempts
            if otp_record['attempts'] >= MAX_OTP_ATTEMPTS:
                return {'success': False, 'error': 'Maximum attempts exceeded'}
            
            # Verify OTP
            otp_hash = self.hash_otp(otp_code)
            if otp_hash == otp_record['otp_code_hash']:
                # Mark OTP as used
                conn.execute(
                    "UPDATE otp_codes SET is_used = 1 WHERE id = ?",
                    (otp_record['id'],)
                )
                conn.commit()
                return {'success': True, 'formatted_phone': formatted_phone}
            else:
                # Increment attempts
                new_attempts = otp_record['attempts'] + 1
                conn.execute(
                    "UPDATE otp_codes SET attempts = ? WHERE id = ?",
                    (new_attempts, otp_record['id'])
                )
                conn.commit()
                
                attempts_left = MAX_OTP_ATTEMPTS - new_attempts
                return {
                    'success': False, 
                    'error': 'Invalid OTP code',
                    'attempts_left': max(0, attempts_left)
                }
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
        finally:
            conn.close()

    def get_or_create_user(self, phone_number):
        """Get existing user or create new one"""
        conn = self.get_db_connection()
        try:
            # Format phone number
            formatted_phone = self.format_phone_number(phone_number)
            
            # Check if user exists
            user = conn.execute(
                "SELECT * FROM users WHERE phone_number = ?",
                (formatted_phone,)
            ).fetchone()
            
            if user:
                # Update last login
                conn.execute(
                    "UPDATE users SET last_login = ? WHERE id = ?",
                    (datetime.now(), user['id'])
                )
                conn.commit()
                return {'success': True, 'user': dict(user), 'is_new': False}
            else:
                # Create new user
                cursor = conn.execute(
                    """INSERT INTO users (phone_number, is_verified, created_at) 
                       VALUES (?, 1, ?)""",
                    (formatted_phone, datetime.now())
                )
                
                # Get the new user
                new_user = conn.execute(
                    "SELECT * FROM users WHERE id = ?",
                    (cursor.lastrowid,)
                ).fetchone()
                
                conn.commit()
                return {'success': True, 'user': dict(new_user), 'is_new': True}
                
        except Exception as e:
            conn.rollback()
            return {'success': False, 'error': str(e)}
        finally:
            conn.close()

    def cleanup_expired_otps(self):
        """Clean up expired OTP codes"""
        conn = self.get_db_connection()
        try:
            conn.execute(
                "DELETE FROM otp_codes WHERE expires_at < ?",
                (datetime.now(),)
            )
            conn.commit()
        except Exception as e:
            print(f"Error cleaning up expired OTPs: {e}")
        finally:
            conn.close()

# Create global auth service instance
auth_service = AuthService()