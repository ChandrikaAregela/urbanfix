from flask import Flask, render_template, request, redirect
import sqlite3
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Upload Folder Configuration

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Database Setup
def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS complaints (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        issue TEXT,
        area TEXT,
        description TEXT,
        image TEXT,
        reports INTEGER DEFAULT 1,
        status TEXT DEFAULT 'Pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP) ''')
    conn.commit()
    conn.close()
init_db()


# Home Page
@app.route('/')
def home():
    return render_template('index.html')

# Report Issue
@app.route('/report', methods=['GET', 'POST'])
def report():
    if request.method == 'POST':
        issue = request.form['issue']
        area = request.form['area']
        description = request.form['description']
        image = request.files['image']
        filename = secure_filename(image.filename)
        image.save(
            os.path.join(
                app.config['UPLOAD_FOLDER'],
                filename
            )
        )
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()

        # Check duplicate issue
        cursor.execute('''SELECT * FROM complaints WHERE issue = ? AND area = ?''', (issue, area))
        existing_issue = cursor.fetchone()

        # Increase report count
        if existing_issue:
            cursor.execute('''UPDATE complaints SET reports = reports + 1 WHERE id = ? ''', (existing_issue[0],))

        # Insert new complaint
        else:
            cursor.execute('''INSERT INTO complaints (issue,area,description,image)
                VALUES (?, ?, ?, ?)''', (issue,area,description,filename))

        conn.commit()
        conn.close()
        return redirect('/complaints')
    return render_template('report.html')


# Complaints Page
@app.route('/complaints')
def complaints():
    search = request.args.get('search')
    status = request.args.get('status')
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    query = 'SELECT * FROM complaints WHERE 1=1'
    params = []

    # Search functionality
    if search:
        query += '''AND (issue LIKE ? OR area LIKE ?)'''
        params.append(f'%{search}%')
        params.append(f'%{search}%')

    # Status filter
    if status and status != 'All':
        query += ' AND status = ?'
        params.append(status)
    cursor.execute(query, params)
    complaints_data = cursor.fetchall()
    conn.close()
    return render_template('complaints.html',complaints=complaints_data)

# Dashboard
@app.route('/dashboard')
def dashboard():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM complaints')
    total_complaints = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM complaints WHERE status='Pending'")
    pending_complaints = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM complaints WHERE status='Resolved'")
    resolved_complaints = cursor.fetchone()[0]
    cursor.execute('SELECT SUM(reports) FROM complaints')
    total_reports = cursor.fetchone()[0]
    conn.close()
    return render_template('dashboard.html',
        total=total_complaints,
        pending=pending_complaints,
        resolved=resolved_complaints,
        reports=total_reports
    )

# Update Status

@app.route('/update_status/<int:id>', methods=['GET', 'POST'])
def update_status(id):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    if request.method == 'POST':
        new_status = request.form['status']
        cursor.execute(''' UPDATE complaints SET status = ? WHERE id = ? ''', (new_status, id))
        conn.commit()
        conn.close()

        return redirect('/complaints')
    cursor.execute('SELECT * FROM complaints WHERE id = ?', (id,))
    complaint = cursor.fetchone()
    conn.close()
    return render_template('update_status.html',complaint=complaint)


# Run Application
if __name__ == '__main__':

    app.run(debug=True)