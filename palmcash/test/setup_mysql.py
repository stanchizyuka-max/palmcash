#!/usr/bin/env python
"""
Script to create MySQL database for Palm Cash
Run this before running migrations
"""
import mysql.connector
from mysql.connector import Error

def create_database():
    """Create the Palm Cash database in MySQL"""
    try:
        # Connect to MySQL server (without specifying database)
        connection = mysql.connector.connect(
            host='localhost',
            port=3307,  # XAMPP MySQL uses port 3307
            user='root',
            password=''  # Default XAMPP password is empty
        )
        
        if connection.is_connected():
            cursor = connection.cursor()
            
            # Create database if it doesn't exist
            cursor.execute("CREATE DATABASE IF NOT EXISTS palmcash_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            print("✅ Database 'palmcash_db' created successfully (or already exists)")
            
            # Show databases to confirm
            cursor.execute("SHOW DATABASES")
            databases = cursor.fetchall()
            print("\n📋 Available databases:")
            for db in databases:
                print(f"   - {db[0]}")
            
            cursor.close()
            connection.close()
            print("\n✅ Setup complete! You can now run: python manage.py migrate")
            
    except Error as e:
        print(f"❌ Error connecting to MySQL: {e}")
        print("\n💡 Make sure:")
        print("   1. XAMPP is running")
        print("   2. MySQL service is started in XAMPP Control Panel")
        print("   3. MySQL is accessible on localhost:3307")

if __name__ == "__main__":
    print("🔧 Setting up MySQL database for Palm Cash...\n")
    create_database()
