from django.shortcuts import render_to_response, redirect, get_object_or_404
from django.template import RequestContext

from django.contrib.auth.models import User
from django.contrib.auth.views import login as login_view
from django.contrib.auth import login
from django.contrib import messages

from mysite.bgame import models


def index(request):
    if not request.user.is_authenticated():
        return redirect('/', request)
    else:
        player = get_object_or_404(models.Player, user=request.user)
    
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
        'player': player,
    }
    return render_to_response('index.html', d, context_instance=RequestContext(request))


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
        return render_to_response('register.html', context_instance=RequestContext(request))


def gameadmin(request):
    if 'tick' in request.POST:
        models.tick()
        messages.success(request, 'Tick ticked!')
    elif 'resetdb' in request.POST:
        models.reset()
        messages.success(request, 'DB resetted')
    
    return redirect('/game')
        
        
def build(request):
    building_id = None
    for k in request.POST:
        if k.startswith('building_'):
            building_id = int(k.split('_')[1])
    
    if building_id is None:
        raise Exception
    
    building = get_object_or_404(models.BuildingType, id=building_id)
    player = get_object_or_404(models.Player, user=request.user)
    res = models.addBuildingToPlayer(player, building)
    msg = ''
    if res['success']:
        messages.success(request, '%s was built'%building.name)
    else:
        if res['reason'] == 'not_enough_resources':
            msg = '%s could not be built, too few from %s'%(building.name, res['resource'])
            messages.error(request, msg)
        else:
            raise Exception('Unknown reason')
        
    return redirect('/game')
