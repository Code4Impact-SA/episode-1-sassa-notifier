from django.contrib import admin
from .models import SassaApplication, SassaStatusCheck, SassaOutcome

@admin.register(SassaApplication)
class SassaApplicationAdmin(admin.ModelAdmin):
    list_display = ['user', 'app_id', 'id_number', 'phone_number', 'application_date']
    search_fields = ['user__username', 'id_number', 'phone_number']
    readonly_fields = ['application_date']


class SassaOutcomeInline(admin.TabularInline):
    model = SassaOutcome
    extra = 1


@admin.register(SassaStatusCheck)
class SassaStatusCheckAdmin(admin.ModelAdmin):
    list_display = ['application', 'status', 'checked_at', 'outcome_period']
    list_filter = ['application__user', 'status', 'checked_at']
    search_fields = ['application__user__username', 'application__id_number']
    date_hierarchy = 'checked_at'
    ordering = ['-checked_at']
    inlines = [SassaOutcomeInline] 

