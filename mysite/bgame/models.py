# Delete the tables from this model: ./manage.py sqlclear bgame |./manage.py dbshell

from django.db import models
from django.contrib.auth.models import User


class ResourceType(models.Model):
    name = models.CharField(max_length=30, unique=True)
    default = models.IntegerField()

    def __unicode__(self):
        return self.name



class BuildingType(models.Model):
    name = models.CharField(max_length=30, unique=True)
    production = models.ForeignKey(ResourceType, related_name='production')

    resources = models.ManyToManyField(ResourceType, through='BuildingType_Resource')

    def __unicode__(self):
        return self.name


class BuildingType_Resource(models.Model):
    buildingType = models.ForeignKey(BuildingType)
    resourceType = models.ForeignKey(ResourceType)
    amount = models.IntegerField()




class Player(models.Model):
    name = models.CharField(max_length=30)
    user = models.OneToOneField(User)
    resources = models.ManyToManyField(ResourceType, through='Player_Resource')
    buildings = models.ManyToManyField(BuildingType, through='Player_Building')

    def __unicode__(self):
        return self.name


class Player_Resource(models.Model):
    player = models.ForeignKey(Player)
    resourceType = models.ForeignKey(ResourceType)
    amount = models.IntegerField()

class Player_Building(models.Model):
    player = models.ForeignKey(Player)
    buildingType = models.ForeignKey(BuildingType)
    quantity = models.IntegerField()


def tick():
    for player in Player.objects.all():
        for building in Player_Building.objects.filter(player=player):
            r = Player_Resource.objects.get(player=player, resourceType=building.buildingType.production)
            r.amount += 10 * building.quantity
            r.save()


def insertResource(name, default):
    obj, created = ResourceType.objects.get_or_create(name=name, defaults=dict(default=default))
    return obj


def insertBuilding(name, production, resources):
    try:
        obj = BuildingType.objects.get(name=name)
    except BuildingType.DoesNotExist, e:
        obj = BuildingType.objects.create(name=name, production=production)
        obj.save()

        for res, amount in resources.iteritems():
            rb = BuildingType_Resource(buildingType=obj, resourceType=res, amount=amount)
            rb.save()

        print '"%s" inserted'%name
    return obj


def insertPlayer(name, user):
    p = Player.objects.create(name=name, user=user)
    p.save()

    for res in ResourceType.objects.all():
        pr = Player_Resource(player=p, resourceType=res, amount=res.default)
        pr.save()

    print '%s inserted'%name
    return p


def addBuildingToPlayer(player, building, alterResources=True):
    if alterResources:
        res = alterResourcesForBuilding(player, building)
        if not res['success']:
            return res

    pb, created = Player_Building.objects.get_or_create(player=player, buildingType=building,
                                               defaults=dict(quantity=0))
    pb.quantity += 1
    pb.save()

    return {'success': True}


def alterResourcesForBuilding(player, building):
    for bRes in BuildingType_Resource.objects.filter(buildingType=building):
        pRes = Player_Resource.objects.get(player=player, resourceType=bRes.resourceType)
        if not pRes.amount >= bRes.amount:
            return {
                'success': False,
                'reason': 'not_enough_resources',
                'resource': bRes.resourceType.name,
            }
        else:
            pRes.amount -= bRes.amount
            pRes.save()

    return {'success': True}


def reset():
    BuildingType_Resource.objects.all().delete()
    BuildingType.objects.all().delete()
    Player_Resource.objects.all().delete()
    ResourceType.objects.all().delete()

    wood = insertResource('Wood', 100)
    stone = insertResource('Stone', 150)

    for player in Player.objects.all():
        Player_Resource.objects.create(player=player, resourceType=wood, amount=wood.default)
        Player_Resource.objects.create(player=player, resourceType=stone, amount=stone.default)

    woodcutter = insertBuilding('Woodcutter', wood, {stone: 20, wood: 15})
    quarry = insertBuilding('Quarry', stone, {stone: 10, wood: 25})



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