DROP DATABASE IF EXISTS campus_room_booking;
CREATE DATABASE campus_room_booking;

use campus_room_booking;

-- =========================================================
-- DATABASE SCHEMA FOR ROOM BOOKING SYSTEM
-- =========================================================

-- Drop tables if they already exist (for reset)
SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE IF EXISTS ActionLog, Notification, Booking, RoomRoomFeature, RoomAvailability, Facility, RoomFeature, Room, RoomType, Profile, User, Role, Product;
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
    email VARCHAR(254) NOT NULL UNIQUE,
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
-- Optional Product Table
-- =========================================================

CREATE TABLE Product (
    id INT AUTO_INCREMENT PRIMARY KEY,
    product_name VARCHAR(100) NOT NULL,
    product_description TEXT,
    product_price DECIMAL(8,2) NOT NULL
);

SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS booking_app_actionlog;
DROP TABLE IF EXISTS booking_app_notification;
DROP TABLE IF EXISTS booking_app_booking;
DROP TABLE IF EXISTS booking_app_facility;
DROP TABLE IF EXISTS booking_app_product;
DROP TABLE IF EXISTS booking_app_profile;
DROP TABLE IF EXISTS booking_app_user;
DROP TABLE IF EXISTS booking_app_role;
DROP TABLE IF EXISTS booking_app_roomavailability;
DROP TABLE IF EXISTS booking_app_roomroomfeature;
DROP TABLE IF EXISTS booking_app_room;
DROP TABLE IF EXISTS booking_app_roomfeature;
DROP TABLE IF EXISTS booking_app_roomtype;

SET FOREIGN_KEY_CHECKS = 1;