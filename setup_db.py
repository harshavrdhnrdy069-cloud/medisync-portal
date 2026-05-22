import mysql.connector
import getpass
import random

def generate_hospital_sql():
    # Base tables and trigger
    sql_statements = [
        "DROP DATABASE IF EXISTS medisync_db;",
        "CREATE DATABASE medisync_db;",
        "USE medisync_db;",
        """
        CREATE TABLE IF NOT EXISTS beds (
            bed_id INT PRIMARY KEY AUTO_INCREMENT,
            ward_type VARCHAR(50),
            floor_number INT,
            room_number INT,
            bed_number INT,
            status ENUM('Available', 'Occupied') DEFAULT 'Available'
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS patients (
            patient_id INT PRIMARY KEY AUTO_INCREMENT,
            name VARCHAR(100),
            age INT,
            ailment VARCHAR(255),
            bed_id INT,
            admitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status ENUM('Admitted', 'Discharged') DEFAULT 'Admitted',
            discharged_at TIMESTAMP NULL,
            total_bill DECIMAL(10, 2) NULL,
            FOREIGN KEY (bed_id) REFERENCES beds(bed_id)
        );
        """,
        "DROP TRIGGER IF EXISTS after_patient_admission;",
        """
        CREATE TRIGGER after_patient_admission
        AFTER INSERT ON patients
        FOR EACH ROW
        UPDATE beds SET status = 'Occupied' WHERE bed_id = NEW.bed_id;
        """
    ]

    other_wards = [
        "Pediatrics", "Maternity", "Orthopedics", "Cardiology", 
        "Neurology", "Oncology", "Psychiatry", "ENT", 
        "Private", "Isolation"
    ]

    insert_values = []

    # Iterate through 10 floors (0 to 9)
    for floor in range(10):
        # Room 1, 2, 3: General Ward (4, 3, 3 beds to make exactly 10)
        general_ward_beds = [4, 3, 3]
        for idx, num_beds in enumerate(general_ward_beds):
            room = idx + 1
            for b in range(1, num_beds + 1):
                insert_values.append(f"('General Ward', {floor}, {room}, {b})")

        # Rooms 4 to 10 depending on floor
        for room in range(4, 11):
            if floor == 0 and room in [4, 5, 6]:
                # Emergency Ward on Ground Floor (Rooms 4, 5, 6)
                num_beds = random.randint(2, 5)
                for b in range(1, num_beds + 1):
                    insert_values.append(f"('Emergency', {floor}, {room}, {b})")
            elif 1 <= floor <= 5 and room == 4:
                # ICU on Floors 1-5 (Room 4 exactly)
                for b in range(1, 4):  # Exactly 3 beds
                    insert_values.append(f"('ICU', {floor}, {room}, {b})")
            else:
                # Other Wards for remaining rooms
                ward = random.choice(other_wards)
                num_beds = random.randint(2, 5)
                for b in range(1, num_beds + 1):
                    insert_values.append(f"('{ward}', {floor}, {room}, {b})")

    # Chunk the inserts to avoid massive single queries
    chunk_size = 50
    for i in range(0, len(insert_values), chunk_size):
        chunk = insert_values[i:i + chunk_size]
        val_str = ",\n            ".join(chunk)
        sql_statements.append(f"INSERT INTO beds (ward_type, floor_number, room_number, bed_number) VALUES \n            {val_str};")
        
    return sql_statements

def setup_database():
    print("=== MediSync Database Setup ===")
    print("Please enter your MySQL root password (it will be hidden as you type).")
    print("If you haven't set a password, just press Enter.")
    
    password = getpass.getpass("MySQL Password: ")
    
    try:
        print("Connecting to MySQL server...")
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password=password
        )
        cursor = conn.cursor()
        print("Connection successful!")
        
        commands = generate_hospital_sql()
        
        print("Generating and executing complex hospital layout...")
        for cmd in commands:
            cursor.execute(cmd)
            
        conn.commit()
        print("Database 'medisync_db' and hundreds of layout-specific beds created successfully!")
        
    except mysql.connector.Error as err:
        print(f"\n[ERROR] MySQL Error: {err}")
    finally:
        if 'cursor' in locals() and cursor is not None:
            cursor.close()
        if 'conn' in locals() and conn.is_connected():
            conn.close()

if __name__ == "__main__":
    setup_database()
