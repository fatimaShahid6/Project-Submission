from flask import Flask, request, jsonify, render_template, send_from_directory, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_pymongo import PyMongo
import os
import logging
from PIL import Image
import torch
from torchvision import transforms, models
import torch.nn as nn
import numpy as np
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
from time import time

# Initialize Flask and MongoDB
app = Flask(__name__)
app.secret_key = 'Smart.Sort#1911'  
app.config["MONGO_URI"] = "mongodb://localhost:27017/sort_system"
mongo = PyMongo(app)

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


# Recreate the model architecture
model = models.mobilenet_v2()
model.classifier[1] = nn.Linear(in_features=1280, out_features=2)  # Match your number of classes

# Load state dictionary
try:
    model.load_state_dict(torch.load('best_model.pth', map_location=torch.device('cpu')))
except FileNotFoundError:
    logger.error("Model file 'best_model.pth' not found.")
    raise Exception("Model file 'best_model.pth' not found. Ensure the file exists in the correct directory.")

# Set the model to evaluation mode
model.eval()

# Set up upload folder
UPLOAD_FOLDER = 'uploads/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Define allowed file extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

# Initialize global variables to store stats and history
stats = {
    'totalClassifications': 0,
    'recyclableCount': 0,
    'nonRecyclableCount': 0,
}

history = []

# Function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Image Preprocessing (same transformations used during training)
preprocess = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

# Route for uploading and predicting the image class
@app.route('/upload_image', methods=['POST'])
def predict():
    start_time = time()

    if 'image' not in request.files:
        logger.warning('No file part in the request.')
        return jsonify({'error': 'No file part'}), 400

    file = request.files['image']

    # Check if no file is selected or file is empty
    if file.filename == '' or not file:
        logger.warning('No file selected or file is empty.')
        return jsonify({'error': 'No selected file or empty file'}), 400

    # Check if the file extension is allowed
    if not allowed_file(file.filename):
        logger.warning(f"Invalid file extension: {file.filename}")
        return jsonify({'error': 'Invalid file extension'}), 400
    
    # Save the uploaded file
    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    try:
        file.save(file_path)
        logger.info(f"Saved file {filename} to {file_path}")
    except Exception as e:
        logger.error(f"Failed to save file {filename}: {str(e)}")
        return jsonify({'error': f'Failed to save image: {str(e)}'}), 500

    # Open and preprocess the image
    try:
        img = Image.open(file.stream).convert("RGB")
    except Exception as e:
        logger.error(f"Failed to open image: {str(e)}")
        return jsonify({'error': f'Failed to open image: {str(e)}'}), 400

    try:
        img_tensor = preprocess(img).unsqueeze(0)
        img_tensor = img_tensor.to(torch.device('cpu'))  # Ensure the tensor is on the correct device
    except Exception as e:
        logger.error(f"Failed to preprocess image: {str(e)}")
        return jsonify({'error': f'Failed to preprocess image: {str(e)}'}), 400

    # Make a prediction
    try:
        with torch.no_grad():
            outputs = model(img_tensor)
            probs = torch.softmax(outputs, dim=1)
            
            # Adjust threshold for "Recyclable" class (index 1)
            threshold = 0.5  # Adjust this value based on model testing/validation
            if probs[0][1] > threshold:
                predicted_label = "Recyclable"
            else:
                predicted_label = "Non-Recyclable"
            
            confidence = probs.max().item()
    except Exception as e:
        logger.error(f"Prediction failed: {str(e)}")
        return jsonify({'error': f'Failed to predict: {str(e)}'}), 500
    
    # Update statistics
    stats['totalClassifications'] += 1
    if predicted_label == 'Recyclable':
        stats['recyclableCount'] += 1
    else:
        stats['nonRecyclableCount'] += 1

    # Add to history
    history.append({
        'id': stats['totalClassifications'],
        'category': predicted_label,
        'confidence': f"{confidence * 100:.2f}%",
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'image_url': f'/uploads/{filename}'  # Include the path to the uploaded image
    })

    # Calculate processing time
    end_time = time()
    logger.info(f"Image processed in {end_time - start_time:.2f} seconds")

    return jsonify({
        'category': predicted_label,
        'confidence': confidence,
        'image_url': f'/uploads/{filename}'  # Return the URL of the uploaded image
    })

