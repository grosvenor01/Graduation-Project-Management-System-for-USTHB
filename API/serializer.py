from rest_framework import serializers
from .models import *
class user_serializer(serializers.ModelSerializer):
    class Meta:
        model =User
        fields="__all__"
class pub_serializer(serializers.ModelSerializer):
    user = user_serializer()
    class Meta:
        model=pub
        fields ="__all__"
class pub_serializer_2(serializers.ModelSerializer):
    class Meta:
        model=pub
        fields ="__all__"
class student_serializer(serializers.ModelSerializer):
    class Meta:
        model=student
        fields ="__all__"
class student_serializer2(serializers.ModelSerializer):
    user=user_serializer()
    class Meta:
        model=student
        fields ="__all__"
class ensignant_serializer(serializers.ModelSerializer):
    class Meta:
        model=ensignant
        fields ="__all__"
class ensignant_serializer2(serializers.ModelSerializer):
    user=user_serializer()
    class Meta:
        model=ensignant
        fields ="__all__"
class company_serializer(serializers.ModelSerializer):
    class Meta: 
        model = company
        fields ="__all__"
class comment_serializer(serializers.ModelSerializer):
    class Meta:
        model=comment
        fields = "__all__"
class message_serializer(serializers.ModelSerializer):
    class Meta:
        model=message
        fields="__all__"
class validated_themes_serializer(serializers.ModelSerializer):
    class Meta:
        model=validated_themes
        fields="__all__"
class jury_serializer(serializers.ModelSerializer):
    themes=validated_themes_serializer()
    class Meta:
        model=jury
        fields="__all__"
class themes_ToValidate_serializer(serializers.ModelSerializer):
    class Meta:
        model=themes_to_validate
        fields="__all__"

class comission_serializer(serializers.ModelSerializer):
    class Meta:
        model=comission_validation
        fields="__all__"
class notification_serializer(serializers.ModelSerializer):
    send_from=user_serializer()
    class Meta:
        model=notification
        fields="__all__"
class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password')
        extra_kwargs = {'password': {'write_only': True}} # the field will only be used for deserialization (when creating or updating an object

    def create(self, validated_data):
        user = User.objects.create_user(validated_data['username'], validated_data['email'], validated_data['password'])
        return user
class skill_serializer(serializers.ModelSerializer):
    class Meta:
        model=skill
        fields ="__all__"