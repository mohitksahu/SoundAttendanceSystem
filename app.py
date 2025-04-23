from flask import Flask, render_template, request, jsonify
import oracledb
from flask_cors import CORS
import os
import json
import traceback
from datetime import datetime
from database.db_config import get_connection

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/reports')
def reports():
    return render_template('reports.html')

@app.route('/mark_attendance', methods=['POST'])
def mark_attendance():
    data = request.json
    student_identifier = data.get('student_id')  # This could now be a name, sound label, or ID
    present = data.get('present', True)
    
    print(f"Received attendance request for student: {student_identifier}, present: {present}")
    
    if not student_identifier:
        return jsonify({"success": False, "error": "Student identifier is required"}), 400
    
    try:
        # Connect to database
        try:
            conn = get_connection()
            print("Database connection successful")
        except Exception as e:
            error_msg = f"Database connection error: {str(e)}"
            print(error_msg)
            print(traceback.format_exc())
            return jsonify({"success": False, "error": error_msg}), 500
        
        cursor = conn.cursor()
        
        # Get current date
        today = datetime.now().strftime('%Y-%m-%d')
        print(f"Marking attendance for date: {today}")
        
        # First check if student exists - now checking by name, ID, or sound label
        try:
            print(f"Looking up student by ID, name, or sound label: {student_identifier}")
            cursor.execute(
                """
                SELECT STUDENT_ID, STUDENT_NAME 
                FROM STUDENTS 
                WHERE STUDENT_ID = :1 
                   OR UPPER(STUDENT_NAME) = UPPER(:2) 
                   OR UPPER(SOUND_LABEL) = UPPER(:3)
                """,
                [student_identifier, student_identifier, student_identifier]
            )
            student_record = cursor.fetchone()
            
            if not student_record:
                error_msg = f"Student not found with identifier: {student_identifier}"
                print(error_msg)
                
                # Let's add this student automatically
                print(f"Adding new student with name: {student_identifier}")
                try:
                    # Generate a student ID
                    cursor.execute("SELECT COUNT(*) FROM STUDENTS")
                    count = cursor.fetchone()[0]
                    new_student_id = f"S{count+1:03d}"
                    
                    # Insert the new student
                    cursor.execute(
                        "INSERT INTO STUDENTS (STUDENT_ID, STUDENT_NAME, SOUND_LABEL) VALUES (:1, :2, :3)",
                        [new_student_id, student_identifier, student_identifier]
                    )
                    conn.commit()
                    print(f"Added new student with ID: {new_student_id}, Name: {student_identifier}")
                    
                    # Use this new student ID
                    actual_student_id = new_student_id
                    
                except Exception as e:
                    error_msg = f"Error adding new student: {str(e)}"
                    print(error_msg)
                    print(traceback.format_exc())
                    return jsonify({"success": False, "error": error_msg}), 500
            else:
                actual_student_id = student_record[0]
                print(f"Found student with ID: {actual_student_id}, Name: {student_record[1]}")
            
        except Exception as e:
            error_msg = f"Error checking student: {str(e)}"
            print(error_msg)
            print(traceback.format_exc())
            return jsonify({"success": False, "error": error_msg}), 500
        
        # Check if attendance already marked for today
        try:
            print(f"Checking if attendance already exists for today")
            cursor.execute(
                "SELECT * FROM ATTENDANCE WHERE STUDENT_ID = :1 AND ATTENDANCE_DATE = TO_DATE(:2, 'YYYY-MM-DD')",
                [actual_student_id, today]
            )
            
            existing = cursor.fetchone()
            
            if existing:
                # Update existing record
                print(f"Updating existing attendance record")
                cursor.execute(
                    "UPDATE ATTENDANCE SET PRESENT = :1 WHERE STUDENT_ID = :2 AND ATTENDANCE_DATE = TO_DATE(:3, 'YYYY-MM-DD')",
                    [1 if present else 0, actual_student_id, today]
                )
            else:
                # Insert new record
                print(f"Creating new attendance record")
                cursor.execute(
                    "INSERT INTO ATTENDANCE (STUDENT_ID, ATTENDANCE_DATE, PRESENT) VALUES (:1, TO_DATE(:2, 'YYYY-MM-DD'), :3)",
                    [actual_student_id, today, 1 if present else 0]
                )
            
            conn.commit()
            print("Attendance marked successfully")
            
        except Exception as e:
            error_msg = f"Error marking attendance: {str(e)}"
            print(error_msg)
            print(traceback.format_exc())
            return jsonify({"success": False, "error": error_msg}), 500
        
        finally:
            cursor.close()
            conn.close()
        
        return jsonify({"success": True, "message": "Attendance marked successfully"})
    
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        print(error_msg)
        print(traceback.format_exc())
        return jsonify({"success": False, "error": error_msg}), 500

