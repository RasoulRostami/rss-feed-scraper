class GetCustomSerializerClass:
    """
    override get_serializer_class method in GenericViewSet to return our custom serializer_class and have more readability
    """
    update_serializer_class = None
    create_serializer_class = None

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH') and self.update_serializer_class is not None:
            return self.update_serializer_class
        elif self.request.method == 'POST' and self.create_serializer_class is not None:
            return self.create_serializer_class
        assert self.serializer_class is not None, (
                "'%s' should either include a `serializer_class` attribute, "
                "or override the `get_serializer_class()` method."
                % self.__class__.__name__
        )
        return self.serializer_class
