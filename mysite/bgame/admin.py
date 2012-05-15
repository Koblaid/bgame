from django.contrib import admin

from mysite.bgame import models as M


class BuildingType_Resource_Inline(admin.TabularInline):
    model = M.BuildingType_Resource
    extra = 1

class BuildingTypeAdmin(admin.ModelAdmin):
    inlines = [BuildingType_Resource_Inline]



class Resource_Inline(admin.TabularInline):
    model = M.Player_Resource
    extra = 1

class Building_Inline(admin.TabularInline):
    model = M.Player_Building
    extra = 1

class PlayerAdmin(admin.ModelAdmin):
    inlines = [Resource_Inline, Building_Inline]


admin.site.register(M.ResourceType)
admin.site.register(M.BuildingType, BuildingTypeAdmin)
admin.site.register(M.Player, PlayerAdmin)