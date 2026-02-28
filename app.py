from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, Admin, Labour, Public, Feedback, Message, WorkShowcase
from werkzeug.utils import secure_filename
import os
from sqlalchemy import func

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hire_labour.db'
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'uploads')

db.init_app(app)
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

# Translations Dictionary
TRANSLATIONS = {
    'en': {
        'welcome': 'Welcome to Hire Labour!',
        'description': 'Find skilled labour for your needs, or register as labour to offer your services.',
        'signup_public': 'Sign up as Public',
        'signup_labour': 'Sign up as Labour',
        'search_labour': 'Search for Labour',
        'recent_labour': 'Recently Registered Labourers',
        'login': 'Login',
        'register': 'Register',
        'logout': 'Logout',
        'admin_panel': 'Admin Panel',
        'dashboard': 'Dashboard',
        'manage_labours': 'Manage Labours',
        'manage_publics': 'Manage Publics'
    },
    'kn': { 'welcome': 'ಹೈರ್ ಲೇಬರ್ ಸ್ವಾಗತ!', 'description': 'ನಿಮ್ಮ ಅಗತ್ಯಗಳಿಗಾಗಿ ನುರಿತ ಕಾರ್ಮಿಕರನ್ನು ಹುಡುಕಿ.', 'signup_public': 'ಸಾರ್ವಜನಿಕವಾಗಿ ನೋಂದಾಯಿಸಿ', 'signup_labour': 'ಕಾರ್ಮಿಕರಾಗಿ ನೋಂದಾಯಿಸಿ', 'login': 'ಲಾಗಿನ್', 'logout': 'ಲಾಗೌಟ್' },
    'hi': { 'welcome': 'हायर लेबर में आपका स्वागत है!', 'description': 'अपनी जरूरतों के लिए कुशल श्रमिक खोजें।', 'signup_public': 'पब्लिक के रूप में जुड़ें', 'signup_labour': 'लेबर के रूप में जुड़ें', 'login': 'लॉगिन', 'logout': 'लॉगआउट' },
    'ta': { 'welcome': 'ஹையர் லேபருக்கு வரவேற்கிறோம்!', 'description': 'உங்கள் தேவைகளுக்கு திறமையான தொழிலாளர்களைக் கண்டறியவும்.', 'signup_public': 'பொதுமக்களாக பதிவு செய்யவும்', 'signup_labour': 'தொழிலாளியாக பதிவு செய்யவும்', 'login': 'உள்நுழை', 'logout': 'வெளியேறு' },
    'te': { 'welcome': 'హైర్ లేబర్‌కు స్వాగతం!', 'description': 'మీ అవసరాల కోసం నైపుణ్యం కలిగిన కార్మికులను కనుగొనండి.', 'signup_public': 'పబ్లిక్ గా నమోదు చేసుకోండి', 'signup_labour': 'కార్మికునిగా నమోదు చేసుకోండి', 'login': 'లాగిన్', 'logout': 'లాగౌట్' },
    'ml': { 'welcome': 'ഹയർ ലേബറിലേക്ക് സ്വാഗതം!', 'description': 'നിങ്ങളുടെ ആവശ്യങ്ങൾക്കായി വിദഗ്ധ തൊഴിലാളികളെ കണ്ടെത്തുക.', 'signup_public': 'പൊതുജനമായി രജിസ്റ്റർ ചെയ്യുക', 'signup_labour': 'തൊഴിലാളിയായി രജിസ്റ്റർ ചെയ്യുക', 'login': 'ലോഗിൻ', 'logout': 'ലോഗ്ഔട്ട്' },
    'mr': { 'welcome': 'हायर लेबरमध्ये स्वागत आहे!', 'description': 'तुमच्या गरजांसाठी कुशल कामगार शोधा.', 'signup_public': 'सार्वजनिक म्हणून नोंदणी करा', 'signup_labour': 'कामगार म्हणून नोंदणी करा', 'login': 'लॉगिन', 'logout': 'लॉगआउट' }
}

