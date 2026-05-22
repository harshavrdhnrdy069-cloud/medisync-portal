from flask import Flask, render_template, request, redirect, flash
import mysql.connector

app = Flask(__name__, template_folder='.')
app.secret_key = "secret_medisync_key"

# DATABASE CONFIGURATION - Update 'password' to your MySQL password
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Hr078*',
    'database': 'medisync_db'
}

def get_db_connection():
    try:
        return mysql.connector.connect(**db_config)
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None

def get_ward_for_patient(age_str, ailment):
    try:
        age = int(age_str)
    except:
        age = 30
        
    ailment_lower = ailment.lower()
    
    if age < 12:
        return "Pediatrics"
    if any(k in ailment_lower for k in ["heart", "cardiac"]):
        return "Cardiology"
    if any(k in ailment_lower for k in ["brain", "stroke", "nerve"]):
        return "Neurology"
    if any(k in ailment_lower for k in ["bone", "fracture", "break", "leg", "arm"]):
        return "Orthopedics"
    if any(k in ailment_lower for k in ["cancer", "tumor"]):
        return "Oncology"
    if any(k in ailment_lower for k in ["ear", "nose", "throat", "ent"]):
        return "ENT"
    if any(k in ailment_lower for k in ["baby", "pregnant", "labor", "maternity"]):
        return "Maternity"
    if any(k in ailment_lower for k in ["mental", "depress", "anxiety", "stress"]):
        return "Psychiatry"
    if any(k in ailment_lower for k in ["critical", "severe", "coma"]):
        return "ICU"
    if any(k in ailment_lower for k in ["accident", "bleed", "trauma"]):
        return "Emergency"
        
    return "General Ward"

WARD_RATES = {
    'ICU': 500,
    'Emergency': 300,
    'Cardiology': 250, 'Neurology': 250, 'Oncology': 250,
    'Orthopedics': 150, 'Maternity': 150, 'Pediatrics': 150, 'Private': 150,
    'General Ward': 100, 'Isolation': 100, 'ENT': 150, 'Psychiatry': 150
}

@app.route('/')
def index():
    conn = get_db_connection()
    if not conn: return "Database Connection Failed"
    
    cursor = conn.cursor(dictionary=True)
    
    # Get all beds (kept for backward compatibility or simple logic if needed)
    cursor.execute("SELECT * FROM beds")
    all_beds = cursor.fetchall()
    
    # Get aggregated bed statistics
    cursor.execute("""
        SELECT ward_type, 
               COUNT(*) as total, 
               SUM(CASE WHEN status = 'Available' THEN 1 ELSE 0 END) as available,
               SUM(CASE WHEN status = 'Occupied' THEN 1 ELSE 0 END) as occupied
        FROM beds
        GROUP BY ward_type
    """)
    bed_stats = cursor.fetchall()
    
    # Get current patient-bed assignments
    cursor.execute("""
        SELECT p.patient_id, p.name, p.age, p.ailment, p.bed_id, 
               b.ward_type, b.floor_number, b.room_number, b.bed_number,
               DATE_FORMAT(p.admitted_at, '%Y-%m-%d %H:%i') as admitted_at
        FROM patients p 
        JOIN beds b ON p.bed_id = b.bed_id
        WHERE p.status = 'Admitted'
        ORDER BY p.admitted_at DESC
    """)
    admissions = cursor.fetchall()
    
    # Get discharged patient history
    cursor.execute("""
        SELECT p.patient_id, p.name, p.age, p.ailment, p.bed_id, p.total_bill,
               b.ward_type, b.floor_number, b.room_number, b.bed_number,
               DATE_FORMAT(p.admitted_at, '%Y-%m-%d %H:%i') as admitted_at,
               DATE_FORMAT(p.discharged_at, '%Y-%m-%d %H:%i') as discharged_at
        FROM patients p 
        JOIN beds b ON p.bed_id = b.bed_id
        WHERE p.status = 'Discharged'
        ORDER BY p.discharged_at DESC
    """)
    history = cursor.fetchall()
    
    cursor.close()
    conn.close()
    return render_template('index.html', beds=all_beds, bed_stats=bed_stats, admissions=admissions, history=history)

@app.route('/admit', methods=['POST'])
def admit_patient():
    name = request.form.get('name')
    age = request.form.get('age')
    ailment = request.form.get('ailment')
    
    # Smart Assignment Logic
    ward_type = get_ward_for_patient(age, ailment)

    conn = get_db_connection()
    if not conn:
        return "Database Connection Failed"
        
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Find a RANDOM available bed in the requested ward
        cursor.execute("SELECT bed_id, floor_number, room_number, bed_number FROM beds WHERE ward_type = %s AND status = 'Available' ORDER BY RAND() LIMIT 1", (ward_type,))
        available_bed = cursor.fetchone()
        
        if not available_bed:
            flash(f"No available beds in {ward_type}!", "danger")
            return redirect('/')
            
        bed_id = available_bed['bed_id']
        floor_num = available_bed['floor_number']
        room_num = available_bed['room_number']
        bed_num = available_bed['bed_number']

        # Insert patient record
        sql = "INSERT INTO patients (name, age, ailment, bed_id) VALUES (%s, %s, %s, %s)"
        cursor.execute(sql, (name, age, ailment, bed_id))
        conn.commit()
        
        floor_text = "Ground Floor" if floor_num == 0 else f"Floor {floor_num}"
        flash(f"Patient admitted successfully! Assigned to {floor_text}, Room {room_num}, Bed #{bed_num}.", "success")
    except Exception as e:
        print(f"Insertion Error: {e}")
        flash("Error admitting patient.", "danger")
    finally:
        cursor.close()
        conn.close()
        
    return redirect('/')

