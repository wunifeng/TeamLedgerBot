"""Shared enumerations used across models and schemas."""
import enum


class TransactionType(str, enum.Enum):
    income = "income"
    expense = "expense"
    salary = "salary"


class CategoryType(str, enum.Enum):
    income = "income"
    expense = "expense"
