from django.contrib.admin.widgets import (
    AutocompleteSelect,
    AutocompleteSelectMultiple,
)
from django import forms
from django.contrib import admin
from django.core.exceptions import ImproperlyConfigured
from django.db.models.fields.related_descriptors import (
    ManyToManyDescriptor,
    ReverseManyToOneDescriptor,
)
from django.forms.widgets import Media, MEDIA_TYPES


class AutocompleteFilterBase(admin.SimpleListFilter):
    template = 'django-admin-autocomplete-filter/autocomplete-filter.html'
    title = ''
    field_name = ''
    parameter_name = f'{field_name}__id__exact'
    is_placeholder_title = False
    widget_attrs = {}
    rel_model = None
    queryset_filter_kwargs = None
    widget_class = None
    form_field_class = None

    class Media:
        js = (
            'django-admin-autocomplete-filter/js/autocomplete_filter_qs.js',
        )
        css = {
            'screen': (
                'django-admin-autocomplete-filter/css/autocomplete-fix.css',
            ),
        }

    def __init__(self, request, params, model, model_admin):
        super().__init__(request, params, model, model_admin)

        if self.rel_model:
            model = self.rel_model

        remote_field, field_desc = self._get_remote_field(
            self.field_name, model)

        widget = self.widget_class(remote_field, model_admin.admin_site)

        try:
            # First try to get the related using logic from ManyToManyDescriptor; any of these accesses might fail
            related_model = field_desc.rel.related_model if field_desc.reverse else field_desc.rel.model
            queryset = related_model.objects.get_queryset()
        except:
            # Fall back to behavior that should work with ReverseManyToOneDescriptor created by ForeignKey
            queryset = field_desc.get_queryset()

        queryset = queryset.filter(**(self.queryset_filter_kwargs or {}))
        queryset |= queryset.model.objects.filter(id__in=self.value())

        field = self.form_field_class(
            queryset=queryset,
            widget=widget,
            required=False,
        )

        self._add_media(model_admin, widget)

        attrs = self.widget_attrs.copy()
        attrs['id'] = 'id-%s-dal-filter' % self.field_name
        if self.is_placeholder_title:
            # Upper case letter P as dirty hack for bypass django2 widget force placeholder value as empty string ("")
            attrs['data-Placeholder'] = self.title
        self.rendered_widget = field.widget.render(
            name=self.parameter_name,
            value=self.value(),
            attrs=attrs
        )

    def _get_remote_field(self, field_path, base_model):
        while '__' in field_path:
            section_path, field_path = field_path.split('__', 1)
            base_model = base_model._meta.get_field(section_path).remote_field.model
        remote_field = base_model._meta.get_field(field_path).remote_field
        field_desc = getattr(base_model, field_path)
        return remote_field, field_desc

    def get_queryset_for_field(self, model, name):
        field_desc = getattr(model, name)
        if isinstance(field_desc, ManyToManyDescriptor):
            related_model = field_desc.rel.related_model if field_desc.reverse else field_desc.rel.model
        elif isinstance(field_desc, ReverseManyToOneDescriptor):
            related_model = field_desc.rel.related_model
        else:
            return field_desc.get_queryset()
        return related_model.objects.get_queryset()

    def _add_media(self, model_admin, widget):

        if not hasattr(model_admin, 'Media'):
            raise ImproperlyConfigured('Add empty Media class to %s. Sorry about this bug.' % model_admin)

        def _get_media(obj):
            return Media(media=getattr(obj, 'Media', None))

        media = _get_media(model_admin) + widget.media + _get_media(AutocompleteFilter) + _get_media(self)

        for name in MEDIA_TYPES:
            setattr(model_admin.Media, name, getattr(media, "_" + name))

    def has_output(self):
        return True

    def lookups(self, request, model_admin):
        return ()

    def value(self):
        raise NotImplementedError()

    def queryset(self, request, queryset):
        for value in self.value():
            queryset = queryset.filter(**{self.parameter_name: value})
        return queryset


class AutocompleteFilter(AutocompleteFilterBase):
    widget_class = AutocompleteSelect
    form_field_class = forms.ModelChoiceField

    def value(self):
        return self.used_parameters.get(self.parameter_name, '')


class AutocompleteMultipleAllFilter(AutocompleteFilterBase):
    widget_class = AutocompleteSelectMultiple
    form_field_class = forms.ModelChoiceField

    def value(self):
        csv_ids = self.used_parameters.get(self.parameter_name, '')
        return csv_ids.split(',') if csv_ids else []


class AutocompleteMultipleAnyFilter(AutocompleteMultipleAllFilter):
    widget_class = AutocompleteSelectMultiple
    form_field_class = forms.ModelChoiceField

    def queryset(self, request, queryset):
        if not self.value():
            return queryset
        queryset = queryset.filter(**{self.parameter_name: self.value()})
        return queryset
