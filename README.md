# LostLink

LostLink is an intelligent Lost & Found platform designed to help reunite people with their lost belongings. It features AI-powered matching based on text similarity and image hashing, user authentication, in-platform messaging, and email/SMS alerts.

## Features

- **Item Listing**: Report lost and found items with photos, locations, and category tags.
- **AI-Powered Matching**: Automatically identifies potential matches using text embeddings (`sentence-transformers`), semantic search, and perceptual image hashing (`imagehash`).
- **Claim & Verification System**: Submit claims for found items with verification questions or proof.
- **Direct Messaging**: In-app chat between finders and owners.
- **Multi-channel Notifications**: Email and SMS notifications (Twilio) for match updates.

## Tech Stack

- **Backend**: Python, Flask, Flask-SQLAlchemy, Flask-WTF
- **Database**: SQLite (default) / PostgreSQL compatible
- **AI / ML**: Sentence Transformers, Scikit-learn, ImageHash, Pillow
- **Frontend**: HTML5, CSS3, JavaScript, Jinja2 templates

## Getting Started

### 1. Clone the repository
```bash
git clone https://github.com/your-username/LostLink.git
cd LostLink
```

### 2. Create a virtual environment & install dependencies
```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
```

### 3. Environment Variables
Copy `.env.example` to `.env` and adjust settings as needed:
```bash
cp .env.example .env
```

### 4. Run the application
```bash
python app.py
```
Open your browser and navigate to `http://127.0.0.1:5000`.

## License
MIT

