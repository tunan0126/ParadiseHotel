# 🏨 Paradise Hotel Management System

## 📌 Introduction
Paradise Hotel is a modern, full-stack web application designed for comprehensive hotel management. It features a stunning, interactive 3D scrollytelling frontend and a robust, scalable backend powered by FastAPI and MongoDB. The system provides a seamless booking experience for guests and powerful administrative tools for hotel staff.

## 🚀 Technologies Used
### Frontend
- **HTML5/CSS3/JavaScript (Vanilla)**: For a lightweight, high-performance client experience.
- **Three.js**: Implementing immersive 3D web graphics and scrollytelling.
- **Responsive Design**: Ensuring a perfect layout across all devices.

### Backend
- **Python 3.x & FastAPI**: Lightning-fast, asynchronous API development.
- **MongoDB**: NoSQL database for flexible and scalable data storage (via `motor`).
- **Uvicorn**: High-performance ASGI web server.
- **JWT (JSON Web Tokens)**: Secure authentication and authorization.

### Deployment
- **Vercel**: Serverless deployment for both the frontend static assets and FastAPI backend.

## ⚙️ Features
- **3D Scrollytelling Tour**: An immersive visual journey through the hotel.
- **User Authentication**: Secure login and registration for guests and administrators.
- **Room Management**: Dynamic inventory tracking, room details, and categorizations.
- **Booking System**: Real-time availability checking and reservation processing.
- **Admin Dashboard**: Centralized control panel for managing users, rooms, bookings, and site settings.
- **Reviews & Ratings**: Guest feedback system to maintain service quality.

## 🛠️ Local Development Setup

### Prerequisites
- Python 3.9+
- MongoDB instance (Local or Atlas)

### Installation
1. **Clone the repository:**
   ```bash
   git clone https://github.com/tunan0126/ParadiseHotel.git
   cd ParadiseHotel
   ```

2. **Set up virtual environment (optional but recommended):**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Variables:**
   Ensure your MongoDB URI is set. You can set it in your environment:
   ```bash
   export MONGO_URI="your_mongodb_connection_string"
   ```

5. **Run the development server:**
   ```bash
   uvicorn main:app --reload
   ```

6. **Access the application:**
   - Frontend: `http://localhost:8000`
   - API Docs (Swagger UI): `http://localhost:8000/docs`

## ☁️ Deployment to Vercel
This project is configured for Vercel deployment using the `vercel.json` file.
1. Connect this repository to your Vercel account.
2. In the Vercel project settings, add the `MONGO_URI` environment variable.
3. Deploy! Vercel will automatically route API endpoints to the FastAPI backend and serve static HTML/CSS/JS files from the root.

## 📜 License
This project is for educational/demonstration purposes.

---
*Architected and engineered for modern hospitality.*
