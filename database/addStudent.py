import oracledb
from database.db_config import DB_USER, DB_PASSWORD, DB_DSN

def add_student(student_id, student_name, sound_label):
    """Add a student to the database"""
    try:
        connection = oracledb.connect(
            user=DB_USER,
            password=DB_PASSWORD,
            dsn=DB_DSN,
            config_dir=None
        )
        cursor = connection.cursor()
        
        cursor.execute(
            "INSERT INTO STUDENTS (STUDENT_ID, STUDENT_NAME, SOUND_LABEL) VALUES (:1, :2, :3)",
            [student_id, student_name, sound_label]
        )
        
        connection.commit()
        cursor.close()
        connection.close()
        print(f"Student {student_name} added successfully!")
        return True
    except Exception as e:
        print(f"Error adding student: {e}")
        return False

if __name__ == "__main__":
    # Add students here
    students = [
        {"id": "1001", "name": "Afaque", "sound_label": "Student1"},
        {"id": "1002", "name": "Amritansha", "sound_label": "Student2"},
        {"id": "1003", "name": "Rumeet", "sound_label": "Student3"}
        # Add more students as needed
    ]
    
    for student in students:
        add_student(student["id"], student["name"], student["sound_label"])