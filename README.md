# Staywise — Residential Management System

A beginner-friendly full-stack residence management dashboard built with **Python (Flask), SQLite, HTML, CSS, and JavaScript**.

## Features
- Overview dashboard with resident, room, occupancy, and maintenance statistics
- Resident directory with search
- **Register new residents** with roll number, name, department, year, email, and phone
- Room directory with occupied and available bed counts
- **Allocate rooms to residents**; only rooms with available capacity are listed, and the backend prevents duplicate allocations and over-capacity rooms
- Maintenance complaint creation and status updates
- SQLite database stored locally in `hostel.db`

## Run locally

1. Open this folder in VS Code.
2. Open **Terminal → New Terminal**.
3. Create a virtual environment (skip if you already have `.venv`):
   ```bash
   python3 -m venv .venv
   ```
4. Activate it:
   ```bash
   source .venv/bin/activate
   ```
5. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
6. Start the server:
   ```bash
   python app.py
   ```
7. Open **http://127.0.0.1:5000** in your browser.

If port 5000 is already occupied, stop the earlier server with `Control + C` in its terminal. Alternatively, change the last line of `app.py` to `app.run(debug=True, port=5001)` and open `http://127.0.0.1:5001`.

## Using the new features

### Register a resident
1. Click **Residents** in the sidebar.
2. Click **Register resident**.
3. Fill in the required fields and submit. Roll numbers must be unique; email addresses must also be unique if provided.

### Allocate a room
1. Register a resident first if they are not in the directory.
2. Open **Residents** or **Rooms** and click **Allocate room**.
3. Select an unallocated resident and a room with available beds.
4. Confirm the allocation. The dashboard and room occupancy figures refresh automatically.

Existing sample records are retained. On first run, sample residents, rooms, allocations, and complaints are created automatically. To reset the demo data, stop the server and remove `hostel.db`; the next run recreates it. **Back up `hostel.db` before deleting it.**

## API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/dashboard` | Dashboard metrics |
| GET | `/api/students` | List residents and their room assignments |
| POST | `/api/students` | Register a resident |
| GET | `/api/rooms` | List rooms and occupancy |
| GET | `/api/rooms/available` | List rooms with available beds |
| POST | `/api/allotments` | Allocate a room to a resident |
| GET | `/api/complaints` | List maintenance requests |
| POST | `/api/complaints` | Create a maintenance request |
| PATCH | `/api/complaints/<id>` | Update request status |

## Notes
- This is a portfolio/demo starter, not yet a production deployment.
- Before public deployment, add authentication and authorization, CSRF protection, stronger validation, and production server configuration.
