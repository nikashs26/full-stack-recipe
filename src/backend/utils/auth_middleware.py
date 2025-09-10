from auth import require_auth, get_user_id_from_request

# Re-export the auth functions for use in routes
__all__ = ['require_auth', 'get_user_id_from_request'] 