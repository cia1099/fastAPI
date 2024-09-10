from sqlalchemy import Column, Integer, String, ForeignKey, create_engine
from sqlalchemy.orm import Session, DeclarativeBase
import sqlalchemy as sql


class Base(DeclarativeBase):
    pass


class Customer(Base):
    __tablename__ = "customers"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    country = Column(String)


class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey("customers.id"))
    amount = Column(Integer)


DB_URL = "sqlite:///join.db"


def create_table():
    engine = create_engine(DB_URL)
    Customer.metadata.drop_all(engine)
    Customer.metadata.create_all(engine)
    customers_gen = (
        ("Alex", "USA"),
        ("Bob", "UK"),
        ("Chris", "France"),
        ("Dave", "Canada"),
    )
    orders_gen = ((1, 100), (2, 200), (5, 300), (3, 400))
    with Session(bind=engine, future=True) as session:
        session.add_all(Customer(name=c[0], country=c[1]) for c in customers_gen)
        session.add_all(Order(customer_id=o[0], amount=o[1]) for o in orders_gen)
        session.commit()


if __name__ == "__main__":
    create_table()
    inner_join = (
        sql.select(Order.id, Customer.name, Order.amount)
        .select_from(Order)
        .join(Customer, Order.customer_id == Customer.id)
    )
    outer_join = sql.select(Customer.id, Customer.name, Order.amount).outerjoin(
        Order, Customer.id == Order.customer_id
    )
    outer_join2 = (
        sql.select(Order.id, Customer.name, Order.amount)
        .select_from(Customer)
        .outerjoin(Order, Order.customer_id == Customer.id)
    )
    full_join = (
        sql.select(Customer.id, Order.id, Customer.name, Order.amount)
        .select_from(Customer)
        .outerjoin(Order, Order.customer_id == Customer.id, full=True)
    )
    engine = create_engine(DB_URL)
    with engine.connect() as cursor:
        print(inner_join)
        print(f"inner join:\n{cursor.execute(inner_join).fetchall()}")
        print("=" * 25)
        print(outer_join)
        print(f"outer join:\n{cursor.execute(outer_join).fetchall()}")
        print("=" * 25)
        print(outer_join2)
        print(f"outer join2:\n{cursor.execute(outer_join2).fetchall()}")
        print("=" * 25)
        print(full_join)
        print(f"full join:\n{cursor.execute(full_join).fetchall()}")
