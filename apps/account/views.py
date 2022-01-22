from django.contrib.auth import get_user_model
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken

from helper.drf import GetCustomSerializerClass
from .serializers import AccountSerializer, CreateAccountSerializer, UpdateAccountSerializer

User = get_user_model()


class AccountView(GetCustomSerializerClass, GenericViewSet):
    queryset = User.objects.all()
    serializer_class = AccountSerializer
    update_serializer_class = UpdateAccountSerializer
    create_serializer_class = CreateAccountSerializer
    permission_classes = (IsAuthenticated,)

    @swagger_auto_schema(
        responses={status.HTTP_201_CREATED: TokenRefreshSerializer()},
        request_body=CreateAccountSerializer(),
    )
    @action(detail=False, methods=('post',), url_path='sign-up', permission_classes=(AllowAny,))
    def sign_up(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_user = serializer.save()
        refresh = RefreshToken.for_user(new_user)
        response_serializer = TokenRefreshSerializer({'refresh': str(refresh), 'access': str(refresh.access_token)})
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['patch'], url_path='update-user-info')
    def update_user_info(self, request, *args, **kwargs):
        serializer = self.get_serializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='user-info')
    def user_info(self, request, *args, **kwargs):
        serializer = self.get_serializer(instance=request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)