# Route to get classification statistics
@app.route('/stats', methods=['GET'])
def get_stats():
    return jsonify({
        'totalClassifications': stats['totalClassifications'],
        'recyclablePercentage': (stats['recyclableCount'] / stats['totalClassifications']) * 100 if stats['totalClassifications'] > 0 else 0,
        'nonRecyclablePercentage': (stats['nonRecyclableCount'] / stats['totalClassifications']) * 100 if stats['totalClassifications'] > 0 else 0,
    })

# Route to get classification history
@app.route('/history', methods=['GET'])
def get_history():
    return jsonify(history)

# Route for checking if the server is running
@app.route('/')
def home():
    if 'email' in session:
        # If the user is logged in, redirect to their role-specific dashboard
        if session['role'] == 'admin':
            return redirect(url_for('admin_dashboard'))
        elif session['role'] == 'user':
            return redirect(url_for('user_dashboard'))
    # If no user is logged in, render the home page
    return render_template('home.html')

@app.route('/signup')
def signup_page():
    return render_template('signup.html')  # Direct the user to the signup page

@app.route('/login')
def login_page():
    return render_template('login.html')  # Direct the user to the login page


# Serve the uploaded images from the 'uploads' folder
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Periodic cleanup function to remove files older than 1 day
def clean_uploads_folder():
    current_time = time()
    for filename in os.listdir(UPLOAD_FOLDER):
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        if os.stat(file_path).st_mtime < current_time - 86400:  # 1 day in seconds
            try:
                os.remove(file_path)
                logger.info(f"Removed old file: {filename}")
            except Exception as e:
                logger.error(f"Failed to delete file {filename}: {str(e)}")


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        # Set the default role to 'user'
        role = 'user'

        # Check if the email already exists
        if mongo.db.users.find_one({'email': email}):
            flash('Email already exists. Please choose a different one.', 'danger')
            return redirect(url_for('signup'))

        # Hash password and save user
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        mongo.db.users.insert_one({
            'email': email,
            'password': hashed_password,
            'role': role
        })

        # Automatically log in the user and redirect to the user dashboard
        session['email'] = email
        session['role'] = role
        flash('Signup successful! Welcome to SmartSort.', 'success')
        return redirect(url_for('user_dashboard'))

    return render_template('signup.html')

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # Fetch user from the database
        user = mongo.db.users.find_one({'email': email})
        if user and check_password_hash(user['password'], password):
            session['email'] = email
            session['role'] = user['role']
            flash('Login successful!', 'success')

            # Redirect based on role
            if user['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('user_dashboard'))

        flash('Invalid email or password.', 'danger')

    return render_template('login.html')

@app.route('/user_dashboard')
def user_dashboard():
    if 'email' in session and session['role'] == 'user':
        return render_template('user.html')
    flash('Unauthorized access.', 'danger')
    return redirect(url_for('login'))

@app.route('/admin_dashboard')
def admin_dashboard():
    if 'email' in session and session['role'] == 'admin':
        return render_template('admin.html')
    flash('Unauthorized access.', 'danger')
    return redirect(url_for('login'))

# Route to get users (Admin-only access)
@app.route('/api/users', methods=['GET'])
def get_users():
    if 'role' in session and session['role'] == 'admin':  # Ensure the user is an admin
        print("Fetching users from the database...")  # Log to check if the route is being accessed
        # Fetch users whose role is 'user' from MongoDB
        users = mongo.db.users.find({'role': 'user'})  
        user_list = []
        for user in users:
            user_list.append({'email': user['email'], 'role': user['role']})
        return jsonify(user_list)  # Return the list of users as JSON
    else:
        return jsonify({'error': 'Unauthorized access'}), 403

# Route to delete user (Admin-only access)
@app.route('/api/users', methods=['DELETE'])
def delete_user():
    if 'role' in session and session['role'] == 'admin':  # Ensure the user is an admin
        email = request.args.get('email')
        if email:
            result = mongo.db.users.delete_one({'email': email})
            if result.deleted_count > 0:
                return jsonify({'message': 'User successfully removed.'})
            else:
                return jsonify({'error': 'User not found.'}), 404
        else:
            return jsonify({'error': 'Email is required.'}), 400
    else:
        return jsonify({'error': 'Unauthorized access'}), 403


# Logout route
@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
