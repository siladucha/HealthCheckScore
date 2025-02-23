import pymysql
from sqlalchemy import (
    create_engine, Column, Integer, String, DateTime, Float, ForeignKey, Text, Index
)
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime

MYSQL_ROOT_USER = "root"
MYSQL_ROOT_PASSWORD = "MethodB2024!"
DB_NAME = "health_tracker"
DB_USER = "health_user"
DB_PASSWORD = "yourpassword"

ROOT_ENGINE = f"mysql+pymysql://{MYSQL_ROOT_USER}:{MYSQL_ROOT_PASSWORD}@localhost/"


def create_database_and_user():
    try:
        connection = pymysql.connect(host='localhost', user=MYSQL_ROOT_USER, password=MYSQL_ROOT_PASSWORD)
        cursor = connection.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
        cursor.execute(f"CREATE USER IF NOT EXISTS '{DB_USER}'@'localhost' IDENTIFIED BY '{DB_PASSWORD}';")
        cursor.execute(f"GRANT ALL PRIVILEGES ON {DB_NAME}.* TO '{DB_USER}'@'localhost';")
        cursor.execute("FLUSH PRIVILEGES;")
        connection.commit()
        print("✅ Database and user successfully created!")

    except pymysql.MySQLError as e:
        print(f"❌ Error creating database or user: {e}")
    finally:
        cursor.close()
        connection.close()


DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@localhost/{DB_NAME}?charset=utf8mb4"
engine = create_engine(
    DATABASE_URL,
    pool_recycle=1800,
    pool_pre_ping=True,
    echo=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    gender = Column(String(10), index=True)
    age_group = Column(String(10), index=True)
    climate_zone = Column(String(50), index=True)
    chronic_conditions = Column(Text)
    fitness_level = Column(String(20), index=True)
    language = Column(String(20))
    uuid = Column(String(36), unique=True, index=True)
    registration_status = Column(String(20))
    registration_source = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
class PhysicalActivity(Base):
    __tablename__ = "physical_activity"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    steps = Column(Integer)
    calories_burned = Column(Float)
    active_minutes = Column(Integer)
    recorded_at = Column(DateTime, default=datetime.utcnow, index=True)

    __table_args__ = (
        Index("idx_physical_activity_user_time", "user_id", "recorded_at"),
    )
class SleepActivity(Base):
    __tablename__ = "sleep_activity"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    sleep_duration = Column(Float)
    sleep_quality = Column(Integer)
    recorded_at = Column(DateTime, default=datetime.utcnow, index=True)

    __table_args__ = (
        Index("idx_sleep_activity_user_time", "user_id", "recorded_at"),
    )
class BloodTests(Base):
    __tablename__ = "blood_tests"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    glucose_level = Column(Float)
    cholesterol_level = Column(Float)
    recorded_at = Column(DateTime, default=datetime.utcnow, index=True)

    __table_args__ = (
        Index("idx_blood_tests_user_time", "user_id", "recorded_at"),
    )
def create_tables():
    print("🚀 Creating tables in the database...")
    Base.metadata.create_all(bind=engine)
    print("✅ Tables successfully created!")


if __name__ == "__main__":
    create_database_and_user()
    create_tables()