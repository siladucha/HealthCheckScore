import logging
from logging.handlers import TimedRotatingFileHandler
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session
from create_db import SessionLocal, User, PhysicalActivity, SleepActivity, BloodTests
from datetime import datetime, UTC
import uuid
from pydantic import BaseModel, Field
from typing import Optional, List

project_name = "Health_Tracker_API"
app = FastAPI(title=project_name)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
def configure_logging():
    # Create a TimedRotatingFileHandler for logging to a file with rotation at midnight
    file_handler = TimedRotatingFileHandler(
        filename=f'{project_name}.log',
        when='midnight',
        interval=1,
        backupCount=7
    )
    file_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        '%(asctime)s - [PID: %(process)d] - [Thread ID: %(thread)d] - %(module)s - %(name)s - %(levelname)s - %(funcName)s - %(message)s'
    )
    file_handler.setFormatter(formatter)

    # Create a StreamHandler for logging to the console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)

    # Configure the root logger
    logging.basicConfig(handlers=[file_handler, console_handler], level=logging.DEBUG)

    # Apply the logging configuration to `uvicorn`
    uvicorn_logger = logging.getLogger("uvicorn")
    uvicorn_logger.handlers.clear()  # Clear existing handlers
    uvicorn_logger.addHandler(file_handler)
    uvicorn_logger.addHandler(console_handler)
    uvicorn_logger.setLevel(logging.DEBUG)

    uvicorn_access_logger = logging.getLogger("uvicorn.access")
    uvicorn_access_logger.handlers.clear()
    uvicorn_access_logger.addHandler(file_handler)
    uvicorn_access_logger.addHandler(console_handler)
    uvicorn_access_logger.setLevel(logging.DEBUG)

    uvicorn_error_logger = logging.getLogger("uvicorn.error")
    uvicorn_error_logger.handlers.clear()
    uvicorn_error_logger.addHandler(file_handler)
    uvicorn_error_logger.addHandler(console_handler)
    uvicorn_error_logger.setLevel(logging.DEBUG)

    # **🔹 ОТКЛЮЧАЕМ лишние DEBUG-логи от `aiormq`, `aio_pika`, `pika`**
    for logger_name in ["aiormq", "aio_pika", "pika", "aiomysql", "aiogram"]:
        logging.getLogger(logger_name).setLevel(logging.WARNING)  # ⬅ Теперь не спамят в логи

    logging.info("[Logging] ✅ Конфигурация логирования завершена!")


configure_logging()
logger = logging.getLogger(project_name)
logger.info(f' {project_name} Started')
### 🔹 USER CRUD

class UserUpdate(BaseModel):
    gender: Optional[str] = None
    age_group: Optional[str] = None
    climate_zone: Optional[str] = None
    chronic_conditions: Optional[str] = None
    fitness_level: Optional[str] = None
    language: Optional[str] = None
    registration_status: Optional[str] = None
    registration_source: Optional[str] = None
class UserCreate(BaseModel):
    gender: str
    age_group: str
    climate_zone: str
    chronic_conditions: str
    fitness_level: str
    language: str
    registration_status: str
    registration_source: str
    uuid: str = Field(default_factory=lambda: str(uuid.uuid4()))
class UserResponse(BaseModel):
    id: int
    gender: str
    age_group: str
    climate_zone: str
    chronic_conditions: str
    fitness_level: str
    language: str
    uuid: str
    registration_status: str
    registration_source: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

@app.post("/users/", response_model=dict)
def create_user(user_data: UserCreate, db: Session = Depends(get_db)):
    try:
        existing_user = db.query(User).filter(User.uuid == user_data.uuid).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="User with this UUID already exists")
        new_user = User(**user_data.dict())
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return {"message": "User created successfully", "user_id": new_user.id, "uuid": new_user.uuid}
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")


@app.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user  # ✅ Теперь FastAPI корректно сериализует ответ через Pydantic
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")


@app.put("/users/{user_id}", response_model=dict)
def update_user(user_id: int, user_data: UserUpdate, db: Session = Depends(get_db)):
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        for key, value in user_data.dict(exclude_unset=True).items():
            setattr(user, key, value)

        user.updated_at = datetime.now(UTC)
        db.commit()
        db.refresh(user)

        return {"message": "User updated successfully", "user_id": user.id}
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")


