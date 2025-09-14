import sqlite3

def migrate_database():
    """Add missing columns to existing database"""
    conn = sqlite3.connect('db.sqlite')
    cursor = conn.cursor()
    
    try:
        # Check if title column exists in conversation table
        cursor.execute("PRAGMA table_info(conversation)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'title' not in columns:
            print("Adding title column to conversation table...")
            cursor.execute('ALTER TABLE conversation ADD COLUMN title TEXT DEFAULT "New Chat"')
            conn.commit()
            print("✓ Added title column")
        else:
            print("✓ Title column already exists")
            
    except sqlite3.Error as e:
        print(f"Error during migration: {e}")
    finally:
        conn.close()
    
    print("Database migration complete!")

if __name__ == "__main__":
    migrate_database()