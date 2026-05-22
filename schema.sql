CREATE DATABASE IF NOT EXISTS medisync_db;
USE medisync_db;

-- 1. Table for Hospital Beds (with massive layout tracking)
CREATE TABLE IF NOT EXISTS beds (
    bed_id INT PRIMARY KEY AUTO_INCREMENT,
    ward_type VARCHAR(50),
    floor_number INT,
    room_number INT,
    bed_number INT,
    status ENUM('Available', 'Occupied') DEFAULT 'Available'
);

-- 2. Table for Patients
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

-- 3. TRIGGER: Automatically mark bed as Occupied when a patient is assigned
DELIMITER //
CREATE TRIGGER after_patient_admission
AFTER INSERT ON patients
FOR EACH ROW
BEGIN
    UPDATE beds SET status = 'Occupied' WHERE bed_id = NEW.bed_id;
END; //
DELIMITER ;

-- Note: Because this schema contains hundreds of beds, run `python setup_db.py` to seed the database instead of doing it manually here.