@login_manager.user_loader
def load_user(user_id):
    try:
        if user_id.startswith('admin_'):
            return Admin.query.get(int(user_id.split('_')[1]))
        elif user_id.startswith('labour_'):
            return Labour.query.get(int(user_id.split('_')[1]))
        elif user_id.startswith('public_'):
            return Public.query.get(int(user_id.split('_')[1]))
    except:
        return None
    return None

@app.context_processor
def inject_lang():
    lang = session.get('lang', 'en')
    return dict(lang=lang, t=TRANSLATIONS.get(lang, TRANSLATIONS['en']))

@app.route('/set_lang/<lang>')
def set_lang(lang):
    session['lang'] = lang
    return redirect(request.referrer or url_for('index'))

@app.errorhandler(404)
def page_not_found(e):
    print(f"DEBUG: 404 Error - Path hit: {request.path}")
    return "Custom 404: Route Not Found in Flask App", 404

@app.route('/')
def index():
    print("DEBUG: Index route hit")
    recent_labours = Labour.query.order_by(Labour.registration_date.desc()).limit(5).all()
    top_rated = db.session.query(
        Labour, func.avg(Feedback.rating).label('average_rating')
    ).join(Feedback).group_by(Labour.labour_id).order_by(func.avg(Feedback.rating).desc()).limit(3).all()
    return render_template('index.html', recent_labours=recent_labours, top_rated=top_rated)

@app.route('/login', methods=['GET', 'POST'])
def login():
    print(f"DEBUG: Login route hit with method {request.method}")
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role')

        user = None
        if role == 'admin':
            user = Admin.query.filter_by(username=username, password=password).first()
        elif role == 'labour':
            user = Labour.query.filter_by(username=username, password=password).first()
        elif role == 'public':
            user = Public.query.filter_by(username=username, password=password).first()

        if user:
            login_user(user)
            session['user_role'] = role
            flash('Logged in successfully!', 'success')
            if role == 'labour':
                return redirect(url_for('labour_dashboard'))
            elif role == 'public':
                return redirect(url_for('public_dashboard'))
            elif role == 'admin':
                return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid username or password', 'danger')

    return render_template('login.html')

@app.route('/register_public', methods=['GET', 'POST'])
def register_public():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        
        # Check if username or email already exists
        if Public.query.filter((Public.username == username) | (Public.email == email)).first():
            flash('Username or Email already exists!', 'danger')
            return redirect(url_for('register_public'))

        new_user = Public(
            username=username,
            password=request.form.get('password'),
            full_name=request.form.get('full_name'),
            email=email,
            phone=request.form.get('phone')
        )
        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Public account created!', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred. Please try again.', 'danger')
            
    return render_template('register_public.html')

@app.route('/register_labour', methods=['GET', 'POST'])
def register_labour():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')

        # Check if username or email already exists
        if Labour.query.filter((Labour.username == username) | (Labour.email == email)).first():
            flash('Username or Email already exists!', 'danger')
            return redirect(url_for('register_labour'))

        new_user = Labour(
            username=username,
            password=request.form.get('password'),
            full_name=request.form.get('full_name'),
            email=email,
            phone=request.form.get('phone'),
            service_offered=request.form.get('service_offered'),
            address=request.form.get('address')
        )
        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Labour account created!', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred. Please try again.', 'danger')

    return render_template('register_labour.html')

@app.route('/public_dashboard')
@login_required
def public_dashboard():
    service = request.args.get('service', '')
    results = Labour.query.filter(Labour.service_offered.ilike(f'%{service}%')).all() if service else []
    recommendations = db.session.query(
        Labour, func.avg(Feedback.rating).label('avg_rating')
    ).join(Feedback).filter(Labour.service_offered.ilike(f'%{service}%'))\
    .group_by(Labour.labour_id).order_by(func.avg(Feedback.rating).desc()).limit(3).all() if service else []
    return render_template('public_dashboard.html', results=results, service=service, recommendations=recommendations)

