import os
import subprocess
import sys

def reset_postgres_password():
    """
    Reset PostgreSQL password using various methods
    """
    print("PostgreSQL Password Reset Tool")
    print("=" * 40)
    
    # Method 1: Try to connect and reset directly
    print("\n1. Attempting direct password reset...")
    try:
        # Try to reset password for postgres user
        new_password = input("Enter new password for postgres user: ")
        confirm_password = input("Confirm new password: ")
        
        if new_password != confirm_password:
            print("Passwords don't match!")
            return False
            
        # Try using psql with trust authentication
        cmd = f'psql -U postgres -c "ALTER USER postgres PASSWORD \'{new_password}\';"'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✓ Password reset successfully!")
            return True
        else:
            print(f"✗ Direct reset failed: {result.stderr}")
            
    except Exception as e:
        print(f"✗ Error during direct reset: {e}")
    
    # Method 2: Try with different connection methods
    print("\n2. Trying alternative connection methods...")
    
    connection_attempts = [
        'psql -U postgres -h 127.0.0.1 -p 5432 -d postgres',
        'psql -U postgres -h localhost -p 5432 -d postgres',
        'psql -U postgres -d postgres',
    ]
    
    for attempt in connection_attempts:
        try:
            print(f"Trying: {attempt}")
            result = subprocess.run(f'{attempt} -c "SELECT version();"', 
                                  shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✓ Connection successful!")
                new_password = input("Enter new password for postgres user: ")
                
                reset_cmd = f'{attempt} -c "ALTER USER postgres PASSWORD \'{new_password}\';"'
                reset_result = subprocess.run(reset_cmd, shell=True, capture_output=True, text=True)
                
                if reset_result.returncode == 0:
                    print("✓ Password reset successfully!")
                    return True
                else:
                    print(f"✗ Password reset failed: {reset_result.stderr}")
                    
        except Exception as e:
            print(f"✗ Connection attempt failed: {e}")
    
    # Method 3: Manual instructions
    print("\n3. Manual reset instructions:")
    print("If automated methods failed, try these manual steps:")
    print("")
    print("Option A - Reset using pg_ctl:")
    print("1. Stop PostgreSQL service")
    print("2. Start PostgreSQL in single-user mode:")
    print("   pg_ctl -D \"C:\\Program Files\\PostgreSQL\\17\\data\" -o \"-c listen_addresses=''\" start")
    print("3. Connect and reset password")
    print("4. Restart PostgreSQL normally")
    print("")
    print("Option B - Edit pg_hba.conf:")
    print("1. Edit: C:\\Program Files\\PostgreSQL\\17\\data\\pg_hba.conf")
    print("2. Change authentication method to 'trust' for local connections")
    print("3. Restart PostgreSQL service")
    print("4. Connect and reset password")
    print("5. Restore original pg_hba.conf settings")
    print("")
    print("Option C - Use pgAdmin:")
    print("1. Open pgAdmin")
    print("2. Try to connect with saved credentials")
    print("3. Reset password through the interface")
    
    return False

if __name__ == "__main__":
    reset_postgres_password()
