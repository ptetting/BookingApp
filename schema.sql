DROP DATABASE IF EXISTS campus_room_booking;
CREATE DATABASE campus_room_booking;
USE campus_room_booking;

-- =========================================================
-- DATABASE SCHEMA FOR ROOM BOOKING SYSTEM
-- =========================================================

-- Drop tables if they already exist (for reset)
SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE IF EXISTS ActionLog, Notification, Booking, RoomRoomFeature, RoomAvailability, Facility, RoomFeature, Room, RoomType, Profile, User, Role;
SET FOREIGN_KEY_CHECKS = 1;

-- =========================================================
-- Roles and Users
-- =========================================================

CREATE TABLE Role (
    id INT AUTO_INCREMENT PRIMARY KEY,
    role_name VARCHAR(50) NOT NULL
);

CREATE TABLE User (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role_id INT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (role_id) REFERENCES Role(id) ON DELETE CASCADE
);

CREATE TABLE Profile (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT UNIQUE NOT NULL,
    phone_number VARCHAR(20),
    address VARCHAR(255),
    FOREIGN KEY (user_id) REFERENCES User(id) ON DELETE CASCADE
);

-- =========================================================
-- Room Tables
-- =========================================================

CREATE TABLE RoomType (
    id INT AUTO_INCREMENT PRIMARY KEY,
    room_type_name VARCHAR(50) NOT NULL,
    room_type_description TEXT
);

CREATE TABLE Room (
    id INT AUTO_INCREMENT PRIMARY KEY,
    room_number VARCHAR(10) NOT NULL UNIQUE,
    room_type_id INT NOT NULL,
    capacity INT UNSIGNED NOT NULL,
    FOREIGN KEY (room_type_id) REFERENCES RoomType(id) ON DELETE CASCADE
);

CREATE TABLE Facility (
    id INT AUTO_INCREMENT PRIMARY KEY,
    room_id INT NOT NULL,
    facility_name VARCHAR(100) NOT NULL,
    FOREIGN KEY (room_id) REFERENCES Room(id) ON DELETE CASCADE
);

CREATE TABLE RoomFeature (
    id INT AUTO_INCREMENT PRIMARY KEY,
    feature_name VARCHAR(100) NOT NULL,
    feature_description TEXT
);

CREATE TABLE RoomRoomFeature (
    id INT AUTO_INCREMENT PRIMARY KEY,
    room_id INT NOT NULL,
    feature_id INT NOT NULL,
    UNIQUE (room_id, feature_id),
    FOREIGN KEY (room_id) REFERENCES Room(id) ON DELETE CASCADE,
    FOREIGN KEY (feature_id) REFERENCES RoomFeature(id) ON DELETE CASCADE
);

-- =========================================================
-- Booking System
-- =========================================================

CREATE TABLE Booking (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    room_id INT NOT NULL,
    start_time DATETIME NOT NULL,
    end_time DATETIME NOT NULL,
    status ENUM('pending', 'approved', 'cancelled', 'completed') DEFAULT 'pending',
    FOREIGN KEY (user_id) REFERENCES User(id) ON DELETE CASCADE,
    FOREIGN KEY (room_id) REFERENCES Room(id) ON DELETE CASCADE
);

-- =========================================================
-- Notifications and Logs
-- =========================================================

CREATE TABLE Notification (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    booking_id INT NULL,
    notification_message TEXT NOT NULL,
    notification_status VARCHAR(20) DEFAULT 'unread',
    notification_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES User(id) ON DELETE CASCADE,
    FOREIGN KEY (booking_id) REFERENCES Booking(id) ON DELETE SET NULL
);

CREATE TABLE ActionLog (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    action VARCHAR(255) NOT NULL,
    action_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES User(id) ON DELETE CASCADE
);

CREATE TABLE RoomAvailability (
    id INT AUTO_INCREMENT PRIMARY KEY,
    room_id INT NOT NULL,
    day_of_week VARCHAR(10) NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    is_available BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (room_id) REFERENCES Room(id) ON DELETE CASCADE
);

-- =========================================================
-- Index for filtering by user and start time
-- =========================================================

CREATE INDEX idx_booking_user_start
ON Booking(user_id, start_time);

-- =========================================================
-- View for showing booking details
-- =========================================================

CREATE VIEW BookingSummary AS
SELECT 
    b.id AS booking_id,
    u.name AS user_name,
    r.room_number,
    rt.room_type_name,
    b.start_time,
    b.end_time,
    b.status
FROM Booking b
JOIN User u ON b.user_id = u.id
JOIN Room r ON b.room_id = r.id
JOIN RoomType rt ON r.room_type_id = rt.id;


-- =========================================================
-- Notification Procedure
-- =========================================================

DELIMITER $$

