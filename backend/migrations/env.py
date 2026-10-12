
import os
import sys
from logging.config import fileConfig

from alembic import context
from dotenv import load_dotenv
from sqlalchemy import engine_from_config, pool
from sqlalchemy.engine import URL

# Add the backend folder to Python's import path.
BACKEND_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
)
sys.path.insert(0, BACKEND_DIR)

# Load database settings from backend/.env.
load_dotenv(os.path.join(BACKEND_DIR, ".env"))

# Get the Alembic configuration.
config = context.config

# Configure Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Read database settings from the existing application config.
from app.core.config import (
    DB_USER,
    DB_PASSWORD,
    DB_HOST,
    DB_NAME,
)

# Build the database URL safely.
database_url = URL.create(
    drivername="mysql+pymysql",
    username=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST,
    database=DB_NAME,
)

# Provide the database URL to Alembic.
config.set_main_option(
    "sqlalchemy.url",
    database_url.render_as_string(hide_password=False).replace("%", "%%"),
)

# Import Base and all current models for migration detection.
from app.database.connection import Base
from app.models import User, Teacher, Student, Department

# Alembic uses this metadata to compare models with the database.
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Configure and run migrations without opening a database connection."""

    url = config.get_main_option("sqlalchemy.url")

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Configure and run migrations using a live database connection."""

    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()

    connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()