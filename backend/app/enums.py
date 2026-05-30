"""Shared enumerations used across models and schemas."""
import enum


class CategoryType(str, enum.Enum):
    income = "income"
    expense = "expense"
