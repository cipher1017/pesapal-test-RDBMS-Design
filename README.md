# Guestbook (Django front-end using mini_db)

## Install & run

1. Create virtualenv and install:
   ```bash
   python -m venv venv
   source venv/bin/activate   # or venv\Scripts\activate on Windows
   pip install -r requirements.txt
Screenshots
The terminal showing the same row (id, name, message, created) — demonstrates the web app and REPL share the same mini_db files.
<img width="980" height="349" alt="Screenshot 2026-01-14 174104" src="https://github.com/user-attachments/assets/3c112966-28af-4fab-8330-e0b7914841cf" />
<img width="768" height="274" alt="Screenshot 2026-01-14 174211" src="https://github.com/user-attachments/assets/727f43a7-03df-4b45-86c0-8fb657ec0a09" />  

Running the tests: Checks that the database rejects duplicate primary keys, database enforces UNIQUE constraints, Validates basic CRUD functionality, and Verifies that INNER JOIN works correctly.
<img width="808" height="62" alt="Screenshot 2026-01-15 161636" src="https://github.com/user-attachments/assets/3d544561-9618-4692-beff-a17c3821f044" />


In the browser go to http://127.0.0.1:8000/:

Click Add new entry
Open a second terminal in the same project folder, activate venv, run:
python repl.py
Entry added from REPL will display in the browswer.