CREATE PROCEDURE create_notifications_for_booking(IN action VARCHAR(50), IN booking_id INT)
BEGIN
    DECLARE room_num VARCHAR(10);
    DECLARE user_name VARCHAR(100);

    SELECT r.room_number, u.name
    INTO room_num, user_name
    FROM Booking b
    JOIN Room r ON b.room_id = r.id
    JOIN User u ON b.user_id = u.id
    WHERE b.id = booking_id;

    -- Notify booking owner
    INSERT INTO Notification(user_id, booking_id, notification_message, notification_status)
    SELECT b.user_id, booking_id,
           CONCAT('Your booking for Room ', room_num, ' at ', b.start_time, ' was ', action),
           'unread'
    FROM Booking b WHERE b.id = booking_id;

    -- Notify admins
    INSERT INTO Notification(user_id, booking_id, notification_message, notification_status)
    SELECT u.id, booking_id,
           CONCAT('Booking for Room ', room_num, ' with user ', user_name, ' was ', action),
           'unread'
    FROM User u
    JOIN Role r ON u.role_id = r.id
    WHERE r.role_name = 'Admin';
END$$

DELIMITER ;

-- =========================================================
-- Audit Log Procedure
-- =========================================================

DELIMITER $$

CREATE PROCEDURE log_action(IN user_id INT, IN action_desc VARCHAR(255))
BEGIN
    INSERT INTO ActionLog(user_id, action) VALUES (user_id, action_desc);
END$$

DELIMITER ;

-- =========================================================
-- Update Booking Status Procedure
-- =========================================================

DELIMITER $$

CREATE PROCEDURE update_booking_status(IN booking_id INT, IN new_status VARCHAR(20))
BEGIN
    UPDATE Booking SET status = new_status WHERE id = booking_id;
    CALL create_notifications_for_booking(CONCAT('updated to ', new_status), booking_id);
END$$

DELIMITER ;

-- =========================================================
-- Triggers for Logging Notifications and Audit
-- =========================================================

DELIMITER $$

-- Log and notify when a booking is created
CREATE TRIGGER trg_booking_insert
AFTER INSERT ON Booking
FOR EACH ROW
BEGIN
    CALL log_action(NEW.user_id, CONCAT('Created booking #', NEW.id));
    CALL create_notifications_for_booking('created', NEW.id);
END$$

-- Log and notify when a booking is updated
CREATE TRIGGER trg_booking_update
AFTER UPDATE ON Booking
FOR EACH ROW
BEGIN
    IF NEW.status <> OLD.status THEN
        CALL log_action(NEW.user_id, CONCAT('Updated booking #', NEW.id, ' status to ', NEW.status));
        CALL create_notifications_for_booking(CONCAT('updated to ', NEW.status), NEW.id);
    END IF;
END$$

-- Log when a booking is deleted
CREATE TRIGGER trg_booking_delete
AFTER DELETE ON Booking
FOR EACH ROW
BEGIN
    CALL log_action(OLD.user_id, CONCAT('Deleted booking #', OLD.id));
END$$

-- Log when a room is deleted
CREATE TRIGGER trg_room_delete
AFTER DELETE ON Room
FOR EACH ROW
BEGIN
    CALL log_action(NULL, CONCAT('Deleted room ', OLD.room_number));
END$$

DELIMITER ;

-- =========================================================
-- Notify All Admins About Booking Procedure
-- =========================================================

DELIMITER $$

CREATE PROCEDURE notify_admins_for_booking(IN booking_id INT, IN action VARCHAR(50))
BEGIN
    DECLARE done INT DEFAULT FALSE;
    DECLARE admin_id INT;

    DECLARE cur CURSOR FOR
        SELECT u.id
        FROM User u
        JOIN Role r ON u.role_id = r.id
        WHERE r.role_name = 'Admin';

    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;

    OPEN cur;
    read_loop: LOOP
        FETCH cur INTO admin_id;
        IF done THEN
            LEAVE read_loop;
        END IF;

        INSERT INTO Notification(user_id, booking_id, notification_message, notification_status)
        VALUES (
            admin_id,
            booking_id,
            CONCAT('Booking #', booking_id, ' was ', action, ' by user.'),
            'unread'
        );
    END LOOP;
    CLOSE cur;
END$$

DELIMITER ;

-- =========================================================
-- Function to check room availability
-- =========================================================

DELIMITER $$

CREATE FUNCTION is_room_available(
    p_room_id INT,
    p_start DATETIME,
    p_end DATETIME
)
RETURNS BOOLEAN
DETERMINISTIC
BEGIN
    DECLARE overlap_count INT;

    -- Count overlapping bookings
    SELECT COUNT(*)
    INTO overlap_count
    FROM Booking
    WHERE room_id = p_room_id
      AND status IN ('pending','approved')
      AND (
          (p_start BETWEEN start_time AND end_time)
          OR (p_end BETWEEN start_time AND end_time)
          OR (start_time BETWEEN p_start AND p_end)
          OR (end_time BETWEEN p_start AND p_end)
      );

    IF overlap_count > 0 THEN
        RETURN FALSE; -- room is not available
    ELSE
        RETURN TRUE; -- room is available
    END IF;
END$$

DELIMITER ;