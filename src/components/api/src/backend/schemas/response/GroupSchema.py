from pydantic_django import ModelSchema

from backend.models import Group


class GroupSchema(ModelSchema):
    class Config:
        model = Group