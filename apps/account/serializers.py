from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()


class AccountSerializer(serializers.ModelSerializer):
    confirm_password = serializers.CharField(required=False, allow_null=True, write_only=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'password', 'confirm_password')
        extra_kwargs = {'password': {'write_only': True}, 'id': {'read_only': True}, 'username': {'read_only': True}}

    def validate_email(self, email):
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError('Email have already been used.')
        return email


class CreateAccountSerializer(AccountSerializer):
    confirm_password = serializers.CharField(required=True, allow_null=True, write_only=True)

    class Meta(AccountSerializer.Meta):
        extra_kwargs = {'password': {'write_only': True}, 'id': {'read_only': True}}

    def validate(self, data):
        if data.get('password') != data.get('confirm_password'):
            raise serializers.ValidationError('password and confirm password have conflicts')
        del data['confirm_password']
        return data

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User()
        for key, value in validated_data.items():
            setattr(user, key, value)
        user.set_password(password)
        user.save()
        return user


class UpdateAccountSerializer(AccountSerializer):

    def validate(self, data):
        if data.get('password'):
            if data.get('password') != data.get('confirm_password'):
                raise serializers.ValidationError('password and confirm password have conflicts')
            del data['confirm_password']
        return data

    def update(self, instance, validated_data):
        if validated_data.get('password'):
            password = validated_data.pop('password')
            user = super().update(instance, validated_data)
            user.set_password(password)
            user.save()
            return user
        return super().update(instance, validated_data)
