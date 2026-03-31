# Bowler-Option

Bowler-Option is a context-aware cricket bowler recommendation system. It uses match context, pitch type, weather conditions, and trained machine learning models to recommend the most suitable bowlers before a match.

## Features

- International and local prediction modes
- Weather-aware recommendations using Open-Meteo
- Top bowler recommendations with alternatives
- Human-readable explanation output
- User authentication and prediction history
- CSV export for generated predictions

## Tech Stack

- Frontend: HTML, CSS, JavaScript
- Backend: Node.js, Express.js
- Machine Learning: Python, scikit-learn, pandas, NumPy
- Database: MongoDB
- External API: Open-Meteo

## Project Structure

```text
Bowler-Optionfullstack/
├── Front-end/
│   ├── homepage.html
│   ├── predictionpage.html
│   ├── login.html
│   ├── sign-up.html
│   └── youraccount.html
├── Backend/
│   ├── config/
│   ├── controllers/
│   ├── middleware/
│   ├── models/
│   ├── routes/
│   ├── package.json
│   └── server.js
├── predict_runtime.py
├── bowler-DatsetFinal.csv
├── international-mode.pkl
├── local-mode.pkl
└── requirements.txt
```

## Prerequisites

Install these before running the project:

- Node.js 18+
- Python 3.10+ or newer
- MongoDB Atlas connection string or a local MongoDB instance

## Setup Instructions

### 1. Clone the repository

```bash
git clone <your-repository-url>
cd Bowler-Optionfullstack
```

### 2. Create the Python virtual environment

From the project root:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

This project expects the Python interpreter at:

```text
venv/bin/python
```

### 3. Install backend dependencies

```bash
cd Backend
npm install
cd ..
```

### 4. Create the backend environment file

Create a file named:

```text
Backend/.env
```

Add:

```env
MONGO_URI=your_mongodb_connection_string
JWT_SECRET=your_secret_key
PORT=5001
```

### 5. Start the backend server

```bash
cd Backend
npm start
```

The backend will run at:

```text
http://localhost:5001
```

### 6. Run the frontend

Open the files inside `Front-end/` using a static server.

One simple option is VS Code Live Server:

- Open the project in VS Code
- Right-click `Front-end/homepage.html`
- Click `Open with Live Server`

You can also use Python:

```bash
cd Front-end
python3 -m http.server 5500
```

Then open:

```text
http://localhost:5500/homepage.html
```

## How to Use

1. Open the homepage
2. Register a new user or log in
3. Open the prediction page
4. Select prediction mode
5. Enter match context
6. Generate recommendations
7. Review top bowlers, alternatives, and explanations
8. Optionally export results or check saved history

## Important Notes

- The frontend currently calls the backend at `http://localhost:5001`
- The Python runtime loads:
  - `bowler-DatsetFinal.csv`
  - `international-mode.pkl`
  - `local-mode.pkl`
- Keep these files in the project root
- Local mode is currently focused on Sri Lankan locations
- The current prediction scope is mainly for Sri Lankan bowlers

## Troubleshooting

### Backend not reachable

Check:

- backend server is running
- `PORT=5001`
- frontend is calling `http://localhost:5001`

### Python prediction errors

Check:

- virtual environment exists at `venv/`
- required Python packages are installed
- model files exist in the project root

### MongoDB connection error

Check:

- `MONGO_URI` is correct
- database access is allowed from your IP

## Future Improvements

- Extend prediction support to bowlers from other countries
- Make local mode usable worldwide
- Add direct sharing of prediction results with team members
- Add phase-based or over-based bowler recommendation

