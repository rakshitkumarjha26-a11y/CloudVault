# ☁ CloudVault — Mini Google Drive
### Cloud Computing Course Project

A complete cloud storage web application built with **Flask + MySQL + HTML/CSS/JS**.
Demonstrates **SaaS service model** on a **Public Cloud deployment model**.

---

## 📁 Folder Structure

```
cloudvault/
├── app.py                  ← Main Flask application (routes, logic)
├── database.sql            ← MySQL schema (run once to set up DB)
├── requirements.txt        ← Python dependencies
├── README.md
│
├── templates/              ← Jinja2 HTML templates
│   ├── base.html           ← Shared layout (navbar, flash messages)
│   ├── login.html          ← Login page
│   ├── register.html       ← Registration page
│   ├── dashboard.html      ← Main file manager UI
│   └── 404.html            ← Error page
│
├── static/
│   ├── css/
│   │   └── style.css       ← All styling (dark theme, responsive)
│   └── js/
│       └── main.js         ← Upload preview, drag-drop, animations
│
└── uploads/                ← Uploaded files stored here (simulates S3)
```

---

## ⚙️ Setup Instructions

### Step 1: Prerequisites
Make sure you have installed:
- Python 3.8+
- MySQL 8.0+
- pip

### Step 2: Clone / Download the project
```bash
cd Desktop
# If using git:
git clone <your-repo-url> cloudvault
cd cloudvault

# Or just unzip the downloaded folder and cd into it
```

### Step 3: Create Python virtual environment
```bash
python -m venv venv

# Activate it:
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate
```

### Step 4: Install dependencies
```bash
pip install -r requirements.txt
```

### Step 5: Set up MySQL database
Open MySQL command line or MySQL Workbench and run:
```bash
mysql -u root -p < database.sql
```
Or paste the contents of `database.sql` into MySQL Workbench and execute.

### Step 6: Configure database credentials
Open `app.py` and update the `get_db()` function:
```python
def get_db():
    return mysql.connector.connect(
        host='localhost',
        user='root',        # ← Your MySQL username
        password='',        # ← Your MySQL password
        database='cloudvault'
    )
```

### Step 7: Run the application
```bash
python app.py
```

### Step 8: Open in browser
```
http://localhost:5000
```

**Register** a new account → **Login** → **Upload files** → **Download / Delete**

---

## 🗄️ Database Schema

```sql
-- Table: users
id          INT (PK, auto-increment)
name        VARCHAR(100)
email       VARCHAR(150) UNIQUE
password    VARCHAR(255)  ← bcrypt hashed, never plain text
created_at  DATETIME

-- Table: files
id            INT (PK)
user_id       INT → FK to users.id
original_name VARCHAR(255)  ← what user sees
stored_name   VARCHAR(255)  ← UUID-based name on disk
file_size     BIGINT (bytes)
file_type     VARCHAR(20)   ← PDF, PNG, DOCX etc.
uploaded_at   DATETIME
```

---

## ☁ Cloud Concepts

### Deployment Model: Public Cloud
This application is designed for **public cloud deployment** — accessible to
any user over the internet via a browser. Contrast with:
- Private Cloud (internal company network)
- Hybrid Cloud (mix of both)

### Service Model: SaaS (Software as a Service)
Users interact with a fully managed **software application** in the browser —
no download, no installation, no infrastructure management required.
(vs IaaS = raw VMs, PaaS = managed platform)

---

## 🌐 How to Deploy on Real Cloud Platforms

### Option A: AWS (Amazon Web Services)

| This Project Component | AWS Equivalent |
|------------------------|---------------|
| `app.py` Flask app     | EC2 instance (t2.micro) running Gunicorn |
| `/uploads/` folder     | S3 Bucket (object storage) |
| MySQL local            | RDS (Relational Database Service) |
| `localhost:5000`       | Elastic Load Balancer + Route 53 domain |

**AWS Deployment Steps:**
```
1. Launch EC2 instance (Ubuntu 22.04)
2. SSH in → install Python, pip, nginx, gunicorn
3. Clone project onto EC2
4. Create S3 bucket → install boto3 → replace file.save() with:
   s3.upload_file(file_path, 'your-bucket', stored_name)
5. Create RDS MySQL → update get_db() with RDS endpoint
6. Point Elastic Load Balancer to EC2
7. Register domain in Route 53 + SSL via ACM
```

### Option B: Google Cloud Platform (GCP)

| Component | GCP Equivalent |
|-----------|---------------|
| Flask app | Cloud Run (serverless containers) |
| Files     | Google Cloud Storage bucket |
| MySQL     | Cloud SQL (MySQL) |
| Domain    | Cloud DNS + Load Balancer |

### Option C: Microsoft Azure

| Component | Azure Equivalent |
|-----------|-----------------|
| Flask app | Azure App Service |
| Files     | Azure Blob Storage |
| MySQL     | Azure Database for MySQL |
| Domain    | Azure Front Door |

---

## 🔒 Security Features

- **Password Hashing**: Werkzeug `generate_password_hash` (PBKDF2-SHA256)
- **Session Management**: Flask server-side sessions
- **File Validation**: Extension whitelist + 10 MB size limit
- **UUID Filenames**: Prevents path traversal and collision attacks
- **User Isolation**: Files scoped to `user_id` — users can't access others' files
- **Secure Filename**: `werkzeug.utils.secure_filename` sanitizes uploads

---

## 📦 Allowed File Types
PNG, JPG, JPEG, GIF, PDF, DOC, DOCX, TXT, ZIP, MP4, XLSX, PPTX

Maximum file size: **10 MB**

---

## 🚀 Tech Stack

| Layer      | Technology |
|------------|-----------|
| Backend    | Python 3 + Flask |
| Database   | MySQL 8 |
| Frontend   | HTML5 + CSS3 + Vanilla JS |
| Templating | Jinja2 |
| Auth       | Werkzeug password hashing |
| Fonts      | Google Fonts (Syne + DM Sans) |

---

*Built for Cloud Computing Course — demonstrating SaaS on Public Cloud.*
