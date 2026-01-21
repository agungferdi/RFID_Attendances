# Time Room - RFID Attendance Tracking System

A real-time RFID-based attendance tracking system using URA4 fixed reader. Track employees entering and exiting different areas (Production, Warehouse, etc.) through antenna gates.

## Features

- 🔄 **Real-time tracking**: WebSocket-based live updates
- 👤 **Employee identification**: Match RFID cards to employee profiles
- 📍 **Multi-area support**: Track presence in different areas via different antennas
- ⏱️ **Duration tracking**: Automatically calculate time spent in each area
- 📊 **Dashboard**: Modern dark theme UI with glass morphism design
- 🗄️ **Supabase integration**: Cloud database for employees and attendance logs

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   URA4 Reader   │────▶│  Python Backend │────▶│  React Frontend │
│  (RFID Cards)   │     │    (main.py)    │     │   (Dashboard)   │
└─────────────────┘     └────────┬────────┘     └─────────────────┘
                                 │
                                 ▼
                        ┌─────────────────┐
                        │    Supabase     │
                        │   (Database)    │
                        └─────────────────┘
```

## Backend Structure

```
backend/
├── main.py              # Entry point
├── config.py            # Configuration settings
├── ura4_monitor.py      # URA4 RFID reader polling
├── tag_processor.py     # Tag processing and debouncing
├── websocket_handler.py # WebSocket connections
├── http_handler.py      # REST API endpoints
├── supabase_client.py   # Database operations
└── requirements.txt     # Dependencies
```

## How It Works

1. **Employee scans RFID card** at antenna gate
2. **URA4 reader** captures EPC code and antenna port
3. **Backend server** polls URA4 API for tag data
4. **Supabase lookup** matches EPC to employee identity
5. **Logic determines IN/OUT**:
   - If employee has no active record at this location → **IN** (start tracking)
   - If employee has active record at this location → **OUT** (complete, calculate duration)
6. **Frontend updates** in real-time via WebSocket

## Setup

### Prerequisites

- Python 3.8+
- Node.js 16+
- URA4 RFID Reader (connected to network)
- Supabase account with database configured

### Database Setup (Supabase)

The following tables should already be created in your Supabase database:

```sql
-- 1. Employees table
CREATE TABLE employees (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    epc_code TEXT UNIQUE NOT NULL,
    full_name TEXT NOT NULL,
    office TEXT,
    position TEXT,
    address TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. Locations table (antenna to area mapping)
CREATE TABLE locations (
    id SERIAL PRIMARY KEY,
    antenna_port INTEGER UNIQUE NOT NULL,
    area_name TEXT NOT NULL
);

-- 3. Attendance logs
CREATE TABLE attendance_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    employee_id UUID REFERENCES employees(id) ON DELETE CASCADE,
    location_id INTEGER REFERENCES locations(id),
    time_in TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    time_out TIMESTAMP WITH TIME ZONE,
    duration INTERVAL GENERATED ALWAYS AS (time_out - time_in) STORED,
    status TEXT CHECK (status IN ('IN', 'COMPLETED')) DEFAULT 'IN'
);

-- Indexes
CREATE INDEX idx_epc_code ON employees(epc_code);
CREATE INDEX idx_attendance_status ON attendance_logs(employee_id, status);
```

### Sample Data

```sql
-- Add locations (antenna port to area mapping)
INSERT INTO locations (antenna_port, area_name) VALUES
(1, 'Production'),
(2, 'Warehouse'),
(3, 'Office'),
(4, 'Lab');

-- Add sample employees
INSERT INTO employees (epc_code, full_name, office, position) VALUES
('E2801170000002151234ABCD', 'John Doe', 'IT Department', 'Software Engineer'),
('E2801170000002151234EFGH', 'Jane Smith', 'HR Department', 'HR Manager'),
('E2801170000002151234IJKL', 'Bob Wilson', 'Operations', 'Technician');
```

### Backend Setup

1. Navigate to backend folder:
   ```bash
   cd backend
   ```

2. Create virtual environment:
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   # or
   source venv/bin/activate  # Linux/Mac
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create `.env` file:
   ```env
   URA4_IP=192.168.1.100
   URA4_HTTP_PORT=8080
   WEBSOCKET_PORT=8765
   HTTP_API_PORT=8766
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_KEY=your-service-role-key
   ```

5. Start the server:
   ```bash
   python server.py
   ```

### Frontend Setup

1. Navigate to frontend folder:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Update `.env` if needed:
   ```env
   REACT_APP_SUPABASE_URL=https://your-project.supabase.co
   REACT_APP_SUPABASE_PUBLISHABLE_DEFAULT_KEY=your-publishable-key
   REACT_APP_BACKEND_WS=ws://localhost:8765
   REACT_APP_BACKEND_API=http://localhost:8766
   ```

4. Start the app:
   ```bash
   npm start
   ```

5. Open http://localhost:3000 in your browser

## Usage

### Dashboard

- **Stats Cards**: View active employees, today's entries, and completed sessions
- **Currently in Areas**: See who is currently in each area with duration
- **Recent Scans**: Live feed of RFID scan events
- **Simulate Panel**: Test the system without physical RFID cards

### Attendance Tab

- View complete attendance history
- Sort by employee, area, time, or status
- Duration automatically calculated for completed sessions

### Employees Tab

- View all registered employees
- Search by name, office, or position
- See EPC codes assigned to each employee

## API Endpoints

### REST API (HTTP)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/status` | GET | Server connection status |
| `/api/events` | GET | Recent scan events |
| `/api/active` | GET | Currently active employees |
| `/api/logs` | GET | Attendance history |
| `/api/employees` | GET | All registered employees |
| `/api/locations` | GET | All configured areas |
| `/api/stats` | GET | Today's statistics |
| `/api/simulate` | POST | Simulate an RFID scan |
| `/api/clear` | POST | Clear recent events |

### WebSocket Commands

| Command | Description |
|---------|-------------|
| `get_active` | Request active employees |
| `get_logs` | Request attendance logs |
| `get_stats` | Request today's stats |
| `get_employees` | Request employee list |
| `get_locations` | Request location list |

## Antenna Logic

- **Same antenna = toggle IN/OUT**: When an employee scans at an antenna, the system checks if they're already IN at that location. If so, marks them OUT. If not, marks them IN.
- **Different areas are independent**: An employee can be IN multiple areas simultaneously (e.g., checked into both Production and Warehouse).

## Troubleshooting

1. **Backend not connecting to URA4**
   - Check URA4 IP address and port in `.env`
   - Ensure URA4 inventory is started from the default web interface

2. **Frontend not updating**
   - Check WebSocket connection status in header
   - Verify backend is running on correct ports

3. **Unknown EPC codes**
   - Add employee records to Supabase with matching EPC codes
   - EPC codes must match exactly (uppercase)

4. **Supabase connection errors**
   - Verify SUPABASE_URL and SUPABASE_KEY in `.env`
   - Use service role key for backend (full access)
   - Use publishable key for frontend (read-only)

## License

MIT License
