from django.shortcuts import render_to_response, redirect, get_object_or_404
from django.template import RequestContext

from django.contrib.auth.models import User
from django.contrib.auth.views import login as login_view
from django.contrib.auth import login
from django.contrib import messages

from mysite.bgame import models as M


def index(request):
    if not request.user.is_authenticated():
        return redirect('mysite.bgame.views.custom_login', request)
    else:
        player = get_object_or_404(M.Player, user=request.user)

    d = {
        'buildings': M.Player_Building.objects.filter(player=player),
        'resources': M.Player_Resource.objects.filter(player=player),
        'building_types': M.BuildingType.getBuildingDetails(),
        'player': player,
    }
    return render_to_response('index.html', d, context_instance=RequestContext(request))


def custom_login(request):
    if request.user.is_authenticated():
        return redirect('mysite.bgame.views.index')
    else:
        return login_view(request, template_name='login.html')


def register(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password1']
        user = User.objects.create_user(username, 'a@b.de', password)
        user.backend='django.contrib.auth.backends.ModelBackend'
        M.Player.objects.create(name=username, user=user)
        login(request, user)
        return redirect('mysite.bgame.views.index', request)
    else:
        return render_to_response('register.html', context_instance=RequestContext(request))


def gameadmin(request):
    if 'tick' in request.POST:
        M.tick()
        messages.success(request, 'Tick ticked!')
    elif 'resetdb' in request.POST:
        M.reset()
        messages.success(request, 'DB resetted')

    return redirect('mysite.bgame.views.index')


def build(request):
    building_id = None
    for k in request.POST:
        if k.startswith('building_'):
            building_id = int(k.split('_')[1])

    if building_id is None:
        raise Exception

    building = get_object_or_404(M.BuildingType, id=building_id)
    player = get_object_or_404(M.Player, user=request.user)
    res = player.addBuilding(building)
    msg = ''
    if res['success']:
        messages.success(request, '%s was built'%building.name)
    else:
        if res['reason'] == 'not_enough_resources':
            msg = '%s could not be built, too few from %s'%(building.name, res['resource'])
            messages.error(request, msg)
        else:
            raise Exception('Unknown reason')

    return redirect('mysite.bgame.views.index')
