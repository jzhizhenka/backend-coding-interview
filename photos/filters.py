import django_filters

from .models import Photo


class PhotoFilter(django_filters.FilterSet):
    photographer_id = django_filters.NumberFilter(field_name="photographer_id")
    width_min = django_filters.NumberFilter(field_name="width", lookup_expr="gte")
    width_max = django_filters.NumberFilter(field_name="width", lookup_expr="lte")
    height_min = django_filters.NumberFilter(field_name="height", lookup_expr="gte")
    height_max = django_filters.NumberFilter(field_name="height", lookup_expr="lte")
    avg_color = django_filters.CharFilter(field_name="avg_color", lookup_expr="iexact")

    class Meta:
        model = Photo
        fields = ("photographer_id", "avg_color")