@app.route('/labour_dashboard')
@login_required
def labour_dashboard():
    if session.get('user_role') != 'labour':
        return redirect(url_for('index'))
    feedbacks = Feedback.query.filter_by(labour_id=current_user.labour_id).all()
    showcase = WorkShowcase.query.filter_by(labour_id=current_user.labour_id).all()
    return render_template('labour_dashboard.html', user=current_user, feedbacks=feedbacks, showcase=showcase)

@app.route('/view_labour/<int:id>')
@login_required
def view_labour(id):
    labour = Labour.query.get_or_404(id)
    feedbacks = Feedback.query.filter_by(labour_id=id).all()
    showcase = WorkShowcase.query.filter_by(labour_id=id).all()
    return render_template('view_labour.html', labour=labour, feedbacks=feedbacks, showcase=showcase)

@app.route('/admin_dashboard')
@login_required
def admin_dashboard():
    if session.get('user_role') != 'admin':
        return redirect(url_for('index'))
    return render_template('admin/dashboard.html', labour_count=Labour.query.count(), public_count=Public.query.count(), feedback_count=Feedback.query.count())

@app.route('/admin/manage_labours')
@login_required
def manage_labours():
    if session.get('user_role') != 'admin':
        return redirect(url_for('index'))
    return render_template('admin/manage_labours.html', labours=Labour.query.all())

@app.route('/admin/manage_publics')
@login_required
def manage_publics():
    if session.get('user_role') != 'admin':
        return redirect(url_for('index'))
    return render_template('admin/manage_publics.html', publics=Public.query.all())

@app.route('/admin/delete_user/<string:type>/<int:id>')
@login_required
def delete_user(type, id):
    if session.get('user_role') != 'admin':
        return redirect(url_for('index'))
    if type == 'labour':
        user = Labour.query.get(id)
        if user:
            Feedback.query.filter_by(labour_id=id).delete()
            db.session.delete(user)
            db.session.commit()
            flash('Labourer deleted successfully', 'success')
        return redirect(url_for('manage_labours'))
    elif type == 'public':
        user = Public.query.get(id)
        if user:
            Feedback.query.filter_by(public_id=id).delete()
            db.session.delete(user)
            db.session.commit()
            flash('Public user deleted successfully', 'success')
        return redirect(url_for('manage_publics'))
    return redirect(url_for('admin_dashboard'))

@app.route('/submit_feedback', methods=['POST'])
@login_required
def submit_feedback():
    if session.get('user_role') != 'public':
        flash('Only public users can give feedback', 'danger')
        return redirect(url_for('index'))
    new_fb = Feedback(public_id=current_user.public_id, labour_id=request.form.get('labour_id'), rating=request.form.get('rating'), comment=request.form.get('comment'))
    db.session.add(new_fb)
    db.session.commit()
    flash('Feedback submitted!', 'success')
    return redirect(url_for('view_labour', id=request.form.get('labour_id')))

@app.route('/upload_work', methods=['POST'])
@login_required
def upload_work():
    if session.get('user_role') != 'labour':
        return redirect(url_for('index'))
    
    if 'work_image' not in request.files:
        flash('No file part', 'danger')
        return redirect(url_for('labour_dashboard'))
    
    file = request.files['work_image']
    if file.filename == '':
        flash('No selected file', 'danger')
        return redirect(url_for('labour_dashboard'))
    
    if file:
        filename = secure_filename(file.filename)
        # Add timestamp to filename to prevent collisions
        import time
        filename = f"{int(time.time())}_{filename}"
        
        if not os.path.exists(app.config['UPLOAD_FOLDER']):
            os.makedirs(app.config['UPLOAD_FOLDER'])
            
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        
        new_showcase = WorkShowcase(
            labour_id=current_user.labour_id,
            image_path=filename,
            description=request.form.get('description')
        )
        db.session.add(new_showcase)
        db.session.commit()
        flash('Work image uploaded successfully!', 'success')
        
    return redirect(url_for('labour_dashboard'))

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    from flask import send_from_directory
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/upload_profile', methods=['POST'])
@login_required
def upload_profile():
    if 'profile_image' not in request.files:
        flash('No file part', 'danger')
        return redirect(request.referrer)
    
    file = request.files['profile_image']
    if file.filename == '':
        flash('No selected file', 'danger')
        return redirect(request.referrer)
    
    if file:
        filename = secure_filename(file.filename)
        import time
        filename = f"profile_{int(time.time())}_{filename}"
        
        if not os.path.exists(app.config['UPLOAD_FOLDER']):
            os.makedirs(app.config['UPLOAD_FOLDER'])
            
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        
        role = session.get('user_role')
        if role == 'labour':
            current_user.profile_image = filename
        elif role == 'public':
            current_user.profile_image = filename
            
        db.session.commit()
        flash('Profile picture updated!', 'success')
        
    return redirect(request.referrer)

