"""API serializers bound to the OpenAPI contract in contracts/openapi.yaml."""

from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.catalog.models import Category, Product, UnitOfMeasure
from apps.movements.models import StockMovement
from apps.warehouses.models import Location, StockLevel

User = get_user_model()


class LoginRequest(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)


class UserPublic(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "role"]


class UserAdmin(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "role", "is_active"]


class UserWrite(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ["username", "password", "email", "role"]

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class RoleWrite(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["role"]


class CategoryRead(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "description", "is_active"]


class CategoryWrite(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["name", "description", "is_active"]


class UnitRead(serializers.ModelSerializer):
    class Meta:
        model = UnitOfMeasure
        fields = ["id", "name", "symbol", "allow_fractional"]


class LocationRead(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ["id", "code", "name", "is_active"]


class LocationWrite(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ["code", "name", "is_active"]


class ItemRead(serializers.ModelSerializer):
    category = CategoryRead()
    unit = UnitRead()

    class Meta:
        model = Product
        fields = ["sku", "name", "category", "unit", "reorder_level", "unit_cost", "is_active"]


class ItemWrite(serializers.ModelSerializer):
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all())
    unit = serializers.PrimaryKeyRelatedField(queryset=UnitOfMeasure.objects.all())

    class Meta:
        model = Product
        fields = ["sku", "name", "category", "unit", "reorder_level", "unit_cost"]

    def validate_reorder_level(self, value):
        if value < 0:
            raise serializers.ValidationError("reorder_level must be zero or greater")
        return value

    def validate_unit_cost(self, value):
        if value < 0:
            raise serializers.ValidationError("unit_cost must be zero or greater")
        return value

    def validate(self, attrs):
        sku = attrs.get("sku")
        if self.instance is not None and sku and sku != self.instance.sku:
            raise serializers.ValidationError({"sku": "SKU is immutable."})
        return attrs


class StockLevelRead(serializers.ModelSerializer):
    product = ItemRead()
    location = LocationRead()
    status = serializers.CharField(read_only=True)

    class Meta:
        model = StockLevel
        fields = ["product", "location", "quantity", "status"]


class MovementWrite(serializers.Serializer):
    flow = serializers.ChoiceField(choices=StockMovement.Flow.choices)
    product = serializers.CharField(max_length=50)
    location = serializers.PrimaryKeyRelatedField(queryset=Location.objects.all())
    quantity = serializers.DecimalField(max_digits=12, decimal_places=3)
    reason = serializers.CharField(max_length=500)
    override = serializers.BooleanField(default=False)
    reconciliation_ref = serializers.CharField(max_length=100, required=False, allow_blank=True)
    unit_cost = serializers.DecimalField(
        max_digits=12, decimal_places=2, required=False, allow_null=True, min_value=0
    )

    def validate_quantity(self, value):
        if value == 0:
            raise serializers.ValidationError("quantity must be non-zero")
        return value


class MovementRead(serializers.ModelSerializer):
    product = serializers.SlugRelatedField(slug_field="sku", read_only=True)
    location = LocationRead()

    class Meta:
        model = StockMovement
        fields = [
            "id",
            "flow",
            "direction",
            "product",
            "location",
            "quantity",
            "reason",
            "recorded_by",
            "recorded_at",
            "status",
            "requires_override",
            "override_by",
            "override_at",
            "reconciliation_ref",
            "unit_cost",
        ]


class ConsentWrite(serializers.Serializer):
    approved = serializers.BooleanField()


class AlertItem(serializers.Serializer):
    sku = serializers.CharField()
    name = serializers.CharField()
    location = LocationRead()
    quantity = serializers.DecimalField(max_digits=12, decimal_places=3)
    reorder_level = serializers.DecimalField(max_digits=12, decimal_places=3)
    status = serializers.CharField()


class AlertSummary(serializers.Serializer):
    low_stock = AlertItem(many=True)
    out_of_stock = AlertItem(many=True)


class ValuationRow(serializers.Serializer):
    sku = serializers.CharField()
    name = serializers.CharField()
    location = LocationRead()
    quantity = serializers.DecimalField(max_digits=12, decimal_places=3)
    unit_cost = serializers.DecimalField(max_digits=12, decimal_places=2)
    value = serializers.DecimalField(max_digits=12, decimal_places=2)


class ValuationReport(serializers.Serializer):
    rows = ValuationRow(many=True)
    total = serializers.DecimalField(max_digits=14, decimal_places=2)
