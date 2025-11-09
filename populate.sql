-- 1. Insert default roles
INSERT INTO Role (id, role_name) VALUES
(1, 'Admin'),
(2, 'User');

-- 2. Insert an admin user
INSERT INTO User (name, email, password_hash, role_id)
VALUES
('Admin User', 'admin@example.com', 'admin123', 1);