# Import all models here so Alembic autogenerate can detect schema changes.
from app.models.category import Category
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.product import Product
from app.models.restaurant import Restaurant
from app.models.user import User

__all__ = ["Category", "Order", "OrderItem", "Product", "Restaurant", "User"]
