# HSE MANAGEMENT SYSTEM - FINAL PROJECT SUMMARY

## TECHNOLOGY STACK

Frontend
- HTML
- CSS
- JavaScript

Backend
- FastAPI

Database
- PostgreSQL

Authentication
- JWT Authentication

Architecture

Frontend
    ↓
FastAPI APIs
    ↓
PostgreSQL Database

All modules share the same PostgreSQL database.

---

# FINALIZED ROLES

## 1. Admin

Responsibilities

- Create Users
- Update Users
- Activate Users
- Deactivate Users
- Reset Passwords
- Assign Roles

Restrictions

- Cannot create incidents
- Cannot manage incidents
- Cannot create tasks
- Cannot manage tasks
- Cannot create trainings
- Cannot manage trainings
- Cannot approve requests
- Cannot access operational dashboard

Purpose

Admin exists only for User Management.

---

## 2. HSE Manager

Responsibilities

- Create Incident Reports
- Manage Incident Lifecycle
- Assign Tasks
- Review Tasks
- Create Trainings
- Assign Trainings
- Track Training Completion
- Approve / Reject Requests
- View Dashboard & Reports

Purpose

Main operational user of the system.

---

## 3. Employee

Responsibilities

- View Assigned Tasks
- Update Task Status
- View Assigned Trainings
- Complete Trainings
- Submit Approval Requests (if required)

Restrictions

- Cannot manage users
- Cannot create incidents
- Cannot create trainings
- Cannot assign tasks
- Cannot approve requests

Purpose

Performs assigned work.

---

# INCIDENT DEFINITION

Incident = Any accident, unsafe act, unsafe condition, or near miss occurring within the organization.

Examples

- Employee slips on wet floor
- Fire incident
- Chemical spill
- PPE violation
- Property damage
- Near miss event

Example Flow

Cleaning employee forgets warning sign
↓
Another employee slips
↓
Incident occurs
↓
HSE Manager logs incident
↓
Investigation completed
↓
Training assigned to responsible employee
↓
Employee completes training
↓
Incident closed

---

# FINALIZED MODULES

# MODULE 1 - AUTHENTICATION & USER MANAGEMENT

Purpose

Foundation of the entire system.

Every user must exist here before accessing any other module.

---

## Authentication

Responsibilities

- Login
- Logout
- JWT Authentication
- Session Validation

Authentication Flow

User enters:

- Email
- Password

↓

System validates credentials

↓

JWT Token Generated

↓

Frontend stores token

↓

Subsequent requests include:

Authorization: Bearer <token>

---

## User Management

Responsibilities

- Create User
- Update User
- View Users
- Search Users
- Reset Password
- Activate User
- Deactivate User
- Assign Roles

Roles Available

- Admin
- HSE Manager
- Employee

---

### Database Table

users

- user_id UUID PK
- full_name VARCHAR(150)
- email VARCHAR(255)
- password_hash TEXT
- role VARCHAR(20)
- status VARCHAR(20)
- created_at TIMESTAMP
- updated_at TIMESTAMP

---

### APIs

POST /login

POST /users

GET /users

GET /users/{id}

PUT /users/{id}

PATCH /users/{id}/status

PATCH /users/{id}/reset-password

---

# MODULE 2 - INCIDENT MANAGEMENT

Purpose

Manage safety incidents from reporting to closure.

---

Responsibilities

- Create Incident
- Assign Responsible Employee
- Investigate Incident
- Track Incident Status
- Close Incident

---

Incident Status Flow

Reported
↓
Under Investigation
↓
Resolved
↓
Closed

---

Database Table

incidents

- incident_id UUID PK
- title VARCHAR(255)
- description TEXT
- incident_type VARCHAR(100)
- severity VARCHAR(20)
- location VARCHAR(255)
- status VARCHAR(50)
- reported_by UUID FK users
- assigned_to UUID FK users
- created_at TIMESTAMP
- updated_at TIMESTAMP

---

APIs

POST /incidents

GET /incidents

GET /incidents/{id}

PUT /incidents/{id}

PATCH /incidents/{id}/status

---

# MODULE 3 - TASK MANAGEMENT

Purpose

Track work assigned by HSE Manager.

---

Responsibilities

- Create Task
- Assign Employee
- Track Progress
- Review Completion

---

Task Status Flow

To Do
↓
In Progress
↓
Review
↓
Done

---

Priority Levels

- Low
- Medium
- High
- Urgent

---

Database Table

tasks

- task_id UUID PK
- title VARCHAR(255)
- description TEXT
- priority VARCHAR(20)
- status VARCHAR(20)
- assigned_to UUID FK users
- created_by UUID FK users
- incident_id UUID FK incidents NULL
- due_date DATE
- reviewed_by UUID FK users NULL
- reviewed_at TIMESTAMP NULL
- created_at TIMESTAMP
- updated_at TIMESTAMP
- is_deleted BOOLEAN

---

Important Decision

One Task = One Employee

No task_assignments table required.

---

APIs

POST /tasks

GET /tasks

GET /tasks/{id}

PUT /tasks/{id}

PATCH /tasks/{id}/status

PATCH /tasks/{id}/review

---

# MODULE 4 - APPROVAL MANAGEMENT

Purpose

