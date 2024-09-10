from myApp.models import Customer, Item, Notification, SubscriptionPlan, NotificationPreference
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

User = get_user_model()


class SubscriptionPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPlan
        fields = '__all__'


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationPreference
        fields = '__all__'


class CustomerSerializer(serializers.ModelSerializer):
    subscription_plan = SubscriptionPlanSerializer(read_only=True)
    notification_preference = NotificationPreferenceSerializer(read_only=True)

    class Meta:
        model = Customer
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'gender', 'phone', 'subscription_plan',
                  'subscription_end_date', 'auto_renew', 'notification_preference']
        read_only_fields = ['id', 'subscription_end_date']

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user


class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = '__all__'
        read_only_fields = ['qrCode']

    def create(self, validated_data):
        owner = validated_data['owner']
        if Item.objects.filter(owner=owner).count() >= owner.subscription_plan.max_items:
            raise ValidationError("Maximum number of items reached for this subscription plan.")
        return super().create(validated_data)


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = '__all__'
