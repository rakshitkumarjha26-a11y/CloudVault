"""
CloudVault v4 - Cloud Storage Web Application
Cloud Computing Course Project
Service Model: SaaS | Deployment: Public Cloud
"""

import os, uuid, base64
from datetime import datetime
from functools import wraps

from flask import (Flask, render_template, request, redirect,
                   url_for, session, flash, send_from_directory, jsonify)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import mysql.connector

app = Flask(__name__)
app.secret_key = 'cloudvault-super-secret-key-change-in-production'

UPLOAD_FOLDER     = os.path.join(os.path.dirname(__file__), 'uploads')
ALLOWED_EXTENSIONS = {'png','jpg','jpeg','gif','pdf','doc','docx','txt','zip','mp4','xlsx','pptx'}
IMAGE_EXTENSIONS   = {'png','jpg','jpeg','gif'}
MAX_FILE_SIZE      = 10 * 1024 * 1024

app.config['UPLOAD_FOLDER']      = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ── Category mapping ──
CATEGORIES = {
    'Images':    {'exts': {'PNG','JPG','JPEG','GIF'},          'icon': '🖼️',  'color': 'cat-purple'},
    'Documents': {'exts': {'PDF','DOC','DOCX','TXT','XLSX','PPTX'}, 'icon': '📄', 'color': 'cat-blue'},
    'Archives':  {'exts': {'ZIP'},                              'icon': '🗜️',  'color': 'cat-amber'},
    'Videos':    {'exts': {'MP4'},                              'icon': '🎬',  'color': 'cat-red'},
}

def get_category(file_type):
    for cat, data in CATEGORIES.items():
        if file_type in data['exts']:
            return cat
    return 'Other'

def get_db():
    return mysql.connector.connect(
        host='localhost',
        user='root',
        password='',            # ← YOUR MYSQL PASSWORD HERE
        database='cloudvault'
    )

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.',1)[1].lower() in ALLOWED_EXTENSIONS

def is_image(file_type):
    return file_type.upper() in {e.upper() for e in IMAGE_EXTENSIONS}

def format_size(b):
    if b < 1024:       return f"{b} B"
    if b < 1024**2:    return f"{b/1024:.1f} KB"
    if b < 1024**3:    return f"{b/(1024**2):.1f} MB"
    return f"{b/(1024**3):.1f} GB"

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login first.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

