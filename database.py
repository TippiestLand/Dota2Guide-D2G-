from sqlalchemy import create_engine, Column, Integer, String, Text, BigInteger, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os
import urllib.parse

DATABASE_URL = os.environ.get('DATABASE_URL')

if DATABASE_URL and DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

if not DATABASE_URL:
    DATABASE_URL = "postgresql://dota2_user:123456@localhost:5432/dota2_guide"

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class News(Base):
    __tablename__ = 'news'
    id = Column(Integer, primary_key=True)
    title = Column(Text, nullable=False)
    content = Column(Text, nullable=False)
    preview = Column(Text)
    type = Column(String, default='update')
    date = Column(String, nullable=False)
    link = Column(String)
    author = Column(String, default='Admin')
    timestamp = Column(BigInteger, nullable=False)
    created_at = Column(DateTime, default=datetime.now)

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, default='user')
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)

def init_db():
    try:
        Base.metadata.create_all(engine)
        print('✅ Таблицы созданы в PostgreSQL')
        return True
    except Exception as e:
        print(f"❌ Ошибка создания таблиц: {e}")
        return False

def get_all_news():
    try:
        session = SessionLocal()
        news = session.query(News).order_by(News.timestamp.desc()).all()
        session.close()
        return [{
            'id': n.id, 'title': n.title, 'content': n.content,
            'preview': n.preview, 'type': n.type, 'date': n.date,
            'link': n.link, 'author': n.author, 'timestamp': n.timestamp
        } for n in news]
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return []

def add_news(title, content, type='update', link='', author='Admin'):
    try:
        session = SessionLocal()
        preview = content[:300] + ('...' if len(content) > 300 else '')
        date = datetime.now().strftime('%d %B %Y')
        timestamp = int(datetime.now().timestamp() * 1000)
        
        news = News(
            title=title, content=content, preview=preview,
            type=type, date=date, link=link, author=author, timestamp=timestamp
        )
        session.add(news)
        session.commit()
        session.refresh(news)
        session.close()
        return {
            'id': news.id, 'title': news.title, 'content': news.content,
            'preview': news.preview, 'type': news.type, 'date': news.date,
            'link': news.link, 'author': news.author, 'timestamp': news.timestamp
        }
    except Exception as e:
        print(f"❌ Ошибка добавления: {e}")
        return None

def delete_news(news_id):
    try:
        session = SessionLocal()
        deleted = session.query(News).filter(News.id == news_id).delete()
        session.commit()
        session.close()
        return deleted > 0
    except Exception as e:
        print(f"❌ Ошибка удаления: {e}")
        return False

def add_user(username, email, password_hash):
    try:
        session = SessionLocal()
        user = User(
            username=username,
            email=email,
            password_hash=password_hash,
            role='user',
            is_active=True
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        session.close()
        return {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'role': user.role
        }
    except Exception as e:
        print(f"❌ Ошибка добавления пользователя: {e}")
        return None

def get_user_by_username(username):
    try:
        session = SessionLocal()
        user = session.query(User).filter(User.username == username).first()
        session.close()
        if user:
            return {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'password_hash': user.password_hash,
                'role': user.role
            }
        return None
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return None

def get_user_by_email(email):
    try:
        session = SessionLocal()
        user = session.query(User).filter(User.email == email).first()
        session.close()
        if user:
            return {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'password_hash': user.password_hash,
                'role': user.role
            }
        return None
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return None

def delete_all_users():
    try:
        session = SessionLocal()
        deleted = session.query(User).delete()
        session.commit()
        session.close()
        return deleted
    except Exception as e:
        print(f"❌ Ошибка удаления пользователей: {e}")
        return 0

def promote_to_admin(username):
    try:
        session = SessionLocal()
        user = session.query(User).filter(User.username == username).first()
        if user:
            user.role = 'admin'
            session.commit()
            session.close()
            return True
        return False
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False