# Furniture Shop (Django + HTML/CSS + SQLite)

A simple multi-page demo furniture store built with Django (Python), HTML, CSS, and SQLite.

## Requirements
- Python 3.10+
- Windows PowerShell (commands below)

## Setup
```powershell
# In project root
python -m venv .venv
.venv\Scripts\python -m pip install --upgrade pip
.venv\Scripts\python -m pip install django

# First run
.venv\Scripts\python manage.py migrate
.venv\Scripts\python manage.py runserver
```
Site will be available at http://127.0.0.1:8000/

## Pages (URLs)
- /
- /about/
- /contact/
- /furniture/
- /furniture/chairs/
- /furniture/tables/
- /furniture/beds/
- /furniture/sofas/
- /furniture/wardrobes/
- /furniture/office/
- /furniture/outdoor/
- /furniture/kids/
- /cart/
- /checkout/
- /payment-methods/
- /order-success/

## Project Structure
- manage.py
- furniture_shop/ (project settings, urls)
- core/ (app: views, urls)
- templates/ (HTML templates)
- static/css/styles.css (site CSS)

## Notes
- SQLite is used by default (db.sqlite3 created on first migrate).
- This is a demo: no real products, cart, or payment processing.