# ── Auth Routes ──
@app.route('/')
def index():
    return redirect(url_for('dashboard') if 'user_id' in session else url_for('login'))

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        name     = request.form.get('name','').strip()
        email    = request.form.get('email','').strip().lower()
        password = request.form.get('password','')
        if not name or not email or not password:
            flash('All fields are required.', 'danger')
            return render_template('register.html')
        if len(password) < 6:
            flash('Password must be at least 6 characters.', 'danger')
            return render_template('register.html')
        try:
            db = get_db(); cur = db.cursor()
            cur.execute("INSERT INTO users (name,email,password) VALUES (%s,%s,%s)",
                        (name, email, generate_password_hash(password)))
            db.commit(); cur.close(); db.close()
            flash('Account created! Please login.', 'success')
            return redirect(url_for('login'))
        except mysql.connector.IntegrityError:
            flash('Email already registered.', 'danger')
        except Exception as e:
            flash(f'Error: {e}', 'danger')
    return render_template('register.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email    = request.form.get('email','').strip().lower()
        password = request.form.get('password','')
        try:
            db = get_db(); cur = db.cursor(dictionary=True)
            cur.execute("SELECT * FROM users WHERE email=%s", (email,))
            user = cur.fetchone(); cur.close(); db.close()
            if user and check_password_hash(user['password'], password):
                session['user_id']    = user['id']
                session['user_name']  = user['name']
                session['user_email'] = user['email']
                flash(f"Welcome back, {user['name']}!", 'success')
                return redirect(url_for('dashboard'))
            flash('Invalid email or password.', 'danger')
        except Exception as e:
            flash(f'Login error: {e}', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.', 'info')
    return redirect(url_for('login'))

# ── Dashboard ──
@app.route('/dashboard')
@login_required
def dashboard():
    try:
        db = get_db(); cur = db.cursor(dictionary=True)
        cur.execute("""SELECT id, original_name, stored_name, file_size, file_type, uploaded_at
                       FROM files WHERE user_id=%s AND deleted=0
                       ORDER BY uploaded_at DESC""", (session['user_id'],))
        files = cur.fetchall(); cur.close(); db.close()

        for f in files:
            f['size_readable'] = format_size(f['file_size'])
            f['category']      = get_category(f['file_type'])
            f['is_image']      = is_image(f['file_type'])

        total_bytes = sum(f['file_size'] for f in files)

        # Build category groups
        cat_groups = {}
        for f in files:
            cat = f['category']
            if cat not in cat_groups:
                cat_groups[cat] = {'files': [], 'size': 0,
                                   'icon':  CATEGORIES.get(cat, {}).get('icon','📁'),
                                   'color': CATEGORIES.get(cat, {}).get('color','cat-gray')}
            cat_groups[cat]['files'].append(f)
            cat_groups[cat]['size'] += f['file_size']

        for cat in cat_groups:
            cat_groups[cat]['size_readable'] = format_size(cat_groups[cat]['size'])

        # Trash count badge
        db2 = get_db(); cur2 = db2.cursor()
        cur2.execute("SELECT COUNT(*) FROM files WHERE user_id=%s AND deleted=1", (session['user_id'],))
        trash_count = cur2.fetchone()[0]; cur2.close(); db2.close()

        return render_template('dashboard.html',
                               files=files,
                               cat_groups=cat_groups,
                               total_files=len(files),
                               total_size=format_size(total_bytes),
                               total_size_bytes=total_bytes,
                               trash_count=trash_count)
    except Exception as e:
        flash(f'Dashboard error: {e}', 'danger')
        return render_template('dashboard.html', files=[], cat_groups={},
                               total_files=0, total_size='0 B',
                               total_size_bytes=0, trash_count=0)

# ── Trash Route ──
@app.route('/trash')
@login_required
def trash():
    try:
        db = get_db(); cur = db.cursor(dictionary=True)
        cur.execute("""SELECT id, original_name, stored_name, file_size, file_type, uploaded_at, deleted_at
                       FROM files WHERE user_id=%s AND deleted=1
                       ORDER BY deleted_at DESC""", (session['user_id'],))
        files = cur.fetchall(); cur.close(); db.close()
        for f in files:
            f['size_readable'] = format_size(f['file_size'])
            f['category']      = get_category(f['file_type'])
        return render_template('trash.html', files=files, total_files=len(files))
    except Exception as e:
        flash(f'Error: {e}', 'danger')
        return render_template('trash.html', files=[], total_files=0)

# ── Upload ──
@app.route('/upload', methods=['POST'])
@login_required
def upload():
    if 'file' not in request.files or request.files['file'].filename == '':
        flash('No file selected.', 'warning')
        return redirect(url_for('dashboard'))
    file = request.files['file']
    if not allowed_file(file.filename):
        flash('File type not allowed.', 'danger')
        return redirect(url_for('dashboard'))
    try:
        original_name = secure_filename(file.filename)
        ext           = original_name.rsplit('.',1)[1].lower()
        stored_name   = f"{uuid.uuid4().hex}.{ext}"
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], stored_name))
        file_size = os.path.getsize(os.path.join(app.config['UPLOAD_FOLDER'], stored_name))
        db = get_db(); cur = db.cursor()
        cur.execute("""INSERT INTO files (user_id,original_name,stored_name,file_size,file_type)
                       VALUES (%s,%s,%s,%s,%s)""",
                    (session['user_id'], original_name, stored_name, file_size, ext.upper()))
        db.commit(); cur.close(); db.close()
        flash(f'"{original_name}" uploaded successfully!', 'success')
    except Exception as e:
        flash(f'Upload failed: {e}', 'danger')
    return redirect(url_for('dashboard'))

# ── Download ──
@app.route('/download/<int:file_id>')
@login_required
def download(file_id):
    try:
        db = get_db(); cur = db.cursor(dictionary=True)
        cur.execute("SELECT * FROM files WHERE id=%s AND user_id=%s AND deleted=0",
                    (file_id, session['user_id']))
        f = cur.fetchone(); cur.close(); db.close()
        if not f:
            flash('File not found.', 'danger')
            return redirect(url_for('dashboard'))
        return send_from_directory(app.config['UPLOAD_FOLDER'], f['stored_name'],
                                   as_attachment=True, download_name=f['original_name'])
    except Exception as e:
        flash(f'Download failed: {e}', 'danger')
        return redirect(url_for('dashboard'))

