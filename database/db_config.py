import oracledb

# Replace these with your actual Oracle database credentials
DB_USER = "c##scott"
DB_PASSWORD = "tiger"
DB_DSN = "localhost:1521/XE"  # Format: hostname:port/service_name

def get_connection():
    return oracledb.connect(
        user=DB_USER,
        password=DB_PASSWORD,
        dsn=DB_DSN,
        config_dir=None  # This forces thin mode
    )

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

if __name__ == "__main__":
    init_db()