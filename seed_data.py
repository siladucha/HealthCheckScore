from sqlalchemy.orm import Session
from create_db import SessionLocal, User, PhysicalActivity, SleepActivity, BloodTests
from datetime import datetime, UTC, timedelta
import uuid
import random

def seed_data():
    session: Session = SessionLocal()

    try:
        print("\n🚀 *** Start filling test data ***\n")
        user_groups = {
            "Athletes": [],
            "Average": [],
            "Sedentary": [],
            "Elderly": []
        }

        users = [
            User(gender="male", age_group="20-30", climate_zone="Temperate", chronic_conditions="no",
                 fitness_level="advanced", language="en", uuid=str(uuid.uuid4()), registration_status="completed",
                 registration_source="Web"),
            User(gender="female", age_group="20-30", climate_zone="Temperate", chronic_conditions="no",
                 fitness_level="advanced", language="fr", uuid=str(uuid.uuid4()), registration_status="completed",
                 registration_source="App"),
            User(gender="male", age_group="30-40", climate_zone="Tropical", chronic_conditions="no",
                 fitness_level="intermediate", language="es", uuid=str(uuid.uuid4()), registration_status="completed",
                 registration_source="Telegram"),
            User(gender="female", age_group="30-40", climate_zone="Tropical", chronic_conditions="yes",
                 fitness_level="intermediate", language="de", uuid=str(uuid.uuid4()), registration_status="pending",
                 registration_source="Web"),
            User(gender="male", age_group="40-50", climate_zone="Arctic", chronic_conditions="yes",
                 fitness_level="beginner", language="en", uuid=str(uuid.uuid4()), registration_status="completed",
                 registration_source="Web"),
            User(gender="female", age_group="40-50", climate_zone="Arctic", chronic_conditions="yes",
                 fitness_level="beginner", language="ru", uuid=str(uuid.uuid4()), registration_status="pending",
                 registration_source="App"),
            User(gender="male", age_group="50-60", climate_zone="Desert", chronic_conditions="yes",
                 fitness_level="low", language="it", uuid=str(uuid.uuid4()), registration_status="completed",
                 registration_source="Telegram"),
            User(gender="female", age_group="50-60", climate_zone="Desert", chronic_conditions="yes",
                 fitness_level="low", language="nl", uuid=str(uuid.uuid4()), registration_status="completed",
                 registration_source="Web"),
            User(gender="male", age_group="60-70", climate_zone="Temperate", chronic_conditions="yes",
                 fitness_level="very low", language="en", uuid=str(uuid.uuid4()), registration_status="pending",
                 registration_source="App"),
            User(gender="female", age_group="60-70", climate_zone="Temperate", chronic_conditions="yes",
                 fitness_level="very low", language="es", uuid=str(uuid.uuid4()), registration_status="completed",
                 registration_source="Web"),
        ]

        session.add_all(users)
        session.commit()
        print("✅ Users added!\n")
        users_data = session.query(User).all()
        user_ids = [user.id for user in users_data]

        user_groups["Athletes"] = user_ids[:2]
        user_groups["Average"] = user_ids[2:5]
        user_groups["Sedentary"] = user_ids[5:8]
        user_groups["Elderly"] = user_ids[8:]

        print("📌 **User groups:**")
        for group, ids in user_groups.items():
            print(f"🔹 {group}: {ids}")

        physical_activities = []
        for user_id in user_ids:
            steps = random.randint(2000, 15000)
            calories = round(steps * 0.05, 1)
            active_minutes = random.randint(20, 120)
            recorded_at = datetime.now(UTC) - timedelta(days=random.randint(0, 30))

            physical_activities.append(PhysicalActivity(
                user_id=user_id, steps=steps, calories_burned=calories,
                active_minutes=active_minutes, recorded_at=recorded_at
            ))

        session.add_all(physical_activities)
        session.commit()
        print("✅ Physical activity data added!\n")
        sleep_data = []
        for user_id in user_ids:
            sleep_duration = round(random.uniform(4, 9), 1)
            sleep_quality = random.randint(50, 100)
            recorded_at = datetime.now(UTC) - timedelta(days=random.randint(0, 30))

            sleep_data.append(SleepActivity(
                user_id=user_id, sleep_duration=sleep_duration,
                sleep_quality=sleep_quality, recorded_at=recorded_at
            ))

        session.add_all(sleep_data)
        session.commit()
        print("✅ Sleep data added!\n")

        blood_tests = []
        for user_id in user_ids:
            glucose_level = round(random.uniform(70, 120), 1)
            cholesterol_level = round(random.uniform(150, 250), 1)
            recorded_at = datetime.now(UTC) - timedelta(days=random.randint(0, 30))

            blood_tests.append(BloodTests(
                user_id=user_id, glucose_level=glucose_level,
                cholesterol_level=cholesterol_level, recorded_at=recorded_at
            ))

        session.add_all(blood_tests)
        session.commit()
        print("✅ Blood test data added!\n")
    except Exception as e:
        session.rollback()
        print(f"❌ Error filling data: {e}")
    finally:
        session.close()
        print("🔄 Database session closed.")

if __name__ == "__main__":
    seed_data()