@app.delete("/users/{user_id}", response_model=dict)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        db.query(BloodTests).filter(BloodTests.user_id == user_id).delete()
        db.query(SleepActivity).filter(SleepActivity.user_id == user_id).delete()
        db.query(PhysicalActivity).filter(PhysicalActivity.user_id == user_id).delete()

        db.delete(user)
        db.commit()

        return {"message": "User deleted successfully"}
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")


### 🔹 PHYSICAL ACTIVITY CRUD

class PhysicalActivityCreate(BaseModel):
    steps: int
    calories_burned: float
    active_minutes: int
class PhysicalActivityUpdate(BaseModel):
    steps: Optional[int] = None
    calories_burned: Optional[float] = None
    active_minutes: Optional[int] = None
    recorded_at: Optional[datetime] = None
class PhysicalActivityResponse(BaseModel):
    id: int
    user_id: int
    steps: int
    calories_burned: float
    active_minutes: int
    recorded_at: Optional[datetime] = None

    class Config:
        from_attributes = True

@app.post("/user/{user_id}/physical_activity/", response_model=PhysicalActivityResponse)
def create_physical_activity(user_id: int, activity_data: PhysicalActivityCreate, db: Session = Depends(get_db)):
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=400, detail="User does not exist")

        new_activity = PhysicalActivity(**activity_data.dict(), user_id=user_id)
        db.add(new_activity)
        db.commit()
        db.refresh(new_activity)
        return new_activity
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")


@app.get("/user/{user_id}/physical_activity/{activity_id}", response_model=PhysicalActivityResponse)
def get_physical_activity(user_id: int, activity_id: int, db: Session = Depends(get_db)):
    try:
        activity = db.query(PhysicalActivity).filter(
            PhysicalActivity.id == activity_id, PhysicalActivity.user_id == user_id
        ).first()

        if not activity:
            raise HTTPException(status_code=404, detail="Activity not found or access denied")

        return activity
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")


@app.get("/user/{user_id}/physical_activity/", response_model=List[PhysicalActivityResponse])
def get_all_physical_activities(user_id: int, db: Session = Depends(get_db)):
    try:
        activities = db.query(PhysicalActivity).filter(PhysicalActivity.user_id == user_id).all()
        if not activities:
            raise HTTPException(status_code=404, detail="Activity not found or access denied")
        return activities
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")


@app.put("/user/{user_id}/physical_activity/{activity_id}", response_model=PhysicalActivityResponse)
def update_physical_activity(user_id: int, activity_id: int, activity_data: PhysicalActivityUpdate, db: Session = Depends(get_db)):
    try:
        activity = db.query(PhysicalActivity).filter(
            PhysicalActivity.id == activity_id,
            PhysicalActivity.user_id == user_id
        ).first()

        if not activity:
            raise HTTPException(status_code=404, detail="Activity not found or access denied")

        # 🔹 Исправленный отступ
        for key, value in activity_data.dict(exclude_unset=True).items():
            setattr(activity, key, value)

        db.commit()
        db.refresh(activity)
        return activity

    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")


@app.delete("/user/{user_id}/physical_activity/{activity_id}", status_code=204)
def delete_physical_activity(user_id: int, activity_id: int, db: Session = Depends(get_db)):
    try:
        activity = db.query(PhysicalActivity).filter(
            PhysicalActivity.id == activity_id, PhysicalActivity.user_id == user_id
        ).first()

        if not activity:
            raise HTTPException(status_code=404, detail="Activity not found or access denied")

        db.delete(activity)
        db.commit()
        return None
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")


### Sleep
class SleepActivityCreate(BaseModel):
    sleep_duration: float
    sleep_quality: int
class SleepActivityUpdate(BaseModel):
    sleep_duration: Optional[float] = None
    sleep_quality: Optional[int] = None
    recorded_at: Optional[datetime] = None
class SleepActivityResponse(BaseModel):
    id: int
    user_id: int
    sleep_duration: float
    sleep_quality: int
    recorded_at: Optional[datetime] = None

    class Config:
        from_attributes = True

