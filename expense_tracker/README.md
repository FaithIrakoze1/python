# Expense Tracker

A full-stack expense tracking app built with FastAPI, PostgreSQL, and a lightweight HTML/CSS/JavaScript frontend. It lets users sign in with Google, manage categories, record expenses, and set category budgets.

## Features

- Google OAuth sign-in
- JWT-protected API
- Create and view personal categories
- Add, view, filter, and delete expenses
- Create and view budgets by category
- Static frontend served by FastAPI

## Tech Stack

- FastAPI
- SQLAlchemy
- PostgreSQL
- Vanilla HTML, CSS, and JavaScript
- Google OAuth 2.0
- JWT authentication

## Project Structure

```text
expense_tracker/
|-- backend/
|   |-- auth.py
|   |-- auth_routes.py
|   |-- crud.py
|   |-- database.py
|   |-- main.py
|   |-- models.py
|   |-- routes.py
|   `-- schemas.py
|-- frontend/
|   |-- index.html
|   |-- login.html
|   `-- static/
|       |-- css/
|       `-- js/
|-- requirements.txt
`-- README.md
```

## Prerequisites

- Python 3.10 or newer
- PostgreSQL
- A Google Cloud OAuth client

## Installation

1. Create and activate a virtual environment.

```powershell
cd expense_tracker
python -m venv .venv
.venv\Scripts\Activate.ps1
```

2. Install dependencies.

```powershell
pip install -r requirements.txt
pip install requests PyJWT google-auth
```

3. Create `expense_tracker/env/.env`.

```env
DATABASE_URL=postgresql://postgres:password@localhost:5432/expense_tracker
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GOOGLE_REDIRECT_URI=http://127.0.0.1:8000/api/auth/google/callback
FRONTEND_URL=http://127.0.0.1:8000
JWT_SECRET_KEY=replace-this-with-a-secure-secret
```

## Google OAuth Setup

Create OAuth credentials in Google Cloud Console and add this redirect URI:

```text
http://127.0.0.1:8000/api/auth/google/callback
```

If you run the app on a different host or port, update both Google Cloud and `GOOGLE_REDIRECT_URI` in `.env`.

## Running the App

From the `expense_tracker/backend` directory:

```powershell
uvicorn main:app --reload
```

Open the app at:

```text
http://127.0.0.1:8000
```

## Authentication Flow

1. Visit `/login`.
2. Sign in through Google.
3. Google redirects back to `/api/auth/google/callback`.
4. The backend verifies the user and issues a JWT.
5. The frontend stores that token in memory and sends it as a Bearer token on API requests.

Because the token is only kept in memory, a full refresh or new session requires signing in again.

## API Routes

Most application routes require authentication.

### Auth

- `GET /api/auth/google`
- `GET /api/auth/google/callback`

### Categories

- `POST /api/categories`
- `GET /api/categories`

### Expenses

- `POST /api/expenses`
- `GET /api/expenses`
- `GET /api/expenses/{expense_id}`
- `DELETE /api/expenses/{expense_id}`

Expense filters supported on `GET /api/expenses`:

- `category`
- `start_date`
- `end_date`

### Budgets

- `POST /api/budgets`
- `GET /api/budgets`

## Database Notes

- Tables are created automatically at startup.
- The app adds `user_id` columns to `categories`, `expenses`, and `budgets` if they are missing.
- Data is scoped per authenticated user.

## Frontend Notes

- The dashboard shows total expenses and transaction count.
- Expenses can be filtered by date range.
- The frontend includes an edit flow for expenses, but the backend currently does not expose a matching `PUT /api/expenses/{id}` route.

## Known Setup Notes

- `requests`, `PyJWT`, and `google-auth` are used by the backend but are not currently listed in `requirements.txt`.

## Future Improvements

- Add update routes for expenses, budgets, and categories
- Add automated tests
- Add Docker support
- Improve token persistence on the frontend
- Add summaries and reporting views

## License

Add a license if you plan to share or deploy the project publicly.