@app.route('/chat/<int:labour_id>')
@login_required
def chat(labour_id):
    role = session.get('user_role')
    if role == 'public':
        public_id = current_user.public_id
        labour = Labour.query.get_or_404(labour_id)
        messages = Message.query.filter_by(public_id=public_id, labour_id=labour_id).order_by(Message.timestamp).all()
        return render_template('chat.html', messages=messages, target=labour, target_role='labour')
    elif role == 'labour':
        # If labour is viewing, they need a public_id from args
        public_id = request.args.get('public_id', type=int)
        if not public_id:
            return redirect(url_for('messages'))
        public = Public.query.get_or_404(public_id)
        messages = Message.query.filter_by(public_id=public_id, labour_id=current_user.labour_id).order_by(Message.timestamp).all()
        # Mark as read
        for m in messages:
            if m.receiver_type == 'labour' and m.receiver_id == current_user.labour_id:
                m.is_read = True
        db.session.commit()
        return render_template('chat.html', messages=messages, target=public, target_role='public')
    return redirect(url_for('index'))

@app.route('/send_message', methods=['POST'])
@login_required
def send_message():
    role = session.get('user_role')
    content = request.form.get('content')
    if not content:
        return redirect(request.referrer)

    if role == 'public':
        labour_id = request.form.get('labour_id', type=int)
        new_msg = Message(
            sender_type='public',
            sender_id=current_user.public_id,
            receiver_type='labour',
            receiver_id=labour_id,
            public_id=current_user.public_id,
            labour_id=labour_id,
            content=content
        )
    elif role == 'labour':
        public_id = request.form.get('public_id', type=int)
        new_msg = Message(
            sender_type='labour',
            sender_id=current_user.labour_id,
            receiver_type='public',
            receiver_id=public_id,
            public_id=public_id,
            labour_id=current_user.labour_id,
            content=content
        )
    else:
        return redirect(url_for('index'))

    db.session.add(new_msg)
    db.session.commit()
    return redirect(request.referrer)

@app.route('/messages')
@login_required
def messages():
    role = session.get('user_role')
    if role == 'public':
        # Get all labours this public has messaged
        chats = db.session.query(Message.labour_id).filter_by(public_id=current_user.public_id).distinct().all()
        chat_partners = [Labour.query.get(c[0]) for c in chats]
        return render_template('messages.html', chat_partners=chat_partners, role='public')
    elif role == 'labour':
        # Get all publics this labour has messaged
        chats = db.session.query(Message.public_id).filter_by(labour_id=current_user.labour_id).distinct().all()
        chat_partners = [Public.query.get(c[0]) for c in chats]
        return render_template('messages.html', chat_partners=chat_partners, role='labour')
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    logout_user()
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        if not Admin.query.first():
            db.session.add_all([Admin(username='admin', password='admin123'), Public(username='raj', password='password', full_name='Raj Kumar', email='raj@example.com', phone='1234567890'), Labour(username='pavan', password='password', full_name='Pavan Kumar', email='pavan@example.com', phone='9353600120', service_offered='Plumbing', address='BIET Road')])
            db.session.commit()
    app.run(host='0.0.0.0', port=5000, debug=True)
