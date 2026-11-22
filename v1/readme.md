# TrekHub — Trekking Management Application

TrekHub is a comprehensive web-based Trekking Management Application that streamlines interactions between Administrators, Trek Staff, and Trekkers. Built with Flask and Bootstrap, the application features role-based access controls, dynamic trek scheduling with collision/gap checking, session security via single-use authentication keys, and interactive user reviews.

---

## Key Features

### User Roles & Capabilities

* **Admin Dashboard:**
  * **Trek Management:** Create and schedule treks, set slots, location, difficulty, and duration.
  * **Smart Staff Assignment:** Prevents scheduling conflicts by verifying staff availability and ensuring required day gaps between assignments.
  * **User & Staff Control:** Approve new staff registrations, and dynamically activate or block staff and trekker accounts.
* **Staff Dashboard:**
  * View assigned ongoing and past treks.
  * Manage booking approvals for assigned treks.
  * Update trek statuses (e.g., set status to completed upon trek conclusion).
* **Trekker Dashboard:**
  * Browse available treks and request bookings.
  * View personal booking and trek history.
  * Rate completed treks and assigned staff members upon trek completion.

### Security & Architecture Highlights

* **Secure Authentication:** Password hashing powered by `bcrypt`.
* **Session Security:** Generates a unique `auth_key` in the database upon login required for authorized access; `auth_key` resets to `NULL` on logout to prevent unauthorized access.
* **Database Management:** Object-Relational Mapping (ORM) managed via Flask-SQLAlchemy over SQLite.

---

## Tech Stack

| Technology / Library | Purpose |
| :--- | :--- |
| **Flask** | Core backend web framework |
| **Flask-SQLAlchemy** | Database ORM and management |
| **Flask-Jinja2** | Dynamic HTML template rendering |
| **Bcrypt** | Secure password hashing |
| **Bootstrap** | Responsive UI styling and layout |
| **SQLite** | Lightweight file-based relational database |

---

## Project Architecture

```text
.
├── app.py           # Main Flask application entry point
├── model.py         # Database models (Flask-SQLAlchemy)
├── controller.py    # Application routes and logic controllers
├── setup.py         # Dependency setup and admin initializer script
├── /templates       # Jinja2 HTML templates
└── /instance        # Contains SQLite database file (tms.sqlite3)
```

---

## Database Schema & Entity Relationships

### Database Tables

1. **`user_credentials`**: Stores primary user authentication details (User ID, role, hashed password, email, and dynamic `auth_key`).
2. **`staff_profile`**: Stores staff member details (Staff ID, User ID, name, address, status, ratings, and completed treks count).
3. **`trekker_profile`**: Stores trekker profile details (Trekker ID, User ID, name, address, and status).
4. **`treks`**: Stores details for created treks (Trek ID, name, assigned staff ID, location, difficulty, available slots, booking deadlines, duration, start/end dates, status, and ratings).
5. **`bookings`**: Tracks trekker bookings (Booking ID, Trekker ID, Trek ID, booking date, status, staff rating, and trek rating).

### Entity Relationships

* **One-to-One:** `user_credentials` → `trekker_profile`
* **One-to-One:** `user_credentials` → `staff_profile`
* **One-to-Many:** `trekker_profile` → `bookings`
* **One-to-Many:** `treks` → `bookings`
* **One-to-Many:** `staff_profile` → `treks`

---

## Installation & Setup Guide

### Prerequisites

Ensure Python is installed on your system. Verify by running:

```cmd
python --version
```

### Setup Steps

1. **Install Dependencies & Initialize Database**  
   Open Command Prompt (`cmd`), navigate to the project directory, and execute:
   ```cmd
   python setup.py
   ```

2. **Launch Application**  
   Start the application server:
   ```cmd
   python app.py
   ```

3. **Access Application**  
   Open your web browser and navigate to the local server URL printed in the terminal (typically `http://127.0.0.1:5000/`).

---

## Default Admin Credentials

* **Email:** `admin@trekhub.com`
* **Password:** `admin`

> **Note:** To create custom admin credentials, delete the `/instance` folder and re-run `python setup.py`. The setup prompt will guide you through setting custom administrator credentials.
