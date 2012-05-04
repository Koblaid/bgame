from mysite.bgame import models
from django.contrib import admin

class BuildingType_Resource_Inline(admin.TabularInline):
    model = models.BuildingType_Resource
    extra = 1
    
class BuildingTypeAdmin(admin.ModelAdmin):
    inlines = [BuildingType_Resource_Inline]



class Resource_Inline(admin.TabularInline):
    model = models.Player_Resource
    extra = 1
    
class Building_Inline(admin.TabularInline):
    model = models.Player_Building
    extra = 1
    
class PlayerAdmin(admin.ModelAdmin):
    inlines = [Resource_Inline, Building_Inline]

    
admin.site.register(models.ResourceType)
admin.site.register(models.BuildingType, BuildingTypeAdmin)
admin.site.register(models.Player, PlayerAdmin)