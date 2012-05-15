from django.test import TestCase as Dj_TestCase
from django.utils.unittest import TestCase
from django.test.client import RequestFactory
from django.contrib.auth.models import User

from django_webtest import WebTest

import models as M



class TestTools(object):
    def assertDict(self, expected, d, dictKey):
        self.assertIsInstance(d, dict)
        self.assertIn(dictKey, d)
        self.assertEqual(expected, d[dictKey])


    def assertSuccess(self, d):
        self.assertDict(True, d, 'success')


    def assertNotSuccess(self, d):
        self.assertDict(False, d, 'success')


    def createPlayer(self, name, password=None):
        user = User.objects.create_user(name, 'a@b.de', password)
        return M.Player.objects.create(name=name, user=user)


    def createResources(self, *namesDefaultTuple):
        res = []
        for name, default in namesDefaultTuple:
            res.append(M.ResourceType.objects.create(name=name, default=default))
        return res



class Test_Player_AddBuilding(Dj_TestCase, TestTools):
    def setUp(self):
        self.wood, self.stone = self.createResources(('Wood', 0), ('Stone', 0))
        self.woodcutter = M.BuildingType.createBuilding('Woodcutter', self.wood, {self.wood: 10, self.stone:50})
        self.quarry = M.BuildingType.createBuilding('Quarry', self.stone, {self.wood: 100, self.stone:30})
        self.player = self.createPlayer('Ben')


    def test_tooFewResources(self):
        # build one building => error, not enough resources
        result = self.player.addBuilding(self.woodcutter)
        self.assertNotSuccess(result)
        self.assertDict('not_enough_resources', result, 'reason')
        self.assertIn('resource', result)


    def checkBuilding(self, buildingType, quantity):
        buildings = M.Player_Building.objects.all()
        self.assertEqual(1, len(buildings))
        self.assertEqual(buildingType, buildings[0].buildingType)
        self.assertEqual(self.player, buildings[0].player)
        self.assertEqual(quantity, buildings[0].quantity)


    def test_addBuildingWithoutResourceChange(self):
        result = self.player.addBuilding(self.woodcutter, subtractResources=False)
        self.assertSuccess(result)
        self.checkBuilding(self.woodcutter, 1)


    def test_addBuilding(self):
        # increase resources for player
        self.player.changeResourceAmount(self.wood, 1000)
        self.player.changeResourceAmount(self.stone, 1500)

        # build one building
        result = self.player.addBuilding(self.woodcutter)
        self.assertSuccess(result)
        self.checkBuilding(self.woodcutter, 1)

        # Check subtraction of resources
        self.assertEqual(1000-10, self.player.getResource(self.wood).amount)
        self.assertEqual(1500-50, self.player.getResource(self.stone).amount)

    def test_multipleBuildings(self):
        result = self.player.addBuilding(self.woodcutter, subtractResources=False)
        result = self.player.addBuilding(self.woodcutter, subtractResources=False)
        self.assertSuccess(result)
        self.checkBuilding(self.woodcutter, 2)

        # Build 3 buildings of another type
        result = self.player.addBuilding(self.quarry, subtractResources=False)
        self.assertSuccess(result)
        result = self.player.addBuilding(self.quarry, subtractResources=False)
        self.assertSuccess(result)
        result = self.player.addBuilding(self.quarry, subtractResources=False)
        self.assertSuccess(result)

        buildings = M.Player_Building.objects.all()
        self.assertEqual(2, len(buildings))
        quarryPlayer = M.Player_Building.objects.filter(buildingType=self.quarry)
        self.assertEqual(1, len(quarryPlayer))
        self.assertEqual(3, quarryPlayer[0].quantity)