Handle review and approval workflows.

---

Responsibilities

- Review Requests
- Approve Requests
- Reject Requests
- Track Approval History

---

Approval Status

Pending
Approved
Rejected

---

Possible Approval Types

- Incident Closure Approval
- Training Completion Approval
- Task Completion Approval

---

Database Table

approvals

- approval_id UUID PK
- module_type VARCHAR(50)
- reference_id UUID
- requested_by UUID FK users
- approved_by UUID FK users
- status VARCHAR(20)
- comments TEXT
- created_at TIMESTAMP
- updated_at TIMESTAMP

---

APIs

POST /approvals

GET /approvals

GET /approvals/{id}

PATCH /approvals/{id}/approve

PATCH /approvals/{id}/reject

---

# MODULE 5 - TRAINING MANAGEMENT

Purpose

Manage employee training programs.

---

Responsibilities

- Create Training
- Assign Training
- Track Training Completion
- Generate Training Reports

---

Training Status

Assigned
↓
In Progress
↓
Completed

---

Business Rule

One Training = One Employee

Training is typically created because of an incident and assigned to the responsible employee.

Therefore:

Single training table is sufficient.

No training_assignments table required.

---

Database Table

trainings

- training_id UUID PK
- incident_id UUID FK incidents NULL
- title VARCHAR(255)
- training_type VARCHAR(100)
- description TEXT
- instructor VARCHAR(255)
- assigned_to UUID FK users
- status VARCHAR(20)
- start_date DATE
- end_date DATE
- created_by UUID FK users
- created_at TIMESTAMP

---

APIs

POST /trainings

GET /trainings

GET /trainings/{id}

PUT /trainings/{id}

PATCH /trainings/{id}/status

---

# MODULE 6 - DASHBOARD & REPORTING

Purpose

Provide operational visibility and analytics.

---

Responsibilities

- Dashboard Cards
- Reports
- Charts
- Trend Analysis
- Statistics

---

Reads Data From

- users
- incidents
- tasks
- trainings
- approvals

Dashboard owns no data.

---

Example Dashboard Metrics

- Total Users
- Open Incidents
- Closed Incidents
- Pending Tasks
- Tasks Under Review
- Completed Tasks
- Pending Approvals
- Training Completion Rate
- Overdue Trainings

---

APIs

GET /dashboard/summary

GET /dashboard/incidents

GET /dashboard/tasks

GET /dashboard/trainings

GET /dashboard/approvals

GET /dashboard/charts

---

# FINAL DATABASE TABLES

1. users

2. incidents

3. tasks

4. approvals

5. trainings

---

# FINAL MODULE 1 TEST CASES

## Authentication

- Login with valid Admin credentials
- Login with valid HSE Manager credentials
- Login with valid Employee credentials
- Login with invalid email
- Login with invalid password
- Login with empty email
- Login with empty password
- Login with both email and password empty
- Login with inactive user account
- Verify successful login redirects to dashboard
- Logout successfully

---

## User Management

### Create User

- Create Admin user
- Create HSE Manager user
- Create Employee user
- Create user with all mandatory fields
- Create user with duplicate email
- Create user with invalid email format
- Create user without full name
- Create user without email
- Create user without password
- Create user without selecting role

### View Users

- View user list
- Verify newly created user appears in user list
- Verify user details are displayed correctly

### Search Users

- Search user by full name
- Search user by email
- Search user using partial text
- Search with no matching results
- Clear search results

### Update User

- Update user full name
- Update user email
- Update user role
- Save updated user information

### User Status Management

- Change user status from Active to Inactive
- Change user status from Inactive to Active
- Verify inactive user remains visible in user list
- Verify active user can login
- Verify inactive user cannot login

### Password Management

- Reset user password
- Login using reset password
- Verify old password no longer works after reset

### Validation

- Verify mandatory field validation messages
- Verify email field accepts valid format
- Verify email field rejects invalid format

---

# DEVELOPMENT PLAN

Phase 1
- Requirements Finalization ✅

Phase 2
- ERD Design

Phase 3
- Database Schema Design

Phase 4
- CTO Review & Approval

Phase 5
- PostgreSQL Table Creation

Phase 6
- FastAPI Project Setup

Phase 7
- Authentication Module

Phase 8
- User Management Module

Phase 9
- Incident Module

Phase 10
- Task Module

Phase 11
- Training Module

Phase 12
- Approval Module

Phase 13
- Dashboard Module

Phase 14
- Testing & QA

---

# TEAM DISTRIBUTION (SUGGESTED)

Developer 1
- Authentication
- User Management

Developer 2
- Incident Management

Developer 3
- Task Management

Developer 4
- Approval Management

Developer 5
- Training Management

Developer 6
- Dashboard & Reporting

---

# DATABASE COLLABORATION STRATEGY

Recommended Approach

Each developer runs PostgreSQL locally.

Database schema is maintained in Git.

Structure:

database/

001_users.sql

002_incidents.sql

003_tasks.sql

004_approvals.sql

005_trainings.sql

Benefits

- Version Controlled
- Easy Collaboration
- Easy Rollback
- Consistent Schema Across Team
- No Shared Database Conflicts

Future Improvement

Use Alembic Migrations for schema versioning and updates.