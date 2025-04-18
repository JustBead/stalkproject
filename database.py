import sqlite3

class Database:
    def __init__(self, db_name="bot_data.db"):
        self.connection = sqlite3.connect(db_name, check_same_thread=False)
        self.cursor = self.connection.cursor()
        self.create_tables()

    def create_tables(self):
        """Create necessary tables for the bot."""
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                free_quota INTEGER DEFAULT 1,
                premium_until INTEGER DEFAULT NULL,
                referral_code TEXT,
                referred_by TEXT
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS referrals (
                user_id INTEGER,
                referred_user_id INTEGER,
                PRIMARY KEY (user_id, referred_user_id)
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS queries (
                user_id INTEGER,
                instagram_username TEXT,
                fake_profiles TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.connection.commit()

    def add_user(self, user_id, username):
        """Add a new user to the database."""
        referral_code = f"REF{user_id}"
        self.cursor.execute("""
            INSERT OR IGNORE INTO users (user_id, username, referral_code)
            VALUES (?, ?, ?)
        """, (user_id, username, referral_code))
        self.connection.commit()

    def get_referral_code(self, user_id):
        """Get the referral code of a user."""
        self.cursor.execute("""
            SELECT referral_code FROM users WHERE user_id = ?
        """, (user_id,))
        result = self.cursor.fetchone()
        return result[0] if result else None

    def user_has_free_quota(self, user_id):
        """Check if the user still has a free quota."""
        self.cursor.execute("""
            SELECT free_quota FROM users WHERE user_id = ?
        """, (user_id,))
        result = self.cursor.fetchone()
        return result[0] > 0 if result else False

    def decrement_free_quota(self, user_id):
        """Decrement the free quota of the user."""
        self.cursor.execute("""
            UPDATE users SET free_quota = free_quota - 1 WHERE user_id = ?
        """, (user_id,))
        self.connection.commit()

    def save_query(self, user_id, instagram_username, fake_profiles):
        """Save a user's query along with generated fake profiles."""
        self.cursor.execute("""
            INSERT INTO queries (user_id, instagram_username, fake_profiles)
            VALUES (?, ?, ?)
        """, (user_id, instagram_username, ','.join(fake_profiles)))
        self.connection.commit()