@app.post("/user/{user_id}/sleep_activity/", response_model=SleepActivityResponse)
def create_sleep_activity(user_id: int, sleep_data: SleepActivityCreate, db: Session = Depends(get_db)):
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=400, detail="User does not exist")

        new_sleep = SleepActivity(**sleep_data.dict(), user_id=user_id)
        db.add(new_sleep)
        db.commit()
        db.refresh(new_sleep)
        return new_sleep
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")

@app.get("/user/{user_id}/sleep_activity/{sleep_id}", response_model=SleepActivityResponse)
def get_sleep_activity(user_id: int, sleep_id: int, db: Session = Depends(get_db)):
    try:
        sleep = db.query(SleepActivity).filter(
        SleepActivity.id == sleep_id, SleepActivity.user_id == user_id
    ).first()

        if not sleep:
            raise HTTPException(status_code=404, detail="Sleep activity not found or access denied")

        return sleep
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")

@app.get("/user/{user_id}/sleep_activity/", response_model=List[SleepActivityResponse])
def get_all_sleep_activities(user_id: int, db: Session = Depends(get_db)):
    try:
        sleeps = db.query(SleepActivity).filter(SleepActivity.user_id == user_id).all()
        if not sleeps:
            raise HTTPException(status_code=404, detail="Sleep activity not found or access denied")
        return sleeps
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")

@app.put("/user/{user_id}/sleep_activity/{sleep_id}", response_model=SleepActivityResponse)
def update_sleep_activity(user_id: int, sleep_id: int, sleep_data: SleepActivityUpdate, db: Session = Depends(get_db)):
    try:
        sleep = db.query(SleepActivity).filter(
        SleepActivity.id == sleep_id, SleepActivity.user_id == user_id
    ).first()

        if not sleep:
            raise HTTPException(status_code=404, detail="Sleep activity not found or access denied")

        for key, value in sleep_data.dict(exclude_unset=True).items():
            setattr(sleep, key, value)

        db.commit()
        db.refresh(sleep)
        return sleep
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")

@app.delete("/user/{user_id}/sleep_activity/{sleep_id}", status_code=204)
def delete_sleep_activity(user_id: int, sleep_id: int, db: Session = Depends(get_db)):
    try:
        sleep = db.query(SleepActivity).filter(
        SleepActivity.id == sleep_id, SleepActivity.user_id == user_id
    ).first()

        if not sleep:
            raise HTTPException(status_code=404, detail="Sleep activity not found or access denied")

        db.delete(sleep)
        db.commit()
        return None
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")

###blood
class BloodTestCreate(BaseModel):
    glucose_level: float
    cholesterol_level: float

class BloodTestUpdate(BaseModel):
    glucose_level: Optional[float] = None
    cholesterol_level: Optional[float] = None
    recorded_at: Optional[datetime] = None

class BloodTestResponse(BaseModel):
    id: int
    user_id: int
    glucose_level: float
    cholesterol_level: float
    recorded_at: Optional[datetime] = None

    class Config:
        from_attributes = True

@app.post("/user/{user_id}/blood_tests/", response_model=BloodTestResponse)
def create_blood_test(user_id: int, blood_data: BloodTestCreate, db: Session = Depends(get_db)):
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=400, detail="User does not exist")

        new_blood_test = BloodTests(**blood_data.dict(), user_id=user_id)
        db.add(new_blood_test)
        db.commit()
        db.refresh(new_blood_test)
        return new_blood_test
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")

@app.get("/user/{user_id}/blood_tests/{blood_test_id}", response_model=BloodTestResponse)
def get_blood_test(user_id: int, blood_test_id: int, db: Session = Depends(get_db)):
    try:
        blood_test = db.query(BloodTests).filter(
        BloodTests.id == blood_test_id, BloodTests.user_id == user_id
    ).first()

        if not blood_test:
            raise HTTPException(status_code=404, detail="Blood test not found or access denied")

        return blood_test
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")

@app.get("/user/{user_id}/blood_tests/", response_model=List[BloodTestResponse])
def get_all_blood_tests(user_id: int, db: Session = Depends(get_db)):
    try:
        blood_tests = db.query(BloodTests).filter(BloodTests.user_id == user_id).all()

        if not blood_tests:
            raise HTTPException(status_code=404, detail="No blood test records found")

        return blood_tests
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")

