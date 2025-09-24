"""
Authentication utilities for Marivor
NOTE: This file is deprecated and can be removed.

All authentication is now handled through:
- Face recognition system (face_register and face_login routes in app.py)
- Supabase user management (supabase_utils.py)

The old SMS/OTP authentication system has been replaced with face recognition.
"""

# This file is deprecated - all auth is now handled through Supabase and face recognition
# You can safely delete this file once you confirm no other parts of your app import from it