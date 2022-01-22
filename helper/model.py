from uuid import uuid4

from django.db import models


class BaseModel(models.Model):
    id = models.UUIDField(editable=False, default=uuid4, primary_key=True)
    create_time = models.DateTimeField(auto_now_add=True, db_index=True)
    modify_time = models.DateTimeField(auto_now=True)

    auto_cols = ('create_time', 'modify_time')

    class Meta:
        abstract = True
