# BookingApp – Campus Room Booking System

A Django-based web application for managing study room reservations on campus. The system supports role-based access for **Users** and **Admins**, persistent notifications, and availability enforcement.

---

## Features

### Student (User)

* View available rooms and room types
* Book rooms for specific dates and times
* Create, edit, and delete reservations
* Receive notifications about booking status
* View personal profile information

### Admin

* Manage users and roles
* Add, edit, and delete rooms
* Add, edit, and delete room types
* Monitor room availability and bookings
* View system notifications and action logs

---

## Technologies Used

* **Backend:** Python 3.14, Django
* **Frontend:** Django Templates, HTML, CSS
* **Database:** MySQL
* **IDE / Environment:** PyCharm with Python virtual environment
* **Operating Systems Supported:** Windows, macOS

---

## Project Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/BookingApp.git
cd BookingApp
```

---

### 2. Create and Activate Virtual Environment

#### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

#### macOS

```bash
python3 -m venv venv
source venv/bin/activate
```

---

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

### 4. Database Setup (MySQL)

* **Database Name:** `campus_room_booking`
* **MySQL Server:** Running locally
* **Username/Password:** Based on each user’s MySQL Workbench login

Create the database manually in MySQL by running schema.sql

---

### 5. Configure Database Connection

Update your `settings.py` file:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'campus_room_booking',
        'USER': 'your_mysql_username',
        'PASSWORD': 'your_mysql_password',
        'HOST': 'localhost',
        'PORT': '3306',
    }
}
```

---

### 6. Apply Database Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

---

### 4. Database Popualation (MySQL)

Populate the database manually in MySQL by running populate.sql

---

### 8. Default Admin Account

A default admin account is already included in the database:

* **Username:** `admin@example.com`
* **Password:** `admin123`

---

### 9. Run the Development Server

```bash
python manage.py runserver
```

Then open your browser and go to:

```
http://127.0.0.1:8000/
```

(There should be a link in the terminal of your IDE that will open the web application)

---

## Team Members

* **Alex Markoutsis**
* **Shikha Mishra**
* **Parker John Tetting**
* **Mohammad Tanvir**
* **Michael Cavros**
* **Rose Schubarth**
