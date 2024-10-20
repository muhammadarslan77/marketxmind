from werkzeug.security import generate_password_hash

def hash_password(password):
    return generate_password_hash(password)

# Additional functions for input validation (e.g., sanitize inputs, prevent XSS)
