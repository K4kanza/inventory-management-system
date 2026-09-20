"""API views. Every endpoint declares the capability it requires (default-deny)."""

from django.contrib.auth import authenticate
from django.contrib.auth import login as dj_login
from django.contrib.auth import logout as dj_logout
from django.contrib.auth.models import AnonymousUser
from django.db.models import F, Q
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import APIException, ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import User as UserModel
from apps.accounts.permissions import Capability
from apps.api import serializers as sz
from apps.catalog.models import Category, Product
from apps.movements.models import StockMovement
from apps.movements.services import MovementService, OverIssueDenied
from apps.warehouses.models import Location, StockLevel


class Conflict(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "Conflict with current stock state."


def _location_data(location):
    return sz.LocationRead(location).data


class Page50(PageNumberPagination):
    page_size = 50
    page_size_query_param = "page_size"


class ApiLogin(APIView):
    authentication_classes = []
    permission_classes = []
    required_capability = None

    @extend_schema(
        request=sz.LoginRequest,
        responses={200: sz.UserPublic, 401: OpenApiResponse(description="Invalid credentials.")},
        auth=[],
    )
    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")
        user = authenticate(request, username=username, password=password)
        if user is None:
            return Response({"detail": "Invalid credentials."}, status=status.HTTP_401_UNAUTHORIZED)
        dj_login(request, user)
        return Response(sz.UserPublic(user).data)


class ApiLogout(APIView):
    permission_classes = [AllowAny]

    @extend_schema(request=None, responses={204: None})
    def post(self, request):
        dj_logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class ApiMe(APIView):
    permission_classes = [AllowAny]

    @extend_schema(responses={200: sz.UserPublic, 401: OpenApiResponse(description="Not authenticated.")})
    def get(self, request):
        if isinstance(request.user, AnonymousUser):
            return Response({"detail": "Not authenticated."}, status=status.HTTP_401_UNAUTHORIZED)
        return Response(sz.UserPublic(request.user).data)


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    required_capability = Capability.MANAGE_ITEMS
    http_method_names = ["get", "post", "patch", "head", "options"]

    def get_serializer_class(self):
        if self.action in ("create", "partial_update"):
            return sz.CategoryWrite
        return sz.CategoryRead

    def get_queryset(self):
        queryset = self.queryset
        active = self.request.query_params.get("active")
        if active is not None:
            queryset = queryset.filter(is_active=active == "true")
        return queryset


class LocationViewSet(viewsets.ModelViewSet):
    queryset = Location.objects.all()
    required_capability = Capability.MANAGE_ITEMS
    http_method_names = ["get", "post", "patch", "head", "options"]

    def get_serializer_class(self):
        if self.action in ("create", "partial_update"):
            return sz.LocationWrite
        return sz.LocationRead


class ItemViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.select_related("category", "unit")
    lookup_field = "sku"
    required_capability = Capability.MANAGE_ITEMS
    http_method_names = ["get", "post", "patch", "head", "options"]
    pagination_class = Page50

    def get_queryset(self):
        queryset = self.queryset
        search = self.request.query_params.get("search")
        if search:
            queryset = queryset.filter(
                Q(sku__icontains=search) | Q(name__icontains=search) | Q(category__name__icontains=search)
            )
        category = self.request.query_params.get("category")
        if category:
            queryset = queryset.filter(category_id=category)
        location = self.request.query_params.get("location")
        if location:
            queryset = queryset.filter(
                Q(stock_levels__location_id=location)
                | Q(
                    pk__in=Product.objects.filter(
                        stock_levels__product_id=F("pk"), stock_levels__location_id=location
                    )
                )
            )
        include_disabled = self.request.query_params.get("include_disabled") == "true"
        if not include_disabled:
            queryset = queryset.filter(is_active=True)
        return queryset.distinct()

    def get_serializer_class(self):
        if self.action in ("create", "partial_update"):
            return sz.ItemWrite
        return sz.ItemRead

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except ValidationError as exc:
            if self._sku_conflict(exc):
                raise Conflict({"sku": "SKU already exists."}) from exc
            raise
        serializer.save()
        item = serializer.instance
        return Response(sz.ItemRead(item).data, status=status.HTTP_201_CREATED)

    @staticmethod
    def _sku_conflict(exc):
        detail = exc.get_full_details().get("sku")
        if not detail:
            return False
        messages = detail if isinstance(detail, list) else [detail]
        return any("already exists" in str(m.get("message", m)) for m in messages)

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(sz.ItemRead(serializer.instance).data)

    @action(detail=True, methods=["post"], url_path="disable")
    def disable(self, request, sku=None):
        item = self.get_object()
        item.is_active = False
        item.save(update_fields=["is_active", "updated_at"])
        return Response(sz.ItemRead(item).data)


class StockLevelViewSet(viewsets.ModelViewSet):
    queryset = StockLevel.objects.select_related("product", "location", "product__category", "product__unit")
    serializer_class = sz.StockLevelRead
    required_capability = Capability.MANAGE_ITEMS
    http_method_names = ["get", "head", "options"]
    pagination_class = None

    def get_queryset(self):
        queryset = self.queryset
        item = self.request.query_params.get("item")
        if item:
            queryset = queryset.filter(product__sku=item)
        location = self.request.query_params.get("location")
        if location:
            queryset = queryset.filter(location_id=location)
        return queryset


class MovementViewSet(viewsets.ModelViewSet):
    queryset = StockMovement.objects.select_related("product", "location")
    serializer_class = sz.MovementRead
    required_capability = Capability.RECORD_MOVEMENTS
    http_method_names = ["get", "post", "head", "options"]
    pagination_class = Page50

    def get_queryset(self):
        queryset = self.queryset
        item = self.request.query_params.get("item")
        if item:
            queryset = queryset.filter(product__sku=item)
        location = self.request.query_params.get("location")
        if location:
            queryset = queryset.filter(location_id=location)
        flow = self.request.query_params.get("flow")
        if flow:
            queryset = queryset.filter(flow=flow)
        date_from = self.request.query_params.get("from")
        if date_from:
            queryset = queryset.filter(recorded_at__date__gte=date_from)
        date_to = self.request.query_params.get("to")
        if date_to:
            queryset = queryset.filter(recorded_at__date__lte=date_to)
        recorded_by = self.request.query_params.get("recorded_by")
        if recorded_by:
            queryset = queryset.filter(recorded_by_id=recorded_by)
        return queryset

    def create(self, request, *args, **kwargs):
        serializer = sz.MovementWrite(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        product = self._resolve_product(data["product"])
        try:
            flow = data["flow"]
            direction, quantity = self._resolve_direction(flow, data["quantity"])
            movement = MovementService().record(
                flow=flow,
                direction=direction,
                product=product,
                location=data["location"],
                quantity=abs(data["quantity"]),
                reason=data["reason"],
                recorded_by=request.user,
                request_override=data.get("override", False),
                reconciliation_ref=data.get("reconciliation_ref", ""),
                unit_cost=data.get("unit_cost"),
            )
        except OverIssueDenied as exc:
            raise Conflict(
                f"Available {exc.available}; shortfall {exc.shortfall}. Request override to continue."
            ) from exc
        except Exception as exc:
            raise self._validation_error(exc) from exc
        return Response(sz.MovementRead(movement).data, status=status.HTTP_201_CREATED)

    def _resolve_product(self, sku):
        try:
            return Product.objects.get(sku=sku)
        except Product.DoesNotExist:
            from rest_framework.exceptions import ValidationError

            raise ValidationError({"product": "Unknown SKU."}) from None

    def _resolve_direction(self, flow, quantity):
        if flow == StockMovement.Flow.RECEIPT.value:
            return StockMovement.Direction.IN, quantity
        if flow == StockMovement.Flow.ISSUE.value:
            return StockMovement.Direction.OUT, quantity
        if quantity > 0:
            return StockMovement.Direction.IN, quantity
        return StockMovement.Direction.OUT, quantity

    def _validation_error(self, exc):
        from rest_framework.exceptions import ValidationError

        detail = exc.message if hasattr(exc, "message") else str(exc)
        return ValidationError({"detail": detail})


class MovementConsent(APIView):
    required_capability = Capability.APPROVE_OVER_ISSUE

    @extend_schema(request=sz.ConsentWrite, responses=sz.MovementRead)
    def post(self, request, movement_id):
        serializer = sz.ConsentWrite(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            movement = MovementService().consent(
                movement_id, manager=request.user, approved=serializer.validated_data["approved"]
            )
        except Exception as exc:
            raise Conflict(str(exc)) from exc
        return Response(sz.MovementRead(movement).data)


class AlertList(APIView):
    required_capability = Capability.RECORD_MOVEMENTS

    @extend_schema(responses=sz.AlertSummary)
    def get(self, request):
        from apps.dashboard.services import build_alert_summary

        location = request.query_params.get("location")
        summary = build_alert_summary(location)
        return Response(_alert_payload(summary))


class ValuationReport(APIView):
    required_capability = Capability.VIEW_REPORTS

    @extend_schema(responses=sz.ValuationReport)
    def get(self, request):
        from apps.reports.services import build_valuation

        location = request.query_params.get("location")
        category = request.query_params.get("category")
        report = build_valuation(location=location, category=category)
        for row in report["rows"]:
            row["location"] = _location_data(row["location"])
        return Response(report)


class MovementsReport(APIView):
    required_capability = Capability.VIEW_REPORTS

    @extend_schema(responses=sz.MovementRead(many=True))
    def get(self, request):
        from apps.reports.services import movement_report

        queryset = movement_report(
            item=request.query_params.get("item"),
            location=request.query_params.get("location"),
            flow=request.query_params.get("flow"),
            date_from=request.query_params.get("from"),
        )
        return Response(sz.MovementRead(queryset[:1000], many=True).data)


class LowStockReport(APIView):
    required_capability = Capability.VIEW_REPORTS

    @extend_schema(responses=sz.AlertSummary)
    def get(self, request):
        from apps.dashboard.services import build_alert_summary

        return Response(_alert_payload(build_alert_summary(request.query_params.get("location"))))


def _alert_payload(summary):
    for bucket in ("low_stock", "out_of_stock"):
        for row in summary[bucket]:
            row["location"] = _location_data(row["location"])
    return summary


class UserViewSet(viewsets.ModelViewSet):
    queryset = UserModel.objects.all()
    required_capability = Capability.MANAGE_USERS
    http_method_names = ["get", "post", "patch", "head", "options"]

    def get_serializer_class(self):
        if self.action == "create":
            return sz.UserWrite
        if self.action == "role":
            return sz.RoleWrite
        return sz.UserAdmin

    @action(detail=True, methods=["patch"], url_path="role")
    def role(self, request, pk=None):
        user = self.get_object()
        serializer = sz.RoleWrite(user, data={"role": request.data.get("role")}, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(sz.UserAdmin(user).data)
