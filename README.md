# 📋 Monlam Annotation Tools (Custom Doccano)

**Production-grade annotation tracking system with Tibetan language support**

Built with Django REST Framework (backend) and Vue.js 3 + Vuetify 3 (frontend).

---

## 🎯 Features

### Core Annotation System
- ✅ **Multi-project support** - Sequence labeling, document classification, STT, seq2seq, image annotation
- ✅ **Role-based access control** - Annotator, Approver, Project Manager, Project Admin
- ✅ **Annotation tracking** - Track who annotated, who reviewed, and status
- ✅ **Example locking** - Prevent simultaneous editing conflicts
- ✅ **Visibility filtering** - Annotators only see pending/rejected-by-them examples

### Approve/Reject Workflow
- ✅ **Floating review panel** - Fixed bottom-right buttons for reviewers
- ✅ **Approval with optional notes**
- ✅ **Rejection with required reason**
- ✅ **Automatic status updates**

### Completion Dashboard
- ✅ **Overall progress tracking** - Visual progress bar and statistics
- ✅ **Annotator performance metrics** - Completed, approved, rejected, success rate
- ✅ **Reviewer performance metrics** - Reviewed, approval rate
- ✅ **Export reports**

### STT Projects
- ✅ **Audio auto-play** - Plays when example loads
- ✅ **Audio auto-loop** - Continuous playback for transcription
- ✅ **Handles browser autoplay restrictions**

### Tibetan Language Support
- ✅ **MonlamTBslim font** - Embedded Tibetan font
- ✅ **Tibetan menu labels** - བོད་ཡིག་ UI elements
- ✅ **Tibetan project names** - Support for Tibetan text throughout