class Test_BuildingType_getBuildingDetails(Dj_TestCase, TestTools):
    def test_(self):
        wood, stone = self.createResources(('Wood', 0), ('Stone', 0))
        woodcutter = M.BuildingType.createBuilding('Woodcutter', wood, {wood: 10, stone:50})
        quarry = M.BuildingType.createBuilding('Quarry', stone, {wood: 100})
        details = M.BuildingType.getBuildingDetails()
        self.assertEqual(2, len(details))

        expected = [
            dict(
                id=woodcutter.id,
                name='Woodcutter',
                production='Wood',
                resources=[
                    dict(name='Wood', amount=10),
                    dict(name='Stone', amount=50),
                ]),
            dict(
                id=quarry.id,
                name='Quarry',
                production='Stone',
                resources=[
                    dict(name='Wood', amount=100),
                    dict(name='Stone', amount=0),
                ]),
        ]
        self.assertEqual(details, expected)


class Test_Player_changeResourceAmount(Dj_TestCase, TestTools):
    def setUp(self):
        self.wood, self.stone = self.createResources(('Wood', 100), ('Stone', 150))
        self.player = self.createPlayer('Ben')

    def test_init(self):
        self.assertEqual(100, self.player.getResource(self.wood).amount)
        self.assertEqual(150, self.player.getResource(self.stone).amount)

    def test_addAmount(self):
        result = self.player.changeResourceAmount(self.wood, 10)
        self.assertSuccess(result)
        self.assertEqual(110, self.player.getResource(self.wood).amount)
        self.assertEqual(150, self.player.getResource(self.stone).amount)

    def test_subtractAmount(self):
        result = self.player.changeResourceAmount(self.wood, -100)
        self.assertSuccess(result)
        self.assertEqual(0, self.player.getResource(self.wood).amount)
        self.assertEqual(150, self.player.getResource(self.stone).amount)

    def test_subtractTooMuch(self):
        result = self.player.changeResourceAmount(self.wood, -110)
        self.assertNotSuccess(result)
        self.assertEqual(100, self.player.getResource(self.wood).amount)
        self.assertEqual(150, self.player.getResource(self.stone).amount)



class ModelTests(Dj_TestCase, TestTools):
    def test_buildingType_createBuilding(self):
        wood, stone = self.createResources(('Wood', 100), ('Stone', 150))

        # Create 2 buildings
        woodcutter = M.BuildingType.createBuilding('Woodcutter', wood, {wood: 10, stone:50})
        quarry = M.BuildingType.createBuilding('Quarry', stone, {wood: 100, stone:30})

        self.assertEqual(wood, woodcutter.production)
        self.assertEqual(1, len(M.BuildingType_Resource.objects.filter(buildingType=woodcutter, resourceType=wood, amount=10)))
        self.assertEqual(1, len(M.BuildingType_Resource.objects.filter(buildingType=woodcutter, resourceType=stone, amount=50)))

        self.assertEqual(stone, quarry.production)
        self.assertEqual(1, len(M.BuildingType_Resource.objects.filter(buildingType=quarry, resourceType=wood, amount=100)))
        self.assertEqual(1, len(M.BuildingType_Resource.objects.filter(buildingType=quarry, resourceType=stone, amount=30)))


    def test_player_getResource(self):
        wood, stone = self.createResources(('Wood', 100), ('Stone', 150))
        player = self.createPlayer('Ben')

        # No resources yet
        self.assertEqual(0, len(M.Player_Resource.objects.filter(player=player)))

        # Get resources (will create resources implicit)
        playerWood = player.getResource(wood)
        playerStone = player.getResource(stone)
        self.assertEqual(wood.default, playerWood.amount)
        self.assertEqual(stone.default, playerStone.amount)

        # Now two resources must be present for this player
        self.assertEqual(2, len(M.Player_Resource.objects.filter(player=player)))

        # Get a resource the second time. This time it must not be created
        playerWood2 = player.getResource(wood)
        self.assertEqual(2, len(M.Player_Resource.objects.filter(player=player)))


    def test_tick(self):
        wood, stone = self.createResources(('Wood', 0), ('Stone', 0))
        woodcutter = M.BuildingType.createBuilding('Woodcutter', wood, {wood: 10, stone:50})
        quarry = M.BuildingType.createBuilding('Quarry', stone, {wood: 100, stone:30})

        ben1 = self.createPlayer('Ben1')

        result = ben1.addBuilding(woodcutter, subtractResources=False)
        self.assertSuccess(result)
        result = ben1.addBuilding(woodcutter, subtractResources=False)
        self.assertSuccess(result)

        result = ben1.addBuilding(quarry, subtractResources=False)
        self.assertSuccess(result)
        result = ben1.addBuilding(quarry, subtractResources=False)
        self.assertSuccess(result)
        result = ben1.addBuilding(quarry, subtractResources=False)
        self.assertSuccess(result)

        ben2 = self.createPlayer('Ben2')

        M.tick()

        self.assertEqual(10+10, ben1.getResource(wood).amount)
        self.assertEqual(10+10+10, ben1.getResource(stone).amount)

        self.assertEqual(0, ben2.getResource(wood).amount)
        self.assertEqual(0, ben2.getResource(stone).amount)



