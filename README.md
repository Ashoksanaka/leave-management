# Workflow-Driven Leave Management System API

## Overview
This project implements a workflow-based Leave Management System API using Django Rest Framework, PostgreSQL, and JWT authentication. It supports multi-step leave approval processes based on user roles and leave policies.

## Tech Stack
- Framework: Django Rest Framework
- Database: PostgreSQL
- Authentication: JWT

## User Roles and Permissions
- **Employee**
  - Can apply for leave and view their own leave requests.
  - Can submit, cancel leave requests (only when status is not final).
- **Manager**
  - Can view leave requests of their direct reports.
  - Can approve or reject leave requests from their team.
- **HR/Admin**
  - Can view all leave requests.
  - Can override any leave decision by approving or rejecting.
  - Can view audit logs of all leave status transitions.

## Features
- Leave request fields: start_date, end_date, leave_type (CL, SL, PL), reason, status.
- Status flow: draft → submitted → approved (manager) → approved (HR) OR submitted → rejected (manager/HR).
- Each status transition is logged with actor and timestamp.
- Rate limiting: employees can submit max 3 leave requests per day.
- Audit log endpoint for leave transitions (read-only, HR only).
- Optional approval expiration: auto-cancel leave requests pending approval > 3 days.

## Setup Instructions

1. Clone the repository:
   ```
   git clone https://github.com/Ashoksanaka/leave-management.git
   cd leave-management-api
   ```

2. Create and activate a virtual environment:
   ```
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Configure PostgreSQL database settings in `config/settings.py`.

5. Run migrations:
   ```
   python manage.py makemigrations
   python manage.py migrate
   ```

6. Create a superuser:
   ```
   python manage.py createsuperuser
   ```

7. Run the development server:
   ```
   python manage.py runserver
   ```

## API Documentation

- JWT Authentication:
  - `POST /api/token/` - Obtain JWT token.
  - `POST /api/token/refresh/` - Refresh JWT token.

- Leave Requests:
  - `GET /api/leave-requests/` - List leave requests (filtered by role).
  - `POST /api/leave-requests/` - Create a leave request (Employee only).
  - `GET /api/leave-requests/{id}/` - Retrieve a leave request.
  - `PUT/PATCH /api/leave-requests/{id}/` - Update a leave request.
  - `DELETE /api/leave-requests/{id}/` - Delete a leave request.
  - `POST /api/leave-requests/{id}/submit/` - Submit a draft leave request.
  - `POST /api/leave-requests/{id}/approve/` - Approve a leave request (Manager or HR).
  - `POST /api/leave-requests/{id}/reject/` - Reject a leave request (Manager or HR).
  - `POST /api/leave-requests/{id}/cancel/` - Cancel a leave request (Employee).

- Audit Log:
  - `GET /api/audit-log/` - List all leave status transitions (HR only).
