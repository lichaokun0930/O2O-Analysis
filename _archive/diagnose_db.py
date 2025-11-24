import socket
import sys
import time
from sqlalchemy import create_engine, text

def check_port(host, port):
    print(f"Checking {host}:{port}...", end="")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(2)
    result = sock.connect_ex((host, port))
    sock.close()
    if result == 0:
        print(" OPEN")
        return True
    else:
        print(" CLOSED")
        return False

def check_db_connection():
    print("Checking database connection...", end="")
    try:
        # 使用 pg8000，使用 .env 中的正确密码
        url = "postgresql+pg8000://postgres:308352588@localhost:5432/o2o_dashboard"
        engine = create_engine(url)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print(" SUCCESS")
            return True
    except Exception as e:
        print(f" FAILED: {e}")
        return False

if __name__ == "__main__":
    print("="*50)
    print("🔍 Database Diagnostic Tool")
    print("="*50)
    
    if check_port("localhost", 5432):
        if check_db_connection():
            print("\n✅ Database is ready.")
            sys.exit(0)
        else:
            print("\n❌ Port is open but connection failed. Service might be starting or authentication failed.")
            sys.exit(1)
    else:
        print("\n❌ PostgreSQL port 5432 is not accessible.")
        print("👉 Please start the PostgreSQL service.")
        sys.exit(1)
