import gamelib
import random
import math
import warnings
from sys import maxsize
import json


"""
Most of the algo code you write will be in this file unless you create new
modules yourself. Start by modifying the 'on_turn' function.

Advanced strategy tips:

  - You can analyze action frames by modifying on_action_frame function

  - The GameState.map object can be manually manipulated to create hypothetical
  board states. Though, we recommended making a copy of the map to preserve
  the actual current map state.
"""

class AlgoStrategy(gamelib.AlgoCore):
    def __init__(self):
        super().__init__()
        seed = random.randrange(maxsize)
        random.seed(seed)
        gamelib.debug_write('Random seed: {}'.format(seed))

    def on_game_start(self, config):
        """
        Read in config and perform any initial setup here
        """
        gamelib.debug_write('Configuring your custom algo strategy...')
        self.config = config
        global WALL, SUPPORT, TURRET, SCOUT, DEMOLISHER, INTERCEPTOR, MP, SP
        WALL = config["unitInformation"][0]["shorthand"]
        SUPPORT = config["unitInformation"][1]["shorthand"]
        TURRET = config["unitInformation"][2]["shorthand"]
        SCOUT = config["unitInformation"][3]["shorthand"]
        DEMOLISHER = config["unitInformation"][4]["shorthand"]
        INTERCEPTOR = config["unitInformation"][5]["shorthand"]
        MP = 1
        SP = 0
        # This is a good place to do initial setup
        self.scored_on_locations = []

    def on_turn(self, turn_state):
        """
        This function is called every turn with the game state wrapper as
        an argument. The wrapper stores the state of the arena and has methods
        for querying its state, allocating your current resources as planned
        unit deployments, and transmitting your intended deployments to the
        game engine.
        """
        game_state = gamelib.GameState(self.config, turn_state)
        gamelib.debug_write('Performing turn {} of your custom algo strategy'.format(game_state.turn_number))
        game_state.suppress_warnings(True)  #Comment or remove this line to enable warnings.

        self.starter_strategy(game_state)

        game_state.submit_turn()


    """
    NOTE: All the methods after this point are part of the sample starter-algo
    strategy and can safely be replaced for your custom algo.
    """

    def starter_strategy(self, game_state):
        """
        For defense we will use a spread out layout and some interceptors early on.
        We will place turrets near locations the opponent managed to score on.
        For offense we will use long range demolishers if they place stationary units near the enemy's front.
        If there are no stationary units to attack in the front, we will send Scouts to try and score quickly.
        """
        # First, place basic defenses

        if game_state.turn_number == 0:
            self.build_defensive_defences(game_state)
            self.twodemolishers(game_state)


        else:
            if game_state.turn_number % 3 !=0:
                self.build_defensive_defences(game_state)
                self.build_extra_defense(game_state)
                game_state.attempt_remove([[19, 9], [20, 9]])


            else:
                dem_spawn_location_options = [[16, 2]]
                best_location = self.least_damage_spawn_location(game_state, dem_spawn_location_options)
                game_state.attempt_spawn(DEMOLISHER, best_location, 3)
                scout_spawn_location_options = [[15, 1]]
                best_location = self.least_damage_spawn_location(game_state, scout_spawn_location_options)
                game_state.attempt_spawn(SCOUT, best_location, 1000)





    def build_defences(self, game_state):
        """
        Build basic defenses using hardcoded locations.
        Remember to defend corners and avoid placing units in the front where enemy demolishers can attack them.
        """
        # Useful tool for setting up your base locations: https://www.kevinbai.design/terminal-map-maker
        # More community tools available at: https://terminal.c1games.com/rules#Download

        # Place turrets that attack enemy units
        turret_locations = [[2, 11], [5, 11], [22, 11], [25, 11], [8, 8], [19, 8], [11, 5], [16, 5]]
        # attempt_spawn will try to spawn units if we have resources, and will check if a blocking unit is already there
        game_state.attempt_spawn(TURRET, turret_locations)

        # Place walls in front of turrets to soak up damage for them
        wall_locations = [[21, 11], [20, 10],[19, 9],[18, 8],[17, 7],[16, 6],[15, 5],[12, 5],[10, 7],[11, 6],[9, 8],[8, 9],[7, 10],[6, 11]]
        game_state.attempt_spawn(WALL, wall_locations)
        # upgrade walls so they soak more damage
        game_state.attempt_upgrade(wall_locations)

    def build_extra_defense(self, game_state):
        wall_locations = [[0, 13], [1, 13], [26, 13], [27, 13], [2, 12], [3, 12], [24, 12], [25, 12], [3, 11], [24, 11], [4, 10], [23, 10], [5, 9], [6, 9], [7, 9], [8, 9], [9, 9], [10, 9], [11, 9], [12, 9], [13, 9], [14, 9], [15, 9], [16, 9], [17, 9], [18, 9], [19, 9], [20, 9], [21, 9], [22, 9]]
        game_state.attempt_spawn(WALL, wall_locations)

        turret_locations = [[1, 12], [26, 12], [2, 11], [25, 11],[11, 8], [17, 8]]
        game_state.attempt_spawn(TURRET, turret_locations)

        extraTurrets = [[3, 10], [24, 10], [9, 8], [11, 8], [16, 8], [18, 8], [10, 3], [17, 3]]
        game_state.attempt_spawn(TURRET, extraTurrets)

        extraWalls = [[25,13],[23,11],[2,13],[4,11]]
        game_state.attempt_spawn(WALL, extraWalls)


    def stall_with_interceptors(self, game_state):
        """
        Send out interceptors at random locations to defend our base from enemy moving units.
        """
        # We can spawn moving units on our edges so a list of all our edge locations
        friendly_edges = game_state.game_map.get_edge_locations(game_state.game_map.BOTTOM_LEFT) + game_state.game_map.get_edge_locations(game_state.game_map.BOTTOM_RIGHT)

        # Remove locations that are blocked by our own structures
        # since we can't deploy units there.
        deploy_locations = self.filter_blocked_locations(friendly_edges, game_state)

        # While we have remaining MP to spend lets send out interceptors randomly.
        if game_state.get_resource(MP) >= (2*game_state.type_cost(INTERCEPTOR)[MP]):
            int_spawn_location_options = [[15, 1], [12, 1]]
            best_location = self.least_damage_spawn_location(game_state, int_spawn_location_options)
            game_state.attempt_spawn(INTERCEPTOR, best_location)
            """
            We don't have to remove the location since multiple mobile
            units can occupy the same space.
            """

    def holeattack(self, game_state):
        wallsloc = [[0, 13], [1, 13], [2, 13], [2, 12], [3, 12], [3, 11], [4, 10], [21, 10], [5, 9], [6, 9], [7, 9], [8, 9], [9, 9], [10, 9], [11, 9], [12, 9], [13, 9], [14, 9], [15, 9], [16, 9], [17, 9], [18, 9], [19, 9], [20, 9]]
        game_state.attempt_spawn(WALL, wallsloc)


        turretsloc = [[24, 13], [25, 13], [23, 12], [22, 11], [25, 11], [24, 10], [23, 9], [9, 8], [10, 8], [11, 8], [16, 8], [17, 8], [18, 8], [17, 3]]

        supportloc = [[19, 8], [18, 7], [17, 6], [17, 5], [17, 4]]


    def build_defensive_defences(self, game_state):
            turret_locations = [[1, 12], [26, 12],[11, 8], [17, 8]]
            # attempt_spawn will try to spawn units if we have resources, and will check if a blocking unit is already there
            game_state.attempt_spawn(TURRET, turret_locations)

            # Place walls in front of turrets to soak up damage for them
            wall_locations = [[0, 13], [1, 13], [26, 13], [27, 13], [2, 12], [3, 12], [24, 12], [25, 12], [3, 11], [24, 11], [4, 10], [23, 10], [5, 9], [6, 9], [7, 9], [10, 9], [11, 9], [12, 9], [16, 9], [17, 9], [18, 9], [20, 9], [21, 9], [22, 9]]
            game_state.attempt_spawn(WALL, wall_locations)



    def twodemolishers(self,game_state):
        friendly_edges = game_state.game_map.get_edge_locations(game_state.game_map.BOTTOM_LEFT) + game_state.game_map.get_edge_locations(game_state.game_map.BOTTOM_RIGHT)

        # Remove locations that are blocked by our own structures
        # since we can't deploy units there.
        deploy_locations = self.filter_blocked_locations(friendly_edges, game_state)

        best_location = self.least_damage_spawn_location(game_state, deploy_locations)
        game_state.attempt_spawn(DEMOLISHER, best_location, 2)


    def least_damage_spawn_location(self, game_state, location_options):
        """
        This function will help us guess which location is the safest to spawn moving units from.
        It gets the path the unit will take then checks locations on that path to
        estimate the path's damage risk.
        """
        damages = []
        # Get the damage estimate each path will take
        for location in location_options:
            path = game_state.find_path_to_edge(location)
            damage = 0
            for path_location in path:
                # Get number of enemy turrets that can attack each location and multiply by turret damage
                damage += len(game_state.get_attackers(path_location, 0)) * gamelib.GameUnit(TURRET, game_state.config).damage_i
            damages.append(damage)

        # Now just return the location that takes the least damage
        return location_options[damages.index(min(damages))]

    def detect_enemy_unit(self, game_state, unit_type=None, valid_x = None, valid_y = None):
        total_units = 0
        for location in game_state.game_map:
            if game_state.contains_stationary_unit(location):
                for unit in game_state.game_map[location]:
                    if unit.player_index == 1 and (unit_type is None or unit.unit_type == unit_type) and (valid_x is None or location[0] in valid_x) and (valid_y is None or location[1] in valid_y):
                        total_units += 1
        return total_units

    def filter_blocked_locations(self, locations, game_state):
        filtered = []
        for location in locations:
            if not game_state.contains_stationary_unit(location):
                filtered.append(location)
        return filtered

    def on_action_frame(self, turn_string):
        """
        This is the action frame of the game. This function could be called
        hundreds of times per turn and could slow the algo down so avoid putting slow code here.
        Processing the action frames is complicated so we only suggest it if you have time and experience.
        Full doc on format of a game frame at in json-docs.html in the root of the Starterkit.
        """
        # Let's record at what position we get scored on
        state = json.loads(turn_string)
        events = state["events"]
        breaches = events["breach"]
        for breach in breaches:
            location = breach[0]
            unit_owner_self = True if breach[4] == 1 else False
            # When parsing the frame data directly,
            # 1 is integer for yourself, 2 is opponent (StarterKit code uses 0, 1 as player_index instead)
            if not unit_owner_self:
                gamelib.debug_write("Got scored on at: {}".format(location))
                self.scored_on_locations.append(location)
                gamelib.debug_write("All locations: {}".format(self.scored_on_locations))


if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()
