import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads', 'profile_images')
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Модель пользователя
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    avatar = db.Column(db.String(255), nullable=True)
    bio = db.Column(db.String(600), nullable=True)

    def __repr__(self):
        return '<User %r>' % self.id

# Модель дневника
class Day(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    intro = db.Column(db.String(100), nullable=False)
    text = db.Column(db.String(6000), nullable=False)

    def __repr__(self):
        return '<Day %r>' % self.id

# Функция проверки расширения файла
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Загружаем пользователя по ID
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Создаем папку для загрузки аватаров
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Регистрация
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        avatar_file = request.files.get('avatar')

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Пользователь с таким именем уже существует.', 'danger')
            return render_template('register.html', username=username)

        avatar_filename = None
        if avatar_file and allowed_file(avatar_file.filename):
            filename = secure_filename(avatar_file.filename)
            avatar_filename = f"{username}_{filename}"
            avatar_path = os.path.join(app.config['UPLOAD_FOLDER'], avatar_filename)
            avatar_file.save(avatar_path)

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        new_user = User(username=username, password=hashed_password, avatar=avatar_filename)
        db.session.add(new_user)
        db.session.commit()

        flash('Регистрация успешна! Теперь вы можете войти.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

# Вход
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            flash('Авторизация успешна!', 'success')
            return redirect(url_for('main'))
        else:
            flash('Неверное имя пользователя или пароль', 'danger')
            return render_template('login.html', username=username)
    return render_template('login.html')

# Выход
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы вышли из системы.', 'info')
    return redirect(url_for('login'))

# Главная страница
@app.route('/')
@login_required
def main():
    return render_template('index.html')

# Создать запись
@app.route('/createZapis', methods=['GET', 'POST'])
@login_required
def createZapis():
    if request.method == 'POST':
        intro = request.form['intro']
        text = request.form['description']
        new_article = Day(intro=intro, text=text)
        db.session.add(new_article)
        db.session.commit()
        # Используйте url_for с именем функции
        return redirect(url_for('allZapis'))
    return render_template('newZapis.html')

# Профиль
@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    user = current_user
    if request.method == 'POST':
        if 'file' in request.files:
            file = request.files['file']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                avatar_filename = f"{user.username}_{filename}"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], avatar_filename)
                try:
                    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                    file.save(filepath)
                    user.avatar = avatar_filename
                    db.session.commit()
                    flash('Аватар успешно обновлен!', 'success')
                except Exception as e:
                    print(e)
                    flash('Ошибка при загрузке аватара.', 'error')
            else:
                flash('Пожалуйста, выберите допустимый файл изображения.', 'error')
        else:
            flash('Файл не был отправлен.', 'error')
    return render_template('profile.html', user=user)

# Маршрут для отображения всех записей (замените название функции на 'allZapis')
@app.route('/oldZapis')
@login_required
def allZapis():
    day_user = Day.query.all()
    return render_template('allZapis.html', day_user=day_user)

# Обновление информации о записи
@app.route('/updatesInfo', methods=['GET', 'POST'])
@login_required
def updatesInfo():
    if request.method == 'POST':
        username = request.form['username']
        bio = request.form['bio']
        email = request.form['email']

        # Обновляем текущего пользователя
        current_user.username = username
        current_user.bio = bio
        current_user.email = email

        try:
            db.session.commit()
            flash('Данные успешно обновлены', 'success')
        except Exception as e:
            db.session.rollback()
            flash('Ошибка при сохранении данных: ' + str(e), 'danger')

        return redirect(url_for('profile'))

    # Перед отображением формы — передаем текущие данные
    return render_template('updatesInfo.html', user=current_user)

# Детали записи
@app.route('/infoZapis/<int:id>')
@login_required
def infoZapis(id):
    day = Day.query.get(id)
    return render_template('infoZapis.html', day=day)

# Удаление записи
@app.route('/zapisDel/<int:id>')
@login_required
def zapisDel(id):
    dayDel = Day.query.get(id)
    if dayDel:
        db.session.delete(dayDel)
        db.session.commit()
    return redirect(url_for('allZapis'))  # используем название функции 'allZapis'

# Редактировать запись
@app.route('/zapisRedect/<int:id>', methods=['POST', 'GET'])
@login_required
def zapisRedect(id):
    print(f"ID полученный в zapisRedect: {id}")  # Отладка

    dayRedect = Day.query.get_or_404(id)
    print(f"Запись найдена: {dayRedect}")  # Отладка

    if request.method == 'POST':
        dayRedect.intro = request.form['intro']
        dayRedect.text = request.form['text']
        db.session.commit()
        return redirect(url_for('allZapis'))  # используем название функции 'allZapis'
    else:
        return render_template('dayRedect.html', dayRedect=dayRedect)
@app.route('/info')
def info ():
    return render_template('informatitoon.html')
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)