class FunctionalTests(WebTest, TestTools):
    def test_index(self):
        request = self.app.get('/')
        self.assertTemplateUsed(request, 'login.html')

    def test_bgame_withoutLogin(self):
        request = self.app.get('/game')
        self.assertRedirects(request, '/')

    def test_login_error(self):
        form = self.app.get('/').form
        form['username'] = 'XXX'
        form['password'] = 'YYY'
        res = form.submit()
        self.assertIn("Your username and password didn't match. Please try again.", res)

    def test_login_success(self):
        self.createPlayer('Ben', 'xxx')
        form = self.app.get('/').form
        form['username'] = 'Ben'
        form['password'] = 'xxx'
        res1 = form.submit()
        res2 = res1.follow()
        self.assertTemplateUsed(res2, 'index.html')

    def test_logout(self):
        self.createPlayer('Ben', 'xxx')
        res1 = self.app.get('/game', user='Ben')
        res2 = res1.click(href='/logout')
        res3 = res2.follow()
        self.assertTemplateUsed(res3, 'login.html')

    def test_registration_login(self):
        form = self.app.get('/register').form
        form['username'] = 'Ben'
        form['password1'] = 'yyy'
        res1 = form.submit()
        res2 = res1.follow()
        self.assertTemplateUsed(res2, 'index.html')

    def test_tick(self):
        # Prepare
        wood, stone = self.createResources(('Wood', 0), ('Stone', 0))
        woodcutter = M.BuildingType.createBuilding('Woodcutter', wood, {wood: 10, stone:50})
        ben = self.createPlayer('Ben')
        res = ben.addBuilding(woodcutter, subtractResources=False)
        self.assertSuccess(res)
        res = ben.addBuilding(woodcutter, subtractResources=False)
        self.assertSuccess(res)

        # Form submit
        res = self.app.get('/game', user='Ben')
        form = res.forms['gameadmin']
        res = form.submit('tick')

        # Checks
        res = res.follow()
        self.assertContains(res, 'dj_msg success')
        self.assertEqual(20, ben.getResource(wood).amount)

    def test_build(self):
        # Prepare
        wood, stone = self.createResources(('Wood', 10), ('Stone', 50))
        woodcutter = M.BuildingType.createBuilding('Woodcutter', wood, {wood: 10, stone:50})
        ben = self.createPlayer('Ben')

        # Form submit
        res = self.app.get('/game', user='Ben')
        form = res.forms['build']
        res = form.submit('building_1')

        # Checks
        res = res.follow()
        self.assertContains(res, 'dj_msg success')
        buildings = M.Player_Building.objects.filter(player=ben)
        self.assertEqual(1, len(buildings))
        self.assertEqual('Woodcutter', buildings[0].buildingType.name)

    def test_build_error(self):
        # Prepare
        wood, stone = self.createResources(('Wood', 0), ('Stone', 0))
        woodcutter = M.BuildingType.createBuilding('Woodcutter', wood, {wood: 10, stone:50})
        ben = self.createPlayer('Ben')

        # Form submit
        res = self.app.get('/game', user='Ben')
        form = res.forms['build']
        res = form.submit('building_1')

        # Checks
        res = res.follow()
        self.assertContains(res, 'dj_msg error')
        buildings = M.Player_Building.objects.filter(player=ben)
        self.assertEqual(0, len(buildings))

