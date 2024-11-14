import databases
import sqlalchemy
import asyncio
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "postgresql://ggjnaaaa:2016@127.0.0.1:5432/tinkoff_db"

database = databases.Database(DATABASE_URL)
metadata = sqlalchemy.MetaData()

web_users = sqlalchemy.Table(
    "web_users",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True, autoincrement=True),
    sqlalchemy.Column("username", sqlalchemy.String, unique=True, nullable=False),
    sqlalchemy.Column("password", sqlalchemy.String, nullable=False),
    sqlalchemy.Column(
        "role", sqlalchemy.String, nullable=False, server_default="user"
    ),  # Add role with default value
)

engine = sqlalchemy.create_engine(DATABASE_URL)
metadata.create_all(engine)
Session = sessionmaker(bind=engine)


async def get_db():
    await database.connect()
    try:
        yield database
    finally:
        await database.disconnect()


async def main():
    await database.connect()
    print("Connected to the database!")
    await database.disconnect()
    print("Disconnected from the database!")


if __name__ == "__main__":
    asyncio.run(main())