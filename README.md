# 🌾 FarmRent Nigeria
### Empowering Small-Scale Farmers Through Equipment Access

> **Hackathon Demo** | Addressing agricultural underproduction in Nigeria by enabling farmers to rent modern machinery at a fraction of the purchase cost.

---

## 🎯 Problem Statement

Over 80% of Nigeria's food supply comes from small-scale farmers who rely on primitive tools because they cannot afford modern equipment. A tractor that costs ₦15M+ to purchase can now be rented for as low as ₦15,000/day through FarmRent.

---

## 🚀 Quick Start

### Prerequisites
- Python 3.8+ installed
- pip

### Run the Application

```bash
# Clone/download the project, then:
cd farmrent

# Run with the startup script (installs deps automatically)
bash run.sh

# OR manually:
pip install -r requirements.txt
cd backend && uvicorn main:app --reload --port 8000
```

Open **http://localhost:8000** in your browser.

---

## 📁 Project Structure

```
farmrent/
├── backend/
│   └── main.py              # FastAPI app (all routes)
├── frontend/
│   ├── static/
│   │   ├── css/
│   │   │   └── main.css     # All styles
│   │   ├── js/
│   │   │   └── main.js      # Utilities (Auth, Cart, Toast, API)
│   │   └── images/
│   │       └── equipment/   # Uploaded equipment images
│   └── templates/
│       ├── index.html           # Home/landing page
│       ├── auth.html            # Login + Signup (both roles)
│       ├── marketplace.html     # Equipment browse/search/cart
│       ├── farmer-dashboard.html
│       └── company-dashboard.html
├── farmrent.db              # SQLite database (auto-created)
├── requirements.txt
├── run.sh
└── README.md
```

---

## 👥 User Roles & Flows

### 🌱 Farmer Flow
1. Sign up at `/auth?role=farmer` (Name, Address, Farm Location, Email, Phone, NIN)
2. Browse equipment at `/marketplace`
3. Select equipment → choose dates & quantity → Add to Cart
4. Checkout → Mock payment confirmation
5. Get payment reference & confirmation
6. View rental history in Farmer Dashboard

### 🏢 Rental Company Flow
1. Sign up at `/auth?role=company` (Business Name, Location, Email, Phone, Tax Number)
2. Add equipment listings with images, pricing, delivery options
3. View incoming rental requests from farmers
4. Manage equipment inventory

---

## 🗄️ Database Schema

**farmers** – id, name, address, farm_location, email, phone, nin, password  
**rental_companies** – id, business_name, business_location, email, phone, tax_number, password  
**equipment** – id, company_id, name, description, price_per_day, quantity_available, delivery_available, image_url, category  
**rentals** – id, farmer_id, equipment_id, company_id, quantity, start_date, end_date, total_days, total_price, delivery_option, delivery_address, status, payment_status, payment_ref  

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/farmer/signup` | Farmer registration |
| POST | `/api/auth/farmer/login` | Farmer login |
| POST | `/api/auth/company/signup` | Company registration |
| POST | `/api/auth/company/login` | Company login |
| GET | `/api/equipment` | List all equipment (with filters) |
| GET | `/api/equipment/{id}` | Get single equipment |
| POST | `/api/equipment` | Add equipment (multipart form) |
| PUT | `/api/equipment/{id}` | Update equipment |
| DELETE | `/api/equipment/{id}` | Delete equipment |
| GET | `/api/company/{id}/equipment` | Company's equipment |
| POST | `/api/rentals` | Create rental (mock payment) |
| GET | `/api/farmer/{id}/rentals` | Farmer's rental history |
| GET | `/api/company/{id}/rentals` | Company's rental requests |
| PUT | `/api/rentals/{id}/status` | Update rental status |

Full interactive docs at: **http://localhost:8000/docs**

---

## 🔑 Demo Credentials

| Role | Email | Password |
|------|-------|----------|
| Company 1 | agromech@demo.com | demo123 |
| Company 2 | farmpower@demo.com | demo123 |
| Farmer | *(Create new account)* | - |

**8 sample equipment listings** are pre-loaded including tractors, harvesters, irrigation pumps, rice transplanters, and more.

---

## ⚙️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI (Python) |
| Database | SQLite (via sqlite3) |
| Frontend | HTML5, CSS3, Vanilla JS |
| Storage | Local file system |
| Fonts | Playfair Display + DM Sans |

---

## 🎯 Key Features

- ✅ Dual user roles (Farmer & Rental Company)
- ✅ Equipment marketplace with search & category filters
- ✅ Shopping cart with rental period calculator
- ✅ Mock payment flow with unique reference numbers
- ✅ Company dashboard with revenue tracking
- ✅ Image upload for equipment listings
- ✅ Delivery option management
- ✅ Pre-loaded sample data for demo
- ✅ Responsive design

---

*Built for Hackathon | FarmRent Nigeria 2024*
