# Delete the tables from this model: ./manage.py sqlclear bgame |./manage.py dbshell

from django.db import models
from django.contrib.auth.models import User
from django.db import transaction


class ResourceType(models.Model):
    name = models.CharField(max_length=30, unique=True)
    default = models.IntegerField()

    def __unicode__(self):
        return self.name



class BuildingType(models.Model):
    name = models.CharField(max_length=30, unique=True)
    production = models.ForeignKey(ResourceType, verbose_name='Resource production', related_name='production')

    resources = models.ManyToManyField(ResourceType, through='BuildingType_Resource')

    def __unicode__(self):
        return self.name

    @classmethod
    def createBuilding(cls, name, production, resources):
        obj = cls.objects.create(name=name, production=production)
        obj.save()

        for res, amount in resources.iteritems():
            rb = BuildingType_Resource(buildingType=obj, resourceType=res, amount=amount)
            rb.save()
        return obj

    @classmethod
    def getBuildingDetails(cls):
        '''
        select b.name, b.id, r2.name, r.name, br.amount

        from bgame_resourcetype r
        join bgame_buildingtype_resource br on r.id = br.resourcetype_id
        join bgame_buildingtype b on b.id = br.buildingtype_id
        join bgame_resourcetype r2 on b.production_id = r2.id
        order by b.name
        '''

        buildingTypes = []
        for bType in cls.objects.all():
            resList = []
            for res in ResourceType.objects.all():
                try:
                    amount = BuildingType_Resource.objects.get(buildingType=bType ,resourceType=res).amount
                except BuildingType_Resource.DoesNotExist:
                    amount = 0
                resList.append(dict(
                    name=res.name,
                    amount=amount
                ))

            buildingTypes.append(dict(
                name = bType.name,
                id = bType.id,
                production = bType.production.name,
                resources = resList
            ))
        return buildingTypes


class BuildingType_Resource(models.Model):
    class Meta:
        verbose_name = "Building cost"

    buildingType = models.ForeignKey(BuildingType)
    resourceType = models.ForeignKey(ResourceType, verbose_name = 'Resource')
    amount = models.IntegerField()

    def __unicode__(self):
        return ''



class Player(models.Model):
    name = models.CharField(max_length=30)
    user = models.OneToOneField(User)
    resources = models.ManyToManyField(ResourceType, through='Player_Resource')
    buildings = models.ManyToManyField(BuildingType, through='Player_Building')

    def __unicode__(self):
        return self.name

    def getResource(self, resourceType):
        obj, created = Player_Resource.objects.get_or_create(resourceType=resourceType,
                                                             player=self,
                                                             defaults=dict(amount=resourceType.default))
        return obj

    def getResource(self, resourceType):
        obj, created = Player_Resource.objects.get_or_create(resourceType=resourceType,
                                                             player=self,
                                                             defaults=dict(amount=resourceType.default))
        return obj

    def getResources(self):
        resList = []
        for res in ResourceType.objects.all():
            resList.append(self.getResource(res))
        return resList

    def changeResourceAmount(self, resourceType, amount):
        resource = self.getResource(resourceType)
        if not resource.amount+amount >= 0:
            return {'success': False}
        else:
            resource.amount += amount
            resource.save()
            return {'success': True}
    changeResourceAmount.alters_data = True

    def subtractResourcesForBuilding(self, buildingType):
        assert transaction.is_managed()
        for bRes in BuildingType_Resource.objects.select_for_update().filter(buildingType=buildingType):
            result = self.changeResourceAmount(bRes.resourceType, bRes.amount*-1)
            if not result['success']:
                return {
                    'success': False,
                    'reason': 'not_enough_resources',
                    'resource': bRes.resourceType.name,
                }

        return {'success': True}
    subtractResourcesForBuilding.alters_data = True


    def addBuilding(self, buildingType, subtractResources=True):
        if subtractResources:
            res = self.subtractResourcesForBuilding(buildingType)
            if not res['success']:
                return res

        pb, created = Player_Building.objects.get_or_create(player=self, buildingType=buildingType,
                                                            defaults=dict(quantity=0))
        pb.quantity += 1
        pb.save()

        return {'success': True}
    addBuilding.alters_data = True



class Player_Resource(models.Model):
    class Meta:
        verbose_name = 'Resource'

    player = models.ForeignKey(Player)
    resourceType = models.ForeignKey(ResourceType, verbose_name='Resource')
    amount = models.IntegerField()

    def __unicode__(self):
        return ''


class Player_Building(models.Model):
    class Meta:
        verbose_name = 'Building'

    player = models.ForeignKey(Player)
    buildingType = models.ForeignKey(BuildingType, verbose_name='Building')
    quantity = models.IntegerField()

    def __unicode__(self):
        return ''


def tick():
    for player in Player.objects.all():
        for building in Player_Building.objects.filter(player=player):
            amount = 10 * building.quantity
            result = player.changeResourceAmount(building.buildingType.production, amount)
            assert(result['success'])






def reset():
    BuildingType_Resource.objects.all().delete()
    BuildingType.objects.all().delete()
    Player_Resource.objects.all().delete()
    ResourceType.objects.all().delete()

    wood, created = ResourceType.objects.get_or_create(name='Wood', default=100)
    stone, created = ResourceType.objects.get_or_create(name='Stone', default=150)

    woodcutter = BuildingType.createBuilding('Woodcutter', wood, {stone: 20, wood: 15})
    quarry = BuildingType.createBuilding('Quarry', stone, {stone: 10, wood: 25})



'''
create table building_type (
  id                       int,
  name                     text,
  longhouse_lvl            int,
  max_lvl			       int,
  people_working_per_lvl   int,

  -- allowedMaxLvl = thisFactor * currentLvl
  longhouse_diff_factor    int,

  -- produktion mit einer ausbaustufe pro arbeiter
  base_production          int,
  -- produktion = anzahl der arbeiter * base_produktion

  max_building_count       int,
  building_time            int
);

create table longhouse_inhabitants (
  lvl                       int,
  numInhabitants            int
);


-- die ausbaukosten des langhauses haengen von der einwohnerzahl ab
-- die ausbaukosten der restlichen bewohner haengen von dem lvl ab
create table resource (
  id                int,
  name              text
);


create table building_resource (
  building_id          int,
  resource_id          int,

  -- ab diesem lvl wird der rohstoff benoetigt
  start_lvl            int,
  -- mit diesem factor wird der rohstoffbedarf pro lvl berechnet
  start_factor         int,
  -- um diesen wert steigt der factor pro lvl an
  factor_delta		   int
);'''