@app.route('/shift_to_general/<int:patient_id>/<int:current_bed_id>', methods=['POST'])
def shift_to_general(patient_id, current_bed_id):
    conn = get_db_connection()
    if not conn:
        return "Database Connection Failed"
        
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Find a RANDOM available bed in the General Ward
        cursor.execute("SELECT bed_id, floor_number, room_number, bed_number FROM beds WHERE ward_type = 'General Ward' AND status = 'Available' ORDER BY RAND() LIMIT 1")
        available_bed = cursor.fetchone()
        
        if not available_bed:
            flash("No available beds in General Ward!", "danger")
            return redirect('/')
            
        new_bed_id = available_bed['bed_id']
        floor_num = available_bed['floor_number']
        room_num = available_bed['room_number']
        bed_num = available_bed['bed_number']

        # Free the old bed
        cursor.execute("UPDATE beds SET status = 'Available' WHERE bed_id = %s", (current_bed_id,))
        
        # Occupy the new bed
        cursor.execute("UPDATE beds SET status = 'Occupied' WHERE bed_id = %s", (new_bed_id,))
        
        # Update patient record
        cursor.execute("UPDATE patients SET bed_id = %s WHERE patient_id = %s", (new_bed_id, patient_id))
        
        conn.commit()
        
        floor_text = "Ground Floor" if floor_num == 0 else f"Floor {floor_num}"
        flash(f"Patient shifted to General Ward successfully! Assigned to {floor_text}, Room {room_num}, Bed #{bed_num}.", "success")
    except Exception as e:
        print(f"Shift Error: {e}")
        flash("Error shifting patient to General Ward.", "danger")
    finally:
        cursor.close()
        conn.close()
        
    return redirect('/')

@app.route('/discharge/<int:patient_id>/<int:bed_id>', methods=['POST'])
def discharge_patient(patient_id, bed_id):
    conn = get_db_connection()
    if not conn:
        return "Database Connection Failed"
        
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Calculate bill
        cursor.execute("SELECT b.ward_type, TIMESTAMPDIFF(HOUR, p.admitted_at, CURRENT_TIMESTAMP) as hours FROM patients p JOIN beds b ON p.bed_id = b.bed_id WHERE p.patient_id = %s", (patient_id,))
        pt_info = cursor.fetchone()
        
        if pt_info:
            hours = max(1, pt_info['hours']) # Minimum 1 hour charge
            rate = WARD_RATES.get(pt_info['ward_type'], 100)
            total_bill = hours * rate
        else:
            total_bill = 0

        # Mark the patient as discharged
        cursor.execute("UPDATE patients SET status = 'Discharged', discharged_at = CURRENT_TIMESTAMP, total_bill = %s WHERE patient_id = %s", (total_bill, patient_id))
        
        # Mark the bed as available
        cursor.execute("UPDATE beds SET status = 'Available' WHERE bed_id = %s", (bed_id,))
        
        conn.commit()
        flash("Patient discharged and bed is now available.", "success")
    except Exception as e:
        print(f"Discharge Error: {e}")
        flash("Error discharging patient.", "danger")
    finally:
        cursor.close()
        conn.close()
        
    return redirect('/')

@app.route('/receipt/<int:patient_id>')
def receipt(patient_id):
    conn = get_db_connection()
    if not conn:
        return "Database Connection Failed"
        
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT p.*, b.ward_type, b.floor_number, b.room_number, b.bed_number,
               DATE_FORMAT(p.admitted_at, '%b %d, %Y %H:%i') as admitted_fmt,
               DATE_FORMAT(p.discharged_at, '%b %d, %Y %H:%i') as discharged_fmt,
               TIMESTAMPDIFF(HOUR, p.admitted_at, p.discharged_at) as hours
        FROM patients p 
        JOIN beds b ON p.bed_id = b.bed_id
        WHERE p.patient_id = %s AND p.status = 'Discharged'
    """, (patient_id,))
    patient = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if not patient:
        return "Patient not found or not yet discharged.", 404
        
    patient['hours'] = max(1, patient['hours'])
    patient['rate'] = WARD_RATES.get(patient['ward_type'], 100)
    
    return render_template('receipt.html', patient=patient)

if __name__ == '__main__':
    app.run(debug=True, port=5000)