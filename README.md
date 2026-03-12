# PinBoard – A Pinterest-Style Image Sharing App

PinBoard is a modern, feature-rich web application inspired by Pinterest. Built with Flask and SQLAlchemy, it offers a clean, responsive UI where users can discover, share, and interact with visual content.

## ✨ Features

### Visual & Interactive UI
* **Masonry Layout:** A stunning, true-masonry pin grid that preserves original image aspect ratios.
* **Dynamic Dark Mode:** A premium dark theme that seamlessly toggles and persists across visits.
* **Expanded View:** Click any pin to open a beautiful, full-screen modal showing details and comments.
* **Image Downloads:** Natively download and save high-resolution pins directly to your device.
* **Clean Frontend:** Built with vanilla CSS variables and Bootstrap for a highly responsive, polished experience.

### Discover & Organize
* **Smart Search:** Find pins instantly by searching against titles, descriptions, and `#tags`.
* **Save & Like:** Curate your own collection by saving pins, and show appreciation with the live like system.
* **Tags Support:** Categorize your uploads with custom tags.
* **Real-time Home Feed:** The dashboard automatically refreshes to show the latest community uploads.

### Social Interaction
* **Pin Comments:** Join the conversation by leaving comments on your favorite pins.
* **Direct Messaging:** Private, real-time one-to-one messaging with other users.
* **Pin Sharing:** Share any pin directly with a friend via a dedicated in-app popup.
* **User Discovery:** Live user search functionality to easily find friends.

### Core Architecture
* **Secure Authentication:** User signup, secure password hashing, and session management via Flask-Login.
* **Robust File Handling:** Drag-and-drop image uploads with live preview, supporting images up to 16MB.
* **Database Driven:** Powered by SQLAlchemy for reliable data management (configured for SQLite by default, easily adaptable to PostgreSQL).

## 🚀 Getting Started

### Prerequisites
* Python 3.8+
* Ensure you are in a virtual environment (`.venv`)

### Installation

1. **Install Dependencies:**
   Install the required packages using pip:
   ```bash
   pip install -r requirements.txt
   ```

2. **Initialize Database:**
   Ensure the database is set up correctly (an initial `app.db` may be generated automatically depending on your environment). Start the application to initialize the tables.

3. **Run the Application:**
   Start the local development server:
   ```bash
   python run.py
   ```

4. **Access the App:**
   Open your browser and navigate to `http://127.0.0.1:5000`.

## 📁 Project Structure

```
d:\pinterest\
├── app/
│   ├── static/
│   │   ├── css/        # Core styling and dark mode logic
│   │   ├── js/         # Client-side interactions and polling
│   │   └── uploads/    # User uploaded images
│   ├── templates/      # HTML views (Jinja2)
│   ├── __init__.py     # Application factory and route definitions
│   └── models.py       # SQLAlchemy database schemas
├── instance/           # Default SQLite database location
├── requirements.txt    # Python dependencies
└── run.py              # Application entry point
```
