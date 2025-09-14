import os
import shutil

def reset_database():
    """Reset the database and vector store"""
    
    # Remove SQLite database
    if os.path.exists("db.sqlite"):
        os.remove("db.sqlite")
        print("✓ Removed SQLite database")
    
    # Remove Chroma vector database
    if os.path.exists("chroma_db"):
        shutil.rmtree("chroma_db")
        print("✓ Removed Chroma vector database")
    
    # Remove uploads folder
    if os.path.exists("uploads"):
        shutil.rmtree("uploads")
        print("✓ Removed uploads folder")
    
    print("\n✓ Database reset complete!")
    print("You can now restart the server and register/login again.")

if __name__ == "__main__":
    reset_database()