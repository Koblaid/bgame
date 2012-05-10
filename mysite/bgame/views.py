from django.shortcuts import render_to_response, redirect
from django.views.decorators.csrf import csrf_protect
from django.core.context_processors import csrf

from django.contrib.auth.models import User
from django.contrib.auth.views import login as login_view
from django.contrib.auth import login

from mysite.bgame import models


def index(request, msg=None):
    if not request.user.is_authenticated():
        return redirect('/', request)
    else:
        player = models.Player.objects.get(user=request.user)
    
    resourceOrder = 'name'
    buildingTypes = {}
    for bType in models.BuildingType.objects.all():
        bDict = {}
        bDict['id'] = bType.id
        bDict['production'] = bType.production.name
        bDict['resources'] = []
        
        for res in models.ResourceType.objects.order_by(resourceOrder):
            bDict['resources'].append(
                models.BuildingType_Resource.objects.get(buildingType=bType ,resourceType=res).amount
            )
            
        buildingTypes[bType.name] = bDict
        
    d = {
        'buildings': models.Player_Building.objects.filter(player=player),
        'resources': models.Player_Resource.objects.filter(player=player),
        'building_types': buildingTypes,
        'resource_types': models.ResourceType.objects.order_by(resourceOrder),
        'msg': msg,
        'player': player,
    }
    d.update(csrf(request))
    return render_to_response('index.html', d)    


def custom_login(request):
    if request.user.is_authenticated():
        return redirect('/game', request)
    else:
        return login_view(request, template_name='login.html')


def register(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password1']
        user = User.objects.create_user(username, 'a@b.de', password)
        user.backend='django.contrib.auth.backends.ModelBackend'
        models.insertPlayer(username, user)
        login(request, user)
        return redirect('/game', request)
    else:
        d = {}
        d.update(csrf(request))
        return render_to_response('register.html', d)


def gameadmin(request):
    if 'tick' in request.POST:
        models.tick()
        msg = 'Tick ticked!'
    elif 'resetdb' in request.POST:
        models.reset()
        msg = 'DB resetted'
    else:
        msg = ''
    
    return index(request, msg)
        
        
def build(request):
    building_id = None
    for k in request.POST:
        if k.startswith('building_'):
            building_id = int(k.split('_')[1])
    
    if building_id is None:
        raise Exception
    
    building = models.BuildingType.objects.get(id=building_id)
    player = models.Player.objects.get(user=request.user)
    print player
    res = models.addBuildingToPlayer(player, building)
    if res['success']:
        msg = '%s was built'%building.name
    else:
        if res['reason'] == 'not_enough_resources':
            msg = '%s could not be built, too few from %s'%(building.name, res['resource'])
        else:
            raise Exception('Unknown reason')
        
    return index(request, msg)