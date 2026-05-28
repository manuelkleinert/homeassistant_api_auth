import sqlite3
import os
import logging
import secrets
import time
import bcrypt

_LOGGER = logging.getLogger(__name__)

class APIAuthStorage:
    """Handle SQLite storage for API Auth."""

    def __init__(self, config_dir):
        self.db_path = os.path.join(config_dir, "api_auth.db")
        self._init_db()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        """Initialize the database tables."""
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    role TEXT NOT NULL DEFAULT 'user'
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tokens (
                    token TEXT PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    expires INTEGER NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                )
            """)
            conn.commit()

    # --- User Management ---

    def add_user(self, username, password, role="user"):
        """Add a new user with hashed password."""
        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        try:
            with self._get_connection() as conn:
                conn.execute(
                    "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                    (username, hashed, role)
                )
                conn.commit()
                return True
        except sqlite3.IntegrityError:
            _LOGGER.error("User %s already exists", username)
            return False

    def delete_user(self, username):
        """Delete a user and their tokens."""
        with self._get_connection() as conn:
            conn.execute("DELETE FROM users WHERE username = ?", (username,))
            conn.commit()

    def update_password(self, username, new_password):
        """Update a user's password."""
        hashed = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
        with self._get_connection() as conn:
            conn.execute(
                "UPDATE users SET password = ? WHERE username = ?",
                (hashed, username)
            )
            conn.commit()

    def get_users(self):
        """Return a list of all usernames."""
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT username FROM users")
            return [row[0] for row in cursor.fetchall()]

    def get_user_by_name(self, username):
        """Return user data if found."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT id, username, password, role FROM users WHERE username = ?",
                (username,)
            )
            row = cursor.fetchone()
            if row:
                return {"id": row[0], "username": row[1], "password": row[2], "role": row[3]}
        return None

    def get_user_by_id(self, user_id):
        """Return user data by ID."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT id, username, role FROM users WHERE id = ?",
                (user_id,)
            )
            row = cursor.fetchone()
            if row:
                return {"id": row[0], "username": row[1], "role": row[2]}
        return None

    # --- Token Management ---

    def create_token(self, user_id, expires_in=604800):
        """Create a new session token."""
        token = secrets.token_hex(32)
        expires = int(time.time()) + expires_in
        with self._get_connection() as conn:
            conn.execute(
                "INSERT INTO tokens (token, user_id, expires) VALUES (?, ?, ?)",
                (token, user_id, expires)
            )
            conn.commit()
        return {"token": token, "expires": expires}

    def validate_token(self, token):
        """Check if a token is valid and not expired."""
        now = int(time.time())
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT user_id, expires FROM tokens WHERE token = ? AND expires > ?",
                (token, now)
            )
            return cursor.fetchone()

    def delete_token(self, token):
        """Delete a token (logout)."""
        with self._get_connection() as conn:
            conn.execute("DELETE FROM tokens WHERE token = ?", (token,))
            conn.commit()

    def cleanup_tokens(self):
        """Remove expired tokens."""
        now = int(time.time())
        with self._get_connection() as conn:
            conn.execute("DELETE FROM tokens WHERE expires <= ?", (now,))
            conn.commit()
