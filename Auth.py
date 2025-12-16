# auth
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from flask import session, redirect, url_for
from db import get_db
import  sqlite3, uuid

class User:
    """User model with authentication support."""

    def __init__(self, id=None, username=None, email=None, oauth_provider=None, oauth_id=None):
        self.id = id
        self.username = username
        self.email = email
        self.oauth_provider = oauth_provider
        self.oauth_id = oauth_id

    @staticmethod
    def create_local(db, username, email, password):
        """Create a new local user with hashed password."""
        try:
            hashed_pwd = generate_password_hash(password)
            cursor = db.cursor()
            cursor.execute(
                "INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
                (username, email, hashed_pwd)
            )
            db.commit()
            return User(id=cursor.lastrowid, username=username, email=email)
        except sqlite3.IntegrityError:
            return None  # User already exists

    @staticmethod
    def create_oauth(db, oauth_provider, oauth_id, username, email):
        """Create or get OAuth user."""
        cursor = db.cursor()
        # Check if OAuth user exists
        cursor.execute("SELECT id, username, email FROM users WHERE oauth_provider=? AND oauth_id=?",
                       (oauth_provider, oauth_id))
        row = cursor.fetchone()
        if row:
            return User(id=row[0], username=row[1], email=row[2], oauth_provider=oauth_provider, oauth_id=oauth_id)

        # Create new OAuth user
        try:
            cursor.execute(
                "INSERT INTO users (username, email, oauth_provider, oauth_id) VALUES (?, ?, ?, ?)",
                (username, email, oauth_provider, oauth_id)
            )
            db.commit()
            return User(id=cursor.lastrowid, username=username, email=email, oauth_provider=oauth_provider,
                        oauth_id=oauth_id)
        except sqlite3.IntegrityError:
            # Username or email conflict; use a unique variant
            unique_username = f"{oauth_provider}_{uuid.uuid4().hex[:8]}"
            cursor.execute(
                "INSERT INTO users (username, email, oauth_provider, oauth_id) VALUES (?, ?, ?, ?)",
                (unique_username, email, oauth_provider, oauth_id)
            )
            db.commit()
            return User(id=cursor.lastrowid, username=unique_username, email=email, oauth_provider=oauth_provider,
                        oauth_id=oauth_id)

    @staticmethod
    def authenticate(db, username, password):
        """Authenticate user by username and password."""
        cursor = db.cursor()
        cursor.execute("SELECT id, username, email, password FROM users WHERE username=?", (username,))
        row = cursor.fetchone()
        if row and row[3]:  # Check if password exists
            if check_password_hash(row[3], password):
                return User(id=row[0], username=row[1], email=row[2])
        return None

    @staticmethod
    def get_by_id(db, user_id):
        """Fetch user by ID."""
        cursor = db.cursor()
        cursor.execute("SELECT id, username, email, oauth_provider, oauth_id FROM users WHERE id=?", (user_id,))
        row = cursor.fetchone()
        if row:
            return User(id=row[0], username=row[1], email=row[2], oauth_provider=row[3], oauth_id=row[4])
        return None


class AuthManager:
    """Manage user sessions and authentication."""

    @staticmethod
    def login_user(user):
        """Store user in session."""
        session['user_id'] = user.id
        session['username'] = user.username

    @staticmethod
    def logout_user():
        """Clear user session."""
        session.pop('user_id', None)
        session.pop('username', None)

    @staticmethod
    def get_current_user(db):
        """Get current logged-in user from session."""
        user_id = session.get('user_id')
        if user_id:
            return User.get_by_id(db, user_id)
        return None

    @staticmethod
    def is_authenticated():
        """Check if user is logged in."""
        return 'user_id' in session


def login_required(f):
    """Decorator to require login."""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not AuthManager.is_authenticated():
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)

    return decorated_function


def get_current_user_context():
    """Get current user for template context."""
    db = get_db()
    user = AuthManager.get_current_user(db)
    return user
