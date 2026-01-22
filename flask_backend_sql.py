# app.py - Main application file
from flask import Flask, request, jsonify, session, render_template, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime
import os
from werkzeug.security import generate_password_hash, check_password_hash
import pymysql

pymysql.install_as_MySQLdb()

app = Flask(__name__)
CORS(app, 
     resources={r"/*": {
         "origins": ["http://localhost:8000", "http://127.0.0.1:8000", "http://127.0.0.1:5000"],
         "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
         "allow_headers": ["Content-Type", "Authorization"],
         "supports_credentials": True
     }},
     supports_credentials=True)

# Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@127.0.0.1:3306/greengear'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key-here'

db = SQLAlchemy(app)

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='customer')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    author_name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class UserCar(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    company = db.Column(db.String(100), nullable=False)
    model = db.Column(db.String(100), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    mileage = db.Column(db.Float, nullable=False)
    fuel_type = db.Column(db.String(50), nullable=False)
    transmission = db.Column(db.String(20), nullable=False)
    image_url = db.Column(db.String(500))
    type = db.Column(db.String(50))
    color = db.Column(db.String(50))
    registration_number = db.Column(db.String(100))
    purchase_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Add relationship to User model
User.cars = db.relationship('UserCar', backref='owner', lazy=True)

# New Models for Enhanced Features
class Trip(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    start_location = db.Column(db.String(255), nullable=False)
    end_location = db.Column(db.String(255), nullable=False)
    distance = db.Column(db.Float, nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('user_car.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='trips')
    vehicle = db.relationship('UserCar', backref='trips')
    emission_record = db.relationship('EmissionRecord', backref='trip', uselist=False)

class EmissionRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    trip_id = db.Column(db.Integer, db.ForeignKey('trip.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('user_car.id'), nullable=False)
    co2_emissions = db.Column(db.Float, nullable=False)
    distance = db.Column(db.Float, nullable=False)
    fuel_consumed = db.Column(db.Float, nullable=False)
    record_date = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='emission_records')
    vehicle = db.relationship('UserCar', backref='emission_records')

class CommunityPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    post_type = db.Column(db.Enum('discussion', 'achievement', 'question', 'tip'), nullable=False)
    likes = db.Column(db.Integer, default=0)
    views = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='posts')
    comments = db.relationship('PostComment', backref='post', lazy='dynamic')

class PostComment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('community_post.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    likes = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='comments')

# Serve HTML files
@app.route('/')
def home():
    return send_from_directory('.', 'login.html')

@app.route('/<path:filename>')
def serve_file(filename):
    return send_from_directory('.', filename)

# Authentication Routes
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    
    if not data or not all(k in data for k in ['username', 'email', 'password']):
        return jsonify({'error': 'Missing required fields'}), 400
    
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Username already exists'}), 400
    
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already exists'}), 400
    
    user = User(
        username=data['username'],
        email=data['email'],
        role='customer'
    )
    user.set_password(data['password'])
    
    db.session.add(user)
    db.session.commit()
    
    session['user_id'] = user.id
    return jsonify({
        'user': {
            'username': user.username,
            'email': user.email,
            'role': user.role
        }
    }), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    
    if not data or not all(k in data for k in ['username', 'password']):
        return jsonify({'error': 'Missing username or password'}), 400
    
    user = User.query.filter_by(username=data['username']).first()
    
    if not user or not user.check_password(data['password']):
        return jsonify({'error': 'Invalid username or password'}), 401
    
    session['user_id'] = user.id
    return jsonify({
        'user': {
            'username': user.username,
            'email': user.email,
            'role': user.role
        }
    })

@app.route('/logout', methods=['POST'])
def logout():
    session.pop('user_id', None)
    return jsonify({'message': 'Logged out successfully'})

@app.route('/check_login', methods=['GET'])
def check_login():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        if user:
            return jsonify({
                'user': {
                    'username': user.username,
                    'email': user.email,
                    'role': user.role
                }
            })
    return jsonify({'error': 'Not logged in'}), 401

# Message Routes
@app.route('/messages', methods=['GET'])
def get_messages():
    messages = Message.query.order_by(Message.created_at.desc()).all()
    return jsonify([{
        'id': m.id,
        'content': m.content,
        'author_name': m.author_name,
        'created_at': m.created_at.isoformat()
    } for m in messages])

@app.route('/messages', methods=['POST'])
def create_message():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json()
    
    if not data or 'content' not in data:
        return jsonify({'error': 'Message content is required'}), 400
    
    message = Message(
        content=data['content'],
        author_name=data.get('author_name', 'Anonymous')
    )
    db.session.add(message)
    db.session.commit()
    
    return jsonify({
        'id': message.id,
        'content': message.content,
        'author_name': message.author_name,
        'created_at': message.created_at.isoformat()
    }), 201

@app.route('/messages/<int:message_id>', methods=['DELETE'])
def delete_message(message_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    message = Message.query.get_or_404(message_id)
    db.session.delete(message)
    db.session.commit()
    return jsonify({'message': 'Message deleted successfully'})

# Car Routes
@app.route('/api/vehicles', methods=['GET'])
def get_vehicles():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
        
    # Get filter parameters
    fuel_type = request.args.get('fuel_type')
    
    # Base query - filter by logged-in user
    query = UserCar.query.filter_by(user_id=session['user_id'])
    
    # Apply filters if provided
    if fuel_type and fuel_type.lower() != 'all':
        query = query.filter(UserCar.fuel_type == fuel_type)
    
    # Get user's cars
    cars = query.all()
    
    return jsonify([{
        'id': car.id,
        'company': car.company,
        'model': car.model,
        'year': car.year,
        'price': car.price,
        'mileage': car.mileage,
        'fuel_type': car.fuel_type,
        'transmission': car.transmission,
        'image_url': car.image_url,
        'created_at': car.created_at.isoformat()
    } for car in cars]), 200

@app.route('/api/vehicles', methods=['POST'])
def add_vehicle():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json()
    required_fields = ['company', 'model', 'year', 'price', 'mileage', 'fuel_type', 'transmission']
    
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
    
    new_car = UserCar(
        user_id=session['user_id'],
        company=data['company'],
        model=data['model'],
        year=data['year'],
        price=float(data['price']),
        mileage=float(data['mileage']),
        fuel_type=data['fuel_type'],
        transmission=data['transmission'],
        image_url=data.get('image_url'),
        type=data.get('type') or 'car',
        color=data.get('color'),
        registration_number=data.get('registration_number'),
        purchase_date=data.get('purchase_date')
    )
    
    db.session.add(new_car)
    db.session.commit()
    
    return jsonify({
        'id': new_car.id,
        'message': 'Vehicle added successfully'
    }), 201

@app.route('/api/vehicles/<int:vehicle_id>', methods=['PUT'])
def update_vehicle(vehicle_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    car = UserCar.query.filter_by(id=vehicle_id, user_id=session['user_id']).first()
    
    if not car:
        return jsonify({'message': 'Vehicle not found'}), 404
    
    data = request.get_json()
    
    # Update only the fields that are provided
    if 'company' in data:
        car.company = data['company']
    if 'model' in data:
        car.model = data['model']
    if 'year' in data:
        car.year = data['year']
    if 'price' in data:
        car.price = float(data['price'])
    if 'mileage' in data:
        car.mileage = float(data['mileage'])
    if 'fuel_type' in data:
        car.fuel_type = data['fuel_type']
    if 'transmission' in data:
        car.transmission = data['transmission']
    if 'image_url' in data:
        car.image_url = data['image_url']
    
    db.session.commit()
    return jsonify({'message': 'Vehicle updated successfully'}), 200

@app.route('/api/vehicles/<int:vehicle_id>', methods=['DELETE'])
def delete_vehicle(vehicle_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    car = UserCar.query.filter_by(id=vehicle_id, user_id=session['user_id']).first()
    
    if not car:
        return jsonify({'message': 'Vehicle not found'}), 404
    
    db.session.delete(car)
    db.session.commit()
    return jsonify({'message': 'Vehicle deleted successfully'}), 200

@app.route('/api/marketplace/vehicles', methods=['GET'])
def get_marketplace_vehicles():
    # Get filter parameters
    fuel_type = request.args.get('fuel_type')
    
    # Base query - show all vehicles available for sale
    query = UserCar.query
    
    # Apply filters if provided
    if fuel_type and fuel_type.lower() != 'all':
        query = query.filter(UserCar.fuel_type == fuel_type)
    
    # Get all cars
    cars = query.all()
    
    return jsonify([{
        'id': car.id,
        'company': car.company,
        'model': car.model,
        'year': car.year,
        'price': car.price,
        'mileage': car.mileage,
        'fuel_type': car.fuel_type,
        'transmission': car.transmission,
        'image_url': car.image_url,
        'created_at': car.created_at.isoformat()
    } for car in cars]), 200

# Trip and Emission Routes
@app.route('/trips', methods=['POST'])
def create_trip():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json()
    required_fields = ['start_location', 'end_location', 'distance', 'start_time', 'end_time', 'vehicle_id']
    
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
    
    try:
        new_trip = Trip(
            user_id=session['user_id'],
            start_location=data['start_location'],
            end_location=data['end_location'],
            distance=float(data['distance']),
            start_time=datetime.fromisoformat(data['start_time']),
            end_time=datetime.fromisoformat(data['end_time']),
            vehicle_id=data['vehicle_id']
        )
        
        db.session.add(new_trip)
        db.session.commit()
        
        return jsonify({
            'id': new_trip.id,
            'message': 'Trip recorded successfully'
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@app.route('/trips', methods=['GET'])
def get_user_trips():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    trips = Trip.query.filter_by(user_id=session['user_id']).order_by(Trip.created_at.desc()).all()
    return jsonify([{
        'id': trip.id,
        'start_location': trip.start_location,
        'end_location': trip.end_location,
        'distance': trip.distance,
        'start_time': trip.start_time.isoformat(),
        'end_time': trip.end_time.isoformat(),
        'vehicle': {
            'id': trip.vehicle.id,
            'model': trip.vehicle.model,
            'company': trip.vehicle.company
        },
        'emissions': trip.emission_record.co2_emissions if trip.emission_record else None
    } for trip in trips])

@app.route('/emissions', methods=['POST'])
def record_emissions():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json()
    required_fields = ['trip_id', 'vehicle_id', 'co2_emissions', 'distance', 'fuel_consumed', 'record_date']
    
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
    
    try:
        new_emission = EmissionRecord(
            trip_id=data.get('trip_id'),
            user_id=session['user_id'],
            vehicle_id=data['vehicle_id'],
            co2_emissions=float(data['co2_emissions']),
            distance=float(data['distance']),
            fuel_consumed=float(data['fuel_consumed']),
            record_date=datetime.fromisoformat(data['record_date']).date()
        )
        
        db.session.add(new_emission)
        db.session.commit()
        
        return jsonify({
            'id': new_emission.id,
            'message': 'Emission record created successfully'
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@app.route('/emissions', methods=['GET'])
def get_user_emissions():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    emissions = EmissionRecord.query.filter_by(user_id=session['user_id']).order_by(EmissionRecord.record_date.desc()).all()
    return jsonify([{
        'id': record.id,
        'trip_id': record.trip_id,
        'co2_emissions': record.co2_emissions,
        'distance': record.distance,
        'fuel_consumed': record.fuel_consumed,
        'record_date': record.record_date.isoformat(),
        'vehicle': {
            'id': record.vehicle.id,
            'model': record.vehicle.model,
            'company': record.vehicle.company
        }
    } for record in emissions])

# Community Routes
@app.route('/posts', methods=['POST'])
def create_post():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json()
    required_fields = ['title', 'content', 'post_type']
    
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
    
    if data['post_type'] not in ['discussion', 'achievement', 'question', 'tip']:
        return jsonify({'error': 'Invalid post type'}), 400
    
    try:
        new_post = CommunityPost(
            user_id=session['user_id'],
            title=data['title'],
            content=data['content'],
            post_type=data['post_type']
        )
        
        db.session.add(new_post)
        db.session.commit()
        
        return jsonify({
            'id': new_post.id,
            'message': 'Post created successfully'
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@app.route('/posts', methods=['GET'])
def get_posts():
    posts = CommunityPost.query.order_by(CommunityPost.created_at.desc()).all()
    return jsonify([{
        'id': post.id,
        'title': post.title,
        'content': post.content,
        'post_type': post.post_type,
        'likes': post.likes,
        'views': post.views,
        'created_at': post.created_at.isoformat(),
        'author': {
            'id': post.user.id,
            'username': post.user.username
        },
        'comments_count': post.comments.count()
    } for post in posts])

@app.route('/posts/<int:post_id>', methods=['GET'])
def get_single_post(post_id):
    post = CommunityPost.query.get_or_404(post_id)
    
    # Increment views counter
    post.views += 1
    db.session.commit()
    
    return jsonify({
        'id': post.id,
        'title': post.title,
        'content': post.content,
        'post_type': post.post_type,
        'likes': post.likes,
        'views': post.views,
        'created_at': post.created_at.isoformat(),
        'author': {
            'id': post.user.id,
            'username': post.user.username
        },
        'comments_count': post.comments.count()
    })

@app.route('/posts/<int:post_id>/comments', methods=['POST'])
def add_comment(post_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json()
    if not data or 'content' not in data:
        return jsonify({'error': 'Comment content is required'}), 400
    
    try:
        new_comment = PostComment(
            post_id=post_id,
            user_id=session['user_id'],
            content=data['content']
        )
        
        db.session.add(new_comment)
        db.session.commit()
        
        return jsonify({
            'id': new_comment.id,
            'message': 'Comment added successfully'
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@app.route('/posts/<int:post_id>/comments', methods=['GET'])
def get_comments(post_id):
    comments = PostComment.query.filter_by(post_id=post_id).order_by(PostComment.created_at.asc()).all()
    
    # Debug: Print current user session
    current_user_id = session.get('user_id')
    print(f"Current user ID in session: {current_user_id}")
    
    comment_list = []
    for comment in comments:
        comment_data = {
            'id': comment.id,
            'content': comment.content,
            'likes': comment.likes,
            'created_at': comment.created_at.isoformat(),
            'author': {
                'id': comment.user.id,
                'username': comment.user.username
            }
        }
        comment_list.append(comment_data)
        print(f"Comment {comment.id}: author_id={comment.user.id}, current_user_id={current_user_id}")
    
    return jsonify(comment_list)

@app.route('/posts/<int:post_id>/like', methods=['POST'])
def like_post(post_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    post = CommunityPost.query.get_or_404(post_id)
    post.likes += 1
    db.session.commit()
    
    return jsonify({'message': 'Post liked successfully'})

@app.route('/comments/<int:comment_id>/like', methods=['POST'])
def like_comment(comment_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    comment = PostComment.query.get_or_404(comment_id)
    comment.likes += 1
    db.session.commit()
    
    return jsonify({'message': 'Comment liked successfully'})

@app.route('/comments/<int:comment_id>', methods=['DELETE'])
def delete_comment(comment_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    comment = PostComment.query.get_or_404(comment_id)
    
    # Check if the user is the author of the comment
    if comment.user_id != session['user_id']:
        return jsonify({'error': 'You can only delete your own comments'}), 403
    
    db.session.delete(comment)
    db.session.commit()
    
    return jsonify({'message': 'Comment deleted successfully'})

# Add CORS headers
@app.after_request
def after_request(response):
    origin = request.headers.get('Origin')
    if origin in ["http://localhost:8000", "http://127.0.0.1:8000", "http://127.0.0.1:5000"]:
        response.headers.add('Access-Control-Allow-Origin', origin)
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response

def init_db():
    with app.app_context():
        db.create_all()

if __name__ == '__main__':
    init_db()  # Initialize the database when starting the app
    app.run(debug=True)