@app.put("/user/{user_id}/blood_tests/{blood_test_id}", response_model=BloodTestResponse)
def update_blood_test(user_id: int, blood_test_id: int, blood_data: BloodTestUpdate, db: Session = Depends(get_db)):
    try:
        blood_test = db.query(BloodTests).filter(
            BloodTests.id == blood_test_id, BloodTests.user_id == user_id
        ).first()

        if not blood_test:
            raise HTTPException(status_code=404, detail="Blood test not found or access denied")

        for key, value in blood_data.dict(exclude_unset=True).items():
            setattr(blood_test, key, value)

        db.commit()
        db.refresh(blood_test)
        return blood_test
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")

@app.delete("/user/{user_id}/blood_tests/{blood_test_id}", status_code=204)
def delete_blood_test(user_id: int, blood_test_id: int, db: Session = Depends(get_db)):
    try:
        blood_test = db.query(BloodTests).filter(
        BloodTests.id == blood_test_id, BloodTests.user_id == user_id
    ).first()

        if not blood_test:
            raise HTTPException(status_code=404, detail="Blood test not found or access denied")

        db.delete(blood_test)
        db.commit()
        return None
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")

### 🔹 GET HEALTH SCORE



@app.get("/user/{user_id}/get_health_score/", response_model=dict)
def get_health_score(user_id: int, db: Session = Depends(get_db)):
    try:
        start_time = datetime.now()
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Определяем группу пользователя
        user_group_query = db.query(User.id).filter(
            User.climate_zone == user.climate_zone,
            User.chronic_conditions == user.chronic_conditions,
            User.age_group == user.age_group,
            User.fitness_level == user.fitness_level
        ).subquery()

        group_size = db.query(func.count()).select_from(user_group_query).scalar()

        # Средние показатели группы
        avg_values = db.query(
            func.avg(PhysicalActivity.steps).label("avg_steps"),
            func.avg(SleepActivity.sleep_duration).label("avg_sleep"),
            func.avg(BloodTests.glucose_level).label("avg_glucose"),
        ).filter(
            PhysicalActivity.user_id.in_(db.query(user_group_query.c.id)),
            SleepActivity.user_id.in_(db.query(user_group_query.c.id)),
            BloodTests.user_id.in_(db.query(user_group_query.c.id))
        ).first()

        # Данные пользователя
        user_values = db.query(
            func.avg(PhysicalActivity.steps).label("user_steps"),
            func.avg(SleepActivity.sleep_duration).label("user_sleep"),
            func.avg(BloodTests.glucose_level).label("user_glucose"),
        ).filter(
            PhysicalActivity.user_id == user_id,
            SleepActivity.user_id == user_id,
            BloodTests.user_id == user_id
        ).first()

        # Конвертация значений и установка дефолтных значений
        avg_steps = float(avg_values.avg_steps or 0)
        avg_sleep = float(avg_values.avg_sleep or 0)
        avg_glucose = float(avg_values.avg_glucose or 100)

        user_steps = float(user_values.user_steps or 0)
        user_sleep = float(user_values.user_sleep or 0)
        user_glucose = float(user_values.user_glucose or 100)

        # Если у пользователя нет данных → Health Score = 0
        if user_steps == 0 and user_sleep == 0 and user_glucose == 100:
            health_score = 0
        else:
            health_score = (
                min(29.9, (user_steps / (avg_steps + 1)) * 30) +
                min(39.9, (user_sleep / (avg_sleep + 1)) * 40) +
                min(29.9, (100 / (user_glucose + 1)) * 30)
            )

        health_score = round(health_score, 2)

        logger.info(f'Calculated health score for user_id {user_id} is {health_score}')

        return {
            "microseconds": (datetime.now() - start_time).microseconds,
            "user_id": user_id,
            "health_score": health_score,
            "user_data": {
                "steps": round(user_steps, 2),
                "sleep": round(user_sleep, 2),
                "glucose": round(user_glucose, 2),
            },
            "group_averages": {
                "steps": round(avg_steps, 2),
                "sleep": round(avg_sleep, 2),
                "glucose": round(avg_glucose, 2),
            },
            "user_group": {
                "group_size": group_size,
                "age_group": user.age_group,
                "fitness_level": user.fitness_level,
                "climate_zone": user.climate_zone,
                "chronic_conditions": user.chronic_conditions
            }
        }
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")

@app.get("/")
def get_hp():
    return {"message": "Health Score API"}