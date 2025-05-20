import oracledb

# Replace these with your actual Oracle database credentials
DB_USER = "c##scott"
DB_PASSWORD = "tiger"
DB_DSN = "localhost:1521/XE"  # Format: hostname:port/service_name


def get_connection():
    # First try using the default connection parameters
    try:
        return oracledb.connect(
            user=DB_USER,
            password=DB_PASSWORD,
            dsn=DB_DSN,
            config_dir=None  # This forces thin mode
        )
    except oracledb.OperationalError as e:
        if "DPY-6001" in str(e):
            # If the service name approach doesn't work, try using SID format
            try:
                sid_dsn = "localhost:1521:XE"  # Note colon instead of slash
                print(f"Trying alternative connection with SID: {sid_dsn}")
                return oracledb.connect(
                    user=DB_USER,
                    password=DB_PASSWORD,
                    dsn=sid_dsn,
                    config_dir=None
                )
            except Exception as e2:
                print(f"Alternative connection also failed: {e2}")
                # Try one more alternative - using Easy Connect Plus syntax
                try:
                    ezconnect = "localhost:1521/XE?retry_count=3&retry_delay=3"
                    print(f"Trying EZ Connect Plus: {ezconnect}")
                    return oracledb.connect(
                        user=DB_USER,
                        password=DB_PASSWORD,
                        dsn=ezconnect,
                        config_dir=None
                    )
                except Exception as e3:
                    print(f"All connection attempts failed: {e3}")
                    raise e  # Raise the original error
        else:
            raise

def init_db():
    """Initialize database tables if they don't exist"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Create STUDENTS table if not exists
    try:
        cursor.execute("""
        BEGIN
            EXECUTE IMMEDIATE 'CREATE TABLE STUDENTS (
                STUDENT_ID VARCHAR2(20) PRIMARY KEY,
                STUDENT_NAME VARCHAR2(100) NOT NULL,
                SOUND_LABEL VARCHAR2(50) UNIQUE
            )';
        EXCEPTION
            WHEN OTHERS THEN
                IF SQLCODE = -955 THEN NULL; ELSE RAISE; END IF;
        END;
        """)
    except Exception as e:
        print(f"Error creating STUDENTS table: {e}")
    
    # Create ATTENDANCE table if not exists
    try:
        cursor.execute("""
        BEGIN
            EXECUTE IMMEDIATE 'CREATE TABLE ATTENDANCE (
                ID NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                STUDENT_ID VARCHAR2(20) NOT NULL,
                ATTENDANCE_DATE DATE NOT NULL,
                PRESENT NUMBER(1) DEFAULT 0,
                CONSTRAINT FK_STUDENT FOREIGN KEY (STUDENT_ID) REFERENCES STUDENTS(STUDENT_ID),
                CONSTRAINT UQ_ATTENDANCE UNIQUE (STUDENT_ID, ATTENDANCE_DATE)
            )';
        EXCEPTION
            WHEN OTHERS THEN
                IF SQLCODE = -955 THEN NULL; ELSE RAISE; END IF;
        END;
        """)
    except Exception as e:
        print(f"Error creating ATTENDANCE table: {e}")
    
    conn.commit()
    cursor.close()
    conn.close()
    print("Database initialized successfully")

def test_connection():
    """Test if the database connection is working"""
    try:
        conn = get_connection()
        print("Connection successful!")
        print(f"Connected to: {conn.version}")
        conn.close()
        return True
    except Exception as e:
        print(f"Connection failed: {e}")
        return False

if __name__ == "__main__":
    if test_connection():
        init_db()
    else:
        print("Database connection test failed. Please check your connection settings.")