@app.route('/get_attendance', methods=['GET'])
def get_attendance():
    date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    
    try:
        try:
            conn = get_connection()
            print(f"Database connection successful for get_attendance on date {date}")
        except Exception as e:
            error_msg = f"Database connection error: {str(e)}"
            print(error_msg)
            print(traceback.format_exc())
            return jsonify({"success": False, "error": error_msg}), 500
            
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                """
                SELECT s.STUDENT_ID, s.STUDENT_NAME, 
                       CASE WHEN a.PRESENT = 1 THEN 'Present' ELSE 'Absent' END as STATUS
                FROM STUDENTS s
                LEFT JOIN ATTENDANCE a ON s.STUDENT_ID = a.STUDENT_ID AND a.ATTENDANCE_DATE = TO_DATE(:date, 'YYYY-MM-DD')
                ORDER BY s.STUDENT_NAME
                """,
                [date]
            )
            
            columns = [col[0] for col in cursor.description]
            attendance_data = [dict(zip(columns, row)) for row in cursor.fetchall()]
            print(f"Retrieved {len(attendance_data)} attendance records")
            
        except Exception as e:
            error_msg = f"Error retrieving attendance data: {str(e)}"
            print(error_msg)
            print(traceback.format_exc())
            return jsonify({"success": False, "error": error_msg}), 500
        
        finally:
            cursor.close()
            conn.close()
        
        return jsonify({"success": True, "data": attendance_data})
    
    except Exception as e:
        error_msg = f"Unexpected error in get_attendance: {str(e)}"
        print(error_msg)
        print(traceback.format_exc())
        return jsonify({"success": False, "error": error_msg}), 500

@app.route('/get_students', methods=['GET'])
def get_students():
    try:
        try:
            conn = get_connection()
            print("Database connection successful for get_students")
        except Exception as e:
            error_msg = f"Database connection error: {str(e)}"
            print(error_msg)
            print(traceback.format_exc())
            return jsonify({"success": False, "error": error_msg}), 500
            
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT STUDENT_ID, STUDENT_NAME, SOUND_LABEL FROM STUDENTS ORDER BY STUDENT_NAME")
            
            columns = [col[0] for col in cursor.description]
            students = [dict(zip(columns, row)) for row in cursor.fetchall()]
            print(f"Retrieved {len(students)} students")
            
        except Exception as e:
            error_msg = f"Error retrieving students: {str(e)}"
            print(error_msg)
            print(traceback.format_exc())
            return jsonify({"success": False, "error": error_msg}), 500
        
        finally:
            cursor.close()
            conn.close()
        
        return jsonify({"success": True, "data": students})
    
    except Exception as e:
        error_msg = f"Unexpected error in get_students: {str(e)}"
        print(error_msg)
        print(traceback.format_exc())
        return jsonify({"success": False, "error": error_msg}), 500

@app.route('/test_db', methods=['GET'])
def test_db():
    """Simple route to test database connection"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Test query
        cursor.execute("SELECT COUNT(*) FROM STUDENTS")
        count = cursor.fetchone()[0]
        
        # Get table names
        cursor.execute("SELECT table_name FROM user_tables")
        tables = [row[0] for row in cursor.fetchall()]
        
        cursor.close()
        conn.close()
        
        return jsonify({
            "success": True, 
            "message": "Database connection successful",
            "student_count": count,
            "tables": tables
        })
    except Exception as e:
        error_msg = f"Database test error: {str(e)}"
        print(error_msg)
        print(traceback.format_exc())
        return jsonify({"success": False, "error": error_msg}), 500

if __name__ == '__main__':
    app.run(debug=True)