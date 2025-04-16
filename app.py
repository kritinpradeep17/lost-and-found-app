from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user, login_user, logout_user, login_required, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
import os

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()

# Define models
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    lost_items = db.relationship('LostItem', backref='owner', lazy=True)
    found_items = db.relationship('FoundItem', backref='finder', lazy=True)

class LostItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    location = db.Column(db.String(100), nullable=False)
    date_lost = db.Column(db.Date, nullable=False)
    image = db.Column(db.String(100))
    status = db.Column(db.String(20), default='lost')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class FoundItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    location = db.Column(db.String(100), nullable=False)
    date_found = db.Column(db.Date, nullable=False)
    image = db.Column(db.String(100))
    status = db.Column(db.String(20), default='found')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')
    
    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    
    with app.app_context():
        db.create_all()
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    def allowed_file(filename):
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']
    
    def save_uploaded_file(file):
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            upload_folder = app.config['UPLOAD_FOLDER']
            os.makedirs(upload_folder, exist_ok=True)
            filepath = os.path.join(upload_folder, filename)
            file.save(filepath)
            return filename
        return None
    
    @app.route('/')
    def index():
        recent_lost = LostItem.query.filter_by(status='lost').order_by(LostItem.created_at.desc()).limit(5).all()
        recent_found = FoundItem.query.filter_by(status='found').order_by(FoundItem.created_at.desc()).limit(5).all()
        return render_template('index.html', recent_lost=recent_lost, recent_found=recent_found)

    # Auth Routes
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if request.method == 'POST':
            username = request.form.get('username')
            email = request.form.get('email')
            password = request.form.get('password')
            confirm_password = request.form.get('confirm_password')
            
            if password != confirm_password:
                flash('Passwords do not match!', 'danger')
                return redirect(url_for('register'))
            
            existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
            if existing_user:
                flash('Username or email already exists!', 'danger')
                return redirect(url_for('register'))
            
            new_user = User(
                username=username,
                email=email,
                password=generate_password_hash(password)
            )
            
            db.session.add(new_user)
            db.session.commit()
            
            flash('Account created successfully! Please login.', 'success')
            return redirect(url_for('login'))
        
        return render_template('auth/register.html')

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            email = request.form.get('email')
            password = request.form.get('password')
            remember = True if request.form.get('remember') else False
            
            user = User.query.filter_by(email=email).first()
            
            if not user or not check_password_hash(user.password, password):
                flash('Please check your login details and try again.', 'danger')
                return redirect(url_for('login'))
            
            login_user(user, remember=remember)
            return redirect(url_for('index'))
        
        return render_template('auth/login.html')

    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        return redirect(url_for('index'))

    @app.route('/reset-password', methods=['GET', 'POST'])
    def reset_password():
        if request.method == 'POST':
            email = request.form.get('email')
            user = User.query.filter_by(email=email).first()
            
            if user:
                # In production: Send email with reset link
                flash('If an account exists with this email, a reset link has been sent.', 'info')
            else:
                # Don't reveal if email doesn't exist (security)
                flash('If an account exists with this email, a reset link has been sent.', 'info')
            
            return redirect(url_for('login'))
        
        return render_template('auth/reset.html')

    # Item Routes
    @app.route('/items/lost', methods=['GET', 'POST'])
    @login_required
    def report_lost():
        if request.method == 'POST':
            name = request.form.get('name')
            description = request.form.get('description')
            location = request.form.get('location')
            date_lost = datetime.strptime(request.form.get('date_lost'), '%Y-%m-%d').date()
            
            image = None
            if 'image' in request.files:
                image = save_uploaded_file(request.files['image'])
            
            new_lost_item = LostItem(
                name=name,
                description=description,
                location=location,
                date_lost=date_lost,
                image=image,
                user_id=current_user.id
            )
            
            db.session.add(new_lost_item)
            db.session.commit()
            
            flash('Lost item reported successfully!', 'success')
            return redirect(url_for('search_items'))
        
        return render_template('items/lost.html')

    @app.route('/items/found', methods=['GET', 'POST'])
    @login_required
    def report_found():
        if request.method == 'POST':
            name = request.form.get('name')
            description = request.form.get('description')
            location = request.form.get('location')
            date_found = datetime.strptime(request.form.get('date_found'), '%Y-%m-%d').date()
            
            image = None
            if 'image' in request.files:
                image = save_uploaded_file(request.files['image'])
            
            new_found_item = FoundItem(
                name=name,
                description=description,
                location=location,
                date_found=date_found,
                image=image,
                user_id=current_user.id
            )
            
            db.session.add(new_found_item)
            db.session.commit()
            
            flash('Found item reported successfully!', 'success')
            return redirect(url_for('search_items'))
        
        return render_template('items/found.html')

    @app.route('/items/search')
    def search_items():
        query = request.args.get('query', '')
        location = request.args.get('location', '')
        date = request.args.get('date', '')
        item_type = request.args.get('type', 'all')
        
        lost_items = []
        found_items = []
        
        if item_type in ['all', 'lost']:
            lost_query = LostItem.query.filter(LostItem.status == 'lost')
            if query:
                lost_query = lost_query.filter(
                    (LostItem.name.ilike(f'%{query}%')) | 
                    (LostItem.description.ilike(f'%{query}%'))
                )
            if location:
                lost_query = lost_query.filter(LostItem.location.ilike(f'%{location}%'))
            if date:
                try:
                    date_obj = datetime.strptime(date, '%Y-%m-%d').date()
                    lost_query = lost_query.filter(LostItem.date_lost == date_obj)
                except ValueError:
                    pass
            lost_items = lost_query.all()
        
        if item_type in ['all', 'found']:
            found_query = FoundItem.query.filter(FoundItem.status == 'found')
            if query:
                found_query = found_query.filter(
                    (FoundItem.name.ilike(f'%{query}%')) | 
                    (FoundItem.description.ilike(f'%{query}%'))
                )
            if location:
                found_query = found_query.filter(FoundItem.location.ilike(f'%{location}%'))
            if date:
                try:
                    date_obj = datetime.strptime(date, '%Y-%m-%d').date()
                    found_query = found_query.filter(FoundItem.date_found == date_obj)
                except ValueError:
                    pass
            found_items = found_query.all()
        
        return render_template('items/search.html',
                            lost_items=lost_items,
                            found_items=found_items,
                            query=query,
                            location=location,
                            date=date,
                            item_type=item_type)

    @app.route('/items/lost/<int:id>')
    def lost_item_details(id):
        item = LostItem.query.get_or_404(id)
        return render_template('items/details.html', item=item, type='lost')

    @app.route('/items/found/<int:id>')
    def found_item_details(id):
        item = FoundItem.query.get_or_404(id)
        return render_template('items/details.html', item=item, type='found')

    # Profile Routes
    @app.route('/profile')
    @login_required
    def profile():
        return render_template('profile/view.html', user=current_user)

    @app.route('/profile/edit', methods=['GET', 'POST'])
    @login_required
    def edit_profile():
        if request.method == 'POST':
            current_user.username = request.form.get('username')
            current_user.email = request.form.get('email')
            current_user.phone = request.form.get('phone')
            
            db.session.commit()
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('profile'))
        
        return render_template('profile/edit.html', user=current_user)

    @app.route('/profile/delete', methods=['POST'])
    @login_required
    def delete_profile():
        db.session.delete(current_user)
        db.session.commit()
        logout_user()
        flash('Your account has been deleted.', 'info')
        return redirect(url_for('index'))

    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)