from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from functools import wraps

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///dnevnik.db'
app.config['SECRET_KEY'] = 'your_secret_key'  # Важно для session и flash
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

class Day(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    intro = db.Column(db.String(100), nullable=False)
    text = db.Column(db.String(6000), nullable=False)

    def __repr__(self):
        return '<Day %r>' % self.id

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)

# Декоратор для проверки авторизации
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('user_id') is None:
            flash('Требуется авторизация для доступа к этой странице.', 'warning')
            return redirect(url_for('login')) # Исправлено: перенаправляем на login
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
@login_required  # Защищаем маршрут main
def main():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST']) #Изменено: корректное имя маршрута
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Пользователь с таким именем уже существует.', 'danger')
            return render_template('register.html', username=username) # Возвращаем шаблон регистрации с данными

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash('Регистрация успешна! Теперь вы можете войти.', 'success') # сообщение об успешной регистрации
        return redirect(url_for('login')) # Перенаправление на страницу входа

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and bcrypt.check_password_hash(user.password, password):
            session['user_id'] = user.id
            flash('Авторизация успешна!', 'success')
            return redirect(url_for('main')) # Перенаправление на главную страницу
        else:
            flash('Неверное имя пользователя или пароль', 'danger')
            return render_template('login.html', username=username) #Возвращаем шаблон входа с сообщением об ошибке и данными

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    session.pop('user_id', None)
    flash('Вы вышли из системы.', 'info')
    return redirect(url_for('login'))

if __name__ == '__main__':
    with app.app_context(): # Добавлено: Создаем контекст приложения
        db.create_all()
    app.run(debug=True)