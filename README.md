# SplitJourney

SplitJourney is a mobile-first expense splitting application built with [Flet](https://flet.dev) (Python) and SQLite.

## Features
- **User Accounts**: Sign up and login.
- **Groups**: Create groups to share expenses.
- **Expenses**: Add expenses to groups and split them automatically.
- **Clean UI**: Minimalist Teal/White design.

## Prerequisites
- Python 3.7+
- pip

## Installation

1. **Create a Virtual Environment** (Recommended)
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate

   # macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

## Running the App

Run the application using Python:

```bash
python main.py
```

The app will open in a native window.

## Project Structure

- `main.py`: Entry point, handles routing.
- `theme.py`: Design constants (colors, spacing).
- `core/`: Backend logic.
  - `db.py`: Database setup.
  - `models.py`: Database models (User, Group, Expense).
  - `auth.py`: Authentication helpers.
  - `logic.py`: Business logic.
- `ui/`: User Interface views.
  - `components.py`: Reusable UI widgets.
  - `*_view.py`: Screen implementations.

## Development

This project uses `SQLAlchemy` for ORM and `Flet` for UI.
The database is a local SQLite file `splitjourney.db` created automatically on first run.
