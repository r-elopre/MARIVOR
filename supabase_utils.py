"""
Supabase database utilities for Marivor
Handles database operations and file storage with Supabase
"""

import os
from typing import Optional, Dict, List, Any
from supabase import create_client, Client
from dotenv import load_dotenv
import base64
import uuid
from datetime import datetime

# Load environment variables
load_dotenv()

class SupabaseClient:
    """Wrapper class for Supabase operations"""
    
    def __init__(self):
        self.url = os.getenv('SUPABASE_URL')
        self.key = os.getenv('SUPABASE_KEY')
        self.service_key = os.getenv('SUPABASE_SERVICE_KEY')  # Service role key for storage
        self.bucket_name = os.getenv('SUPABASE_STORAGE_BUCKET', 'faces')
        
        if not self.url or not self.key:
            raise ValueError("Supabase URL and Key must be set in environment variables")
        
        # Use service key for storage operations if available, otherwise use anon key
        storage_key = self.service_key if self.service_key else self.key
        self.client: Client = create_client(self.url, self.key)
        self.storage_client: Client = create_client(self.url, storage_key)  # Separate client for storage
    
    # User Management Methods
    def create_user(self, username: str, phone_number: str, face_login_code: str, 
                   auth_type: str = 'face') -> Dict[str, Any]:
        """Create a new user in the database"""
        try:
            user_data = {
                'username': username,
                'phone_number': phone_number,
                'face_login_code': face_login_code,
                'auth_type': auth_type,
                'is_verified': True,
                'created_at': datetime.utcnow().isoformat()
            }
            
            response = self.client.table('users').insert(user_data).execute()
            return {'success': True, 'data': response.data[0] if response.data else None}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        try:
            response = self.client.table('users').select('*').eq('id', user_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Error getting user by ID: {e}")
            return None
    
    def get_user_by_face_code(self, face_code: str) -> Optional[Dict[str, Any]]:
        """Get user by face login code"""
        try:
            response = self.client.table('users').select('*').eq('face_login_code', face_code).eq('is_verified', True).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Error getting user by face code: {e}")
            return None
    
    def get_user_by_phone(self, phone_number: str) -> Optional[Dict[str, Any]]:
        """Get user by phone number"""
        try:
            response = self.client.table('users').select('*').eq('phone_number', phone_number).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Error getting user by phone: {e}")
            return None
    
    def update_user_photos(self, user_id: int, front_url: str, left_url: str, right_url: str) -> bool:
        """Update user's face photo URLs"""
        try:
            update_data = {
                'face_photo_front': front_url,
                'face_photo_left': left_url,
                'face_photo_right': right_url
            }
            
            response = self.client.table('users').update(update_data).eq('id', user_id).execute()
            return len(response.data) > 0
        except Exception as e:
            print(f"Error updating user photos: {e}")
            return False
    
    # Storage Methods
    def upload_face_photo(self, user_id: str, photo_data: str, direction: str) -> Optional[str]:
        """
        Upload face photo to Supabase storage
        
        Args:
            user_id: Unique user identifier
            photo_data: Base64 encoded image data
            direction: 'front', 'left', or 'right'
        
        Returns:
            Public URL of uploaded photo or None if failed
        """
        try:
            # Debug: Check photo_data type and content
            print(f"Uploading {direction} photo for user {user_id}")
            print(f"Photo data type: {type(photo_data)}")
            print(f"Photo data length: {len(photo_data) if isinstance(photo_data, str) else 'N/A'}")
            
            # Validate photo_data is a string
            if not isinstance(photo_data, str):
                print(f"Error: photo_data is not a string, it's {type(photo_data)}")
                return None
            
            if not photo_data or len(photo_data) < 100:  # Too short to be valid base64 image
                print(f"Error: photo_data is empty or too short: {len(photo_data) if photo_data else 0}")
                return None
            
            # Remove data URL prefix if present
            if ',' in photo_data:
                photo_data = photo_data.split(',')[1]
            
            # Decode base64 image
            image_bytes = base64.b64decode(photo_data)
            
            # Generate unique filename
            filename = f"{user_id}_{direction}_{int(datetime.utcnow().timestamp())}.jpg"
            file_path = f"users/{user_id}/{filename}"
            
            print(f"Uploading to path: {file_path}")
            
            # Upload to Supabase storage (with upsert to allow overwriting)
            try:
                response = self.storage_client.storage.from_(self.bucket_name).upload(
                    path=file_path,
                    file=image_bytes,
                    file_options={
                        "content-type": "image/jpeg",
                        "upsert": "true"  # String instead of boolean
                    }
                )
            except Exception as upload_error:
                # If upload fails due to existing file, try removing and re-uploading
                print(f"Upload failed, trying to remove existing file: {upload_error}")
                try:
                    self.storage_client.storage.from_(self.bucket_name).remove([file_path])
                    response = self.storage_client.storage.from_(self.bucket_name).upload(
                        path=file_path,
                        file=image_bytes,
                        file_options={
                            "content-type": "image/jpeg"
                        }
                    )
                except Exception as retry_error:
                    print(f"Retry upload also failed: {retry_error}")
                    raise upload_error
            
            print(f"Upload response: {response}")
            
            if response:
                # Get public URL
                public_url = self.storage_client.storage.from_(self.bucket_name).get_public_url(file_path)
                print(f"Generated public URL: {public_url}")
                return public_url
            else:
                print("Upload response was falsy")
                return None
            
        except Exception as e:
            print(f"Error uploading photo: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def get_photo_url(self, file_path: str) -> str:
        """Get public URL for a stored photo"""
        try:
            return self.client.storage.from_(self.bucket_name).get_public_url(file_path)
        except Exception as e:
            print(f"Error getting photo URL: {e}")
            return ""
    
    def delete_user_photos(self, user_id: str) -> bool:
        """Delete all photos for a user"""
        try:
            # List all files for the user
            response = self.client.storage.from_(self.bucket_name).list(f"users/{user_id}")
            
            if response:
                # Delete all files
                file_paths = [f"users/{user_id}/{file['name']}" for file in response]
                delete_response = self.client.storage.from_(self.bucket_name).remove(file_paths)
                return delete_response is not None
            
            return True
        except Exception as e:
            print(f"Error deleting user photos: {e}")
            return False

# Global Supabase client instance
supabase_client = None

def get_supabase_client() -> SupabaseClient:
    """Get or create Supabase client instance"""
    global supabase_client
    if supabase_client is None:
        supabase_client = SupabaseClient()
    return supabase_client

def test_connection() -> bool:
    """Test Supabase connection"""
    try:
        client = get_supabase_client()
        # Simple test query
        response = client.client.table('users').select('id').limit(1).execute()
        return True
    except Exception as e:
        print(f"Supabase connection test failed: {e}")
        return False