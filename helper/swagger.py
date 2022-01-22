from drf_yasg.inspectors import SwaggerAutoSchema


class CompoundTagsSchema(SwaggerAutoSchema):
    def get_tags(self, operation_keys=None):
        if operation_keys is None:
            return []
        return [' > '.join(operation_keys[:-1])]
