from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv
import os
from .services.chat_handler import ChatHandler
from .models.database_models import Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

load_dotenv()

app = Flask(__name__)

# Database configuration
DB_USER = os.getenv('DB_USER', 'budget_app')
DB_PASS = os.getenv('DB_PASS', 'local_dev_password')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_NAME = os.getenv('DB_NAME', 'budget_db')

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

# Create tables
Base.metadata.create_all(bind=engine)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    message = data.get('message')
    
    if not message:
        return jsonify({'error': 'No message provided'}), 400
        
    session = SessionLocal()
    try:
        chat_handler = ChatHandler(session)
        response = chat_handler.process_message(message)
        return jsonify({'response': response})
    finally:
        session.close()

if __name__ == '__main__':
    app.run(debug=True)