from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """
    Базовый класс для всех ORM-моделей проекта.
    В SQLAlchemy 2.0 используется наследование от DeclarativeBase.
    """
    pass