# ── Soft Delete (move to trash) ──
@app.route('/delete/<int:file_id>', methods=['POST'])
@login_required
def delete(file_id):
    try:
        db = get_db(); cur = db.cursor(dictionary=True)
        cur.execute("SELECT * FROM files WHERE id=%s AND user_id=%s AND deleted=0",
                    (file_id, session['user_id']))
        f = cur.fetchone()
        if not f:
            flash('File not found.', 'danger')
        else:
            cur.execute("UPDATE files SET deleted=1, deleted_at=NOW() WHERE id=%s", (file_id,))
            db.commit()
            flash(f'"{f["original_name"]}" moved to Trash.', 'success')
        cur.close(); db.close()
    except Exception as e:
        flash(f'Delete failed: {e}', 'danger')
    return redirect(url_for('dashboard'))

# ── Restore from Trash ──
@app.route('/restore/<int:file_id>', methods=['POST'])
@login_required
def restore(file_id):
    try:
        db = get_db(); cur = db.cursor(dictionary=True)
        cur.execute("SELECT * FROM files WHERE id=%s AND user_id=%s AND deleted=1",
                    (file_id, session['user_id']))
        f = cur.fetchone()
        if not f:
            flash('File not found in trash.', 'danger')
        else:
            cur.execute("UPDATE files SET deleted=0, deleted_at=NULL WHERE id=%s", (file_id,))
            db.commit()
            flash(f'"{f["original_name"]}" restored successfully.', 'success')
        cur.close(); db.close()
    except Exception as e:
        flash(f'Restore failed: {e}', 'danger')
    return redirect(url_for('trash'))

# ── Permanent Delete ──
@app.route('/delete_permanent/<int:file_id>', methods=['POST'])
@login_required
def delete_permanent(file_id):
    try:
        db = get_db(); cur = db.cursor(dictionary=True)
        cur.execute("SELECT * FROM files WHERE id=%s AND user_id=%s AND deleted=1",
                    (file_id, session['user_id']))
        f = cur.fetchone()
        if not f:
            flash('File not found.', 'danger')
        else:
            fp = os.path.join(app.config['UPLOAD_FOLDER'], f['stored_name'])
            if os.path.exists(fp): os.remove(fp)
            cur.execute("DELETE FROM files WHERE id=%s", (file_id,))
            db.commit()
            flash(f'"{f["original_name"]}" permanently deleted.', 'success')
        cur.close(); db.close()
    except Exception as e:
        flash(f'Error: {e}', 'danger')
    return redirect(url_for('trash'))

# ── Empty Trash ──
@app.route('/empty_trash', methods=['POST'])
@login_required
def empty_trash():
    try:
        db = get_db(); cur = db.cursor(dictionary=True)
        cur.execute("SELECT * FROM files WHERE user_id=%s AND deleted=1", (session['user_id'],))
        files = cur.fetchall()
        for f in files:
            fp = os.path.join(app.config['UPLOAD_FOLDER'], f['stored_name'])
            if os.path.exists(fp): os.remove(fp)
        cur.execute("DELETE FROM files WHERE user_id=%s AND deleted=1", (session['user_id'],))
        db.commit(); cur.close(); db.close()
        flash(f'Trash emptied — {len(files)} file(s) permanently deleted.', 'success')
    except Exception as e:
        flash(f'Error: {e}', 'danger')
    return redirect(url_for('trash'))

# ── Image Preview API ──
@app.route('/preview/<int:file_id>')
@login_required
def preview(file_id):
    try:
        db = get_db(); cur = db.cursor(dictionary=True)
        cur.execute("SELECT * FROM files WHERE id=%s AND user_id=%s AND deleted=0",
                    (file_id, session['user_id']))
        f = cur.fetchone(); cur.close(); db.close()
        if not f or not is_image(f['file_type']):
            return jsonify({'error': 'Not found'}), 404
        fp = os.path.join(app.config['UPLOAD_FOLDER'], f['stored_name'])
        ext_map = {'PNG':'image/png','JPG':'image/jpeg','JPEG':'image/jpeg','GIF':'image/gif'}
        mime = ext_map.get(f['file_type'], 'image/jpeg')
        with open(fp, 'rb') as img:
            data = base64.b64encode(img.read()).decode()
        return jsonify({'src': f"data:{mime};base64,{data}",
                        'name': f['original_name'],
                        'size': format_size(f['file_size']),
                        'date': f['uploaded_at'].strftime('%d %b %Y, %I:%M %p')})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.errorhandler(413)
def file_too_large(e):
    flash('File too large! Max 10 MB.', 'danger')
    return redirect(url_for('dashboard'))

@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