### Monlam Branding
- ✅ **Monlam Gold (#B8963E)** - Primary accent color
- ✅ **Monlam Navy (#1a1a2e)** - Navbar and dark elements
- ✅ **Custom logo and favicon**
- ✅ **No GitHub links**

---

## 🏗️ Architecture

```
doccano_Vue/
├── backend/                    # Django REST Framework
│   ├── config/                 # Django settings
│   ├── apps/
│   │   ├── users/             # Custom user model
│   │   ├── projects/          # Projects and members
│   │   ├── examples/          # Examples (data items)
│   │   ├── labels/            # Label types and annotations
│   │   ├── monlam_tracking/   # Annotation tracking system
│   │   └── monlam_ui/         # Custom UI views
│   └── templates/
├── frontend/                   # Vue.js 3 + Vuetify 3
│   ├── src/
│   │   ├── components/        # Reusable components
│   │   ├── views/             # Page views
│   │   ├── stores/            # Pinia stores
│   │   └── services/          # API services
│   └── public/
├── nginx/                      # Nginx config
├── Dockerfile                  # Production Docker
├── docker-compose.yml          # Production compose
└── render.yaml                 # Render.com blueprint
```

---

## 🚀 Quick Start

### Development (Docker)

```bash
# Clone the repository
git clone https://github.com/MonlamAI/Monlam-Annotation-Tools.git
cd Monlam-Annotation-Tools

# Start development environment
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

# Access:
# - Frontend: http://localhost:3000
# - Backend API: http://localhost:8000/v1/
# - Admin: http://localhost:8000/admin/
```

### Development (Local)

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r ../requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver

# Frontend (new terminal)
cd frontend
npm install
npm run dev
```

### Production (Docker)

```bash
# Build and run
docker-compose up -d --build

# Run migrations
docker-compose exec backend python manage.py migrate

# Create superuser
docker-compose exec backend python manage.py createsuperuser
```

### Deploy to Render.com

#### Step 1: Push to GitHub

```bash
# Initialize git (if not already)
git init

# Add remote
git remote add origin https://github.com/YOUR_ORG/monlam-annotation-tools.git

# Add all files
git add .

# Commit
git commit -m "Initial commit: Monlam Annotation Tools"

# Push
git push -u origin main
```

#### Step 2: Create PostgreSQL Database on Render

1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click **New** → **PostgreSQL**
3. Configure:
   - **Name**: `monlam-doccano-db`
   - **Database**: `monlam_doccano`
   - **User**: `doccano`
   - **Region**: Oregon (or your preference)
   - **Plan**: Starter ($7/mo) or Free (for testing)
4. Click **Create Database**
5. Copy the **Internal Database URL** (you'll need this)

#### Step 3: Deploy Web Service

**Option A: Blueprint (Automatic)**
1. Click **New** → **Blueprint**
2. Connect your GitHub repo
3. Select `render.yaml`
4. Render will automatically create the database and web service

**Option B: Manual Setup**
1. Click **New** → **Web Service**
2. Connect your GitHub repo
3. Configure:
   - **Name**: `monlam-doccano`
   - **Environment**: Docker
   - **Branch**: main
   - **Region**: Oregon (same as DB)
4. Add Environment Variables:
   ```
   DATABASE_URL=<your-internal-database-url>
   SECRET_KEY=<generate-a-strong-key>
   DEBUG=False
   ALLOWED_HOSTS=.onrender.com
   CORS_ALLOWED_ORIGINS=https://monlam-doccano.onrender.com
   ```
5. Click **Create Web Service**

#### Step 4: Run Migrations

After first deployment:
1. Go to your Web Service on Render
2. Click **Shell** tab
3. Run:
   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   ```

#### Step 5: Verify Deployment

- Health check: `https://your-app.onrender.com/health/`
- Admin: `https://your-app.onrender.com/admin/`
- API: `https://your-app.onrender.com/v1/`

---

## 🔑 User Roles

| Role | Can Annotate | Can Review | Can See All | Can Manage |
|------|--------------|------------|-------------|------------|
| **Annotator** | ✅ | ❌ | ❌ | ❌ |
| **Approver** | ✅ | ✅ | ✅ | ❌ |
| **Project Manager** | ✅ | ✅ | ✅ | ✅ Limited |
| **Project Admin** | ✅ | ✅ | ✅ | ✅ Full |

---

## 🔄 Workflow

### Annotator Workflow
1. Login → Dashboard
2. Select project → See only pending examples
3. Annotate → Save
4. Example disappears (status: submitted)
5. If rejected → Example reappears with notes
6. Fix and re-submit

### Reviewer Workflow
1. Login → Select project
2. Filter by "submitted" status
3. Open example → Review annotation
4. Approve or Reject (with notes)
5. Status updates automatically

### Project Manager Workflow
1. Access completion dashboard
2. View overall progress
3. Monitor annotator performance
4. Monitor reviewer performance
5. Export reports

---

## 📊 API Endpoints

### Tracking API

```
GET    /v1/projects/{id}/tracking/                    # List tracking records
GET    /v1/projects/{id}/tracking/{example_id}/       # Get tracking
GET    /v1/projects/{id}/tracking/{example_id}/status/ # Get status
POST   /v1/projects/{id}/tracking/{example_id}/approve/ # Approve
POST   /v1/projects/{id}/tracking/{example_id}/reject/  # Reject
POST   /v1/projects/{id}/tracking/{example_id}/lock/   # Lock
POST   /v1/projects/{id}/tracking/{example_id}/unlock/ # Unlock
GET    /v1/projects/{id}/tracking/summary/            # Summary stats
GET    /v1/projects/{id}/tracking/annotators/         # Annotator stats
GET    /v1/projects/{id}/tracking/approvers/          # Reviewer stats
```

### Completion Dashboard

```
GET    /monlam/{id}/completion/     # Dashboard page
GET    /monlam/{id}/completion/api/ # Dashboard JSON
```

---

## 🎨 Status Colors

| Status | Color | Hex |
|--------|-------|-----|
| Pending | Gray | `#e0e0e0` |
| In Progress | Blue | `#2196f3` |
| Submitted | Orange | `#ff9800` |
| Approved | Green | `#4caf50` |
| Rejected | Red | `#f44336` |

---

## 🔧 Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | Django secret key | Required |
| `DEBUG` | Debug mode | `False` |
| `DATABASE_URL` | PostgreSQL connection | Required |
| `ALLOWED_HOSTS` | Comma-separated hosts | `localhost` |
| `CORS_ALLOWED_ORIGINS` | Comma-separated origins | - |
| `USE_S3` | Use AWS S3 for media | `False` |
| `AWS_ACCESS_KEY_ID` | AWS access key | - |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key | - |
| `AWS_STORAGE_BUCKET_NAME` | S3 bucket name | - |

---

## 📁 Font Setup

Place MonlamTBslim font files in:
- `frontend/public/fonts/MonlamTBslim.woff2`
- `frontend/public/fonts/MonlamTBslim.woff`
- `frontend/public/fonts/MonlamTBslim.ttf`

---

## 🧪 Testing

```bash
# Backend tests
cd backend
python manage.py test

# Frontend tests
cd frontend
npm run test
```

---

## 📄 License

Proprietary - Monlam AI

---

## 🙏 Acknowledgments

- Based on [Doccano](https://github.com/doccano/doccano) open-source annotation tool
- Customized for Tibetan language annotation workflows
- Developed for Monlam AI

---

**སྨོན་ལམ། - Monlam Annotation Tools**

