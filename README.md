# HealthCheckScore
for longevity ai

Database Schema & API Implementation
	•	Database: MySQL with SQLAlchemy ORM.
	•	Tables: users, physical_activity, sleep_activity, blood_tests.
	•	Schema Initialization: The create_db.py script sets up the database schema.
	•	It creates the necessary tables and indexes.
	•	Includes Index on user_id and recorded_at to optimize queries.
	•	Uses MySQL connection pooling to prevent connection issues.
	•	Data Seeding: The seed_data.py script pre-populates test data, grouping users by fitness level.
	•	API: FastAPI + SQLAlchemy for CRUD operations.
	•	Health Score Calculation: Aggregates steps, sleep_duration, and glucose_level compared to user group averages.
