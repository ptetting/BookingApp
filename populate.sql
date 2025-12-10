use campus_room_booking;

-- 1. Insert default roles
INSERT INTO Role (id, role_name) VALUES
(1, 'Admin'),
(2, 'User');

-- 2. Insert an admin user
INSERT INTO User (name, email, password_hash, role_id, created_at)
VALUES
('Admin User', 'admin@example.com', 'admin123', 1, NOW());

-- 3. Insert sample users
INSERT INTO User (name, email, password_hash, role_id, created_at) VALUES
('Alice UserA', 'alice@uwm.edu', 'hash_alice', 2, NOW()),
('Bob UserB', 'bob@uwm.edu', 'hash_bob', 2, NOW()),
('Charlie UserC', 'charlie@uwm.edu', 'hash_charlie', 2, NOW()),
('Dana Admin', 'dana@uwm.edu', 'hash_dana', 1, NOW());

-- 4. Insert profile info
INSERT INTO Profile (user_id, phone_number, address) VALUES
(2, '555-1111', '123 Student Lane'),
(3, '555-2222', '456 Dorm Road'),
(4, '555-3333', '789 Faculty Ave'),
(5, '555-4444', '101 Admin Blvd');

-- 5. Insert room types
INSERT INTO RoomType (room_type_name, room_type_description) VALUES
('Library Study Room', 'Quiet study space in the library'),
('Lecture Hall', 'Large hall for lectures'),
('Computer Lab', 'Lab with PCs and equipment');

-- 6. Insert rooms
INSERT INTO Room (room_number, room_type_id, capacity) VALUES
('L101', 1, 4),
('L102', 1, 6),
('H201', 2, 100),
('C301', 3, 25);

-- 7. Insert facilities
INSERT INTO Facility (room_id, facility_name) VALUES
(1, 'Whiteboard'),
(1, 'Projector'),
(2, 'TV Screen'),
(3, 'Podium'),
(4, 'Computers'),
(4, 'Printer');

-- 8. Insert room features
INSERT INTO RoomFeature (feature_name, feature_description) VALUES
('Quiet Zone', 'Noise restricted area'),
('Group Work', 'Designed for collaborative study'),
('Accessible', 'Wheelchair accessible'),
('Technology Enabled', 'Equipped with modern tech');

-- 9. Link rooms to features
INSERT INTO RoomRoomFeature (room_id, feature_id) VALUES
(1, 1),
(1, 2),
(2, 2),
(3, 3),
(4, 4);

-- 10. Insert room availability
INSERT INTO RoomAvailability (room_id, day_of_week, start_time, end_time, is_available) VALUES
(1, 'Monday', '08:00:00', '20:00:00', TRUE),
(2, 'Tuesday', '08:00:00', '20:00:00', TRUE),
(3, 'Wednesday', '09:00:00', '17:00:00', TRUE),
(4, 'Thursday', '10:00:00', '18:00:00', TRUE);