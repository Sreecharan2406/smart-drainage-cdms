# CDMS — Chennai Drainage Management System

A full-stack drainage infrastructure management system built with Python (Flask) and vanilla JavaScript. Designed as a portfolio project demonstrating real-world full-stack engineering — auth, database design, REST API, analytics, and role-based access control.

---

## Screenshots

> Login · Dashboard · Manage Reports · Analytics

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3, Flask, Flask-CORS |
| Database | SQLite3 (via Python stdlib) |
| Auth | bcrypt password hashing, Flask sessions |
| Frontend | Vanilla HTML/CSS/JS — zero frameworks |
| Charts | Chart.js 4.4 |
| Fonts | Space Mono, Barlow Condensed |

No React. No Node. No ORM. Just clean engineering.

---

## Features

### Auth System
- Login and registration with bcrypt-hashed passwords
- Flask session-based authentication
- Two roles — `admin` and `public`
- Role-based UI — admin sees extra tabs, public sees only their own reports

### Dashboard
- Live stat cards — active drains, blocked count, maintenance count, total reports
- High/Critical alert feed auto-populated from report data
- Zone blockage heatmap with progress bars
- Recent incident table with reporter info

### Drain Network Registry
- Full searchable, filterable table of all drains
- Filter by status, zone, or free-text search
- Admin can update drain status inline (Active / Blocked / Maintenance / Inactive)

### Report Issue
- Public users submit drainage issues with zone, drain ID, type, severity, and description
- Reports auto-assigned an ID (RPT-001, RPT-002...)
- Reporter sees their own reports with admin notes inline

### Manage Reports (Admin only)
- All reports displayed as severity-coded cards
- Click any card to open a modal — update status, add admin note
- Filter by status, severity, zone
- Admin notes are visible to the original reporter

### Maintenance Logs
- Full maintenance history table
- Filter by work type and status
- Admin can schedule new maintenance jobs with crew assignment and date

### Analytics
- Four live stat cards from real DB aggregation
- Drain status doughnut chart
- Reports by zone bar chart
- Reports by severity doughnut chart
- Drain type distribution bar chart
- Reports over time line chart (last 7 days)

### Activity Log (Admin only)
- Every action logged — login, logout, report submit, drain update, maintenance schedule, DB reset
- Shows user, action type, target, detail, and timestamp

### Admin Panel
- Add new drains to the registry
- View all registered users with roles
- Export full database as JSON
- Reset all operational data (drains, reports, maintenance)

---

## Project Structure

```
smart-drainage-cdms/
├── app.py                  # Flask backend — all routes and DB logic
├── cdms.db                 # SQLite database (auto-created on first run)
├── requirements.txt        # Python dependencies
├── README.md
└── templates/
    └── index.html          # Single-page frontend — all HTML/CSS/JS
```

---

## Database Schema

```sql
drains        — id, zone, type, diameter, inspected, status
reports       — id, zone, drain_id, type, severity, status,
                description, reporter, admin_note, created_at, updated_at
maintenance   — id, drain_id, zone, work_type, crew,
                scheduled_date, duration, status
users         — id, username, password_hash, role, created_at
activity_log  — id, user, action, target, detail, logged_at
predictions   — drain_id, risk_score, risk_level, reason, predicted_at
java_alerts   — id, zone, drain_id, message, level, triggered_at
```

---

## REST API

| Method | Route | Auth | Description |
|---|---|---|---|
| POST | `/auth/login` | Public | Login |
| POST | `/auth/logout` | Session | Logout |
| POST | `/auth/register` | Public | Register public user |
| GET | `/auth/me` | Session | Get current session |
| GET | `/drains` | Login | List all drains |
| POST | `/drains` | Admin | Add new drain |
| PATCH | `/drains/<id>` | Admin | Update drain status |
| GET | `/reports` | Login | List reports (own for public, all for admin) |
| POST | `/reports` | Login | Submit new report |
| PATCH | `/reports/<id>` | Admin | Update report status + note |
| GET | `/maintenance` | Login | List maintenance logs |
| POST | `/maintenance` | Admin | Schedule maintenance |
| GET | `/analytics` | Login | Aggregated analytics data |
| GET | `/activity_log` | Admin | Full activity log |
| GET | `/users` | Admin | List all users |
| DELETE | `/reset` | Admin | Clear all operational data |

---

## Getting Started

### Prerequisites
- Python 3.10+
- pip

### Installation

```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/smart-drainage-cdms.git
cd smart-drainage-cdms

# Install dependencies
pip install flask flask-cors bcrypt

# Run the server
python app.py
```

Open your browser at `http://127.0.0.1:5000`

### Default Admin Credentials
```
Username: admin
Password: admin123
```

Change this immediately in production.

### First Run
On first run, `app.py` automatically:
- Creates `cdms.db` with the full schema
- Seeds 15 drains across 8 Chennai zones
- Seeds 5 sample reports and 5 maintenance logs
- Creates the default admin account

---

## Design

Brutalist minimal aesthetic — raw, high contrast, thick borders, no decoration. Built around two typefaces: **Space Mono** for data and labels, **Barlow Condensed** for headings. Emerald green accent (`#00C853`) against a near-black background.

No CSS frameworks. No UI libraries. Every component hand-written.

---

## Roadmap / Possible Extensions

- [ ] Java blockage prediction engine (scoring algorithm over drain data)
- [ ] Java alert engine (background monitor, fires alerts on threshold breach)
- [ ] Map view — SVG zone map with drain locations
- [ ] Email notifications on Critical reports
- [ ] Crew management page
- [ ] Pagination on large tables
- [ ] Dark/light mode toggle

---

## License

MIT — free to use, modify, and distribute.

---

Built by Sreecharan R
