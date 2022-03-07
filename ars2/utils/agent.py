import math
import numpy as np

from utils.motion_model import MotionModel
from utils.sensor_model import SensorModel

from utils.object import Object
from utils.vector import Vector, Point

import sys
from ann.ann import Neural_Network



class Agent():
    def __init__(self, map = None, radius = None, start_pos_index = None):
        if map == None or radius == None or start_pos_index == None:
            print("SPECIFY MAP, RADIUS AND START_POS_INDEX FOR AGENT!")
            sys.exit()

        self.position = map["start_points"][start_pos_index]
        self.theta = 0
        self.radius = radius
        self.fitness = 0

        self.map = map

        self.motion_model = MotionModel(self.radius * 2, self.map["map"])
        self.sensor_model = SensorModel(self.position, self.theta, self.radius,
                                        self.map["map"],12,100)

        # Radius Bound is a horizontal vector
        self.circleObject = Object(self.position, [Vector(Point(0, 0), Point(self.radius, 0))], type="circle")

        # Create object line that will serve as vision. By default we put the cast to be twice the agent's radius
        self.lineObject = Object(self.position, [Vector(Point(0, 0), Point(self.radius, 0))], type="line")

        self.speed_increment = 1
        self.agent_actions = {
            "w": (self.motion_model.update_speed, [self.speed_increment, 0]),
            "s": (self.motion_model.update_speed, [-self.speed_increment, 0]),
            "o": (self.motion_model.update_speed, [0, self.speed_increment]),
            "l": (self.motion_model.update_speed, [0, -self.speed_increment]),
            "x": (self.motion_model.reset_speed, []),
            "t": (self.motion_model.update_speed, [self.speed_increment, self.speed_increment]),
            "g": (self.motion_model.update_speed, [-self.speed_increment, -self.speed_increment]),
        }

        # Create Neural Network with 14 input nodes (12 sensors + 2 timesteps) and 2 output nodes for the motors
        self.ann = Neural_Network()
        self.network = self.ann.initialize_random_network(16,2) # By default do random network

    def get_map(self):
        return self.map


    def ann_controller_run(self):
        self.set_speed(1,1)    

    def set_speed(self, vr, vl):
        self.motion_model.update_speed(vr, vl)

    # This loop will be the agent's own controller
    # The ANN will be controlled from here
    def loop_agent(self, timesteps):
        #output = self.motion_model.get_speeds()

        # This is the output of our hidden layer initialized to 0 for the first iteration
        hidden_layer = [0,0,0,0]

        for i in range(timesteps):
            print("- Iteration " + str(i))

            input_layer = []
            for d in self.sensor_model.get_sensor_distances():
                input_layer.append(d)
            input_layer.append(hidden_layer[0])
            input_layer.append(hidden_layer[1])
            input_layer.append(hidden_layer[2])
            input_layer.append(hidden_layer[3])


            print(input_layer)


            output = self.ann.forward_propagation(input_layer)
            left_motor = output[0]
            right_motor = output[1]
            print(output)

            hidden_layer = self.ann.hidden_layer_values

            # Move backward, forward, or nothing
            if left_motor < 0.5:
                self.move_agent("l")
            else:
                self.move_agent("o")

            if right_motor < 0.5:
                self.move_agent("s")
            else:
                self.move_agent("w")

            self.update()


            # Increment metrics for Fitness function here such as amount of dust sucked:
            if len(self.motion_model.get_collisions()) == 0: # and left_motor > 0 and right_motor > 0:
                print("UPDATE FITNESS")
                #self.fitness = self.fitness + 1




    # Passes an action parameter to move the agent according to the output weights of the ANN
    def move_agent(self, action):
        if action == "w":
            self.motion_model.update_speed(self.speed_increment, 0)
        elif action == "s":
            self.motion_model.update_speed(-self.speed_increment, 0)
        elif action == "o":
            self.motion_model.update_speed(0, self.speed_increment)
        elif action == "l":
            self.motion_model.update_speed(0, -self.speed_increment)
        elif action == "x":
            self.motion_model.update_speed()
        elif action == "t":
            self.motion_model.update_speed(self.speed_increment, self.speed_increment)
        elif action == "g":
            self.motion_model.update_speed(-self.speed_increment, -self.speed_increment)

    def set_network_weights(self, network):
        self.network = self.ann.initialize_network(network)

    def get_circle_coordinates(self):
        return self.position

    def get_line_coordinates(self):
        return self.lineObject.get_ui_coordinates()

    def get_vision_lines(self):
        lines = self.sensor_model.get_sensor_lines()
        dist = self.sensor_model.get_sensor_distances()
        return (lines, dist)

    def is_agent_moving(self):
        return self.motion_model.is_moving()

    def get_speeds(self):
        return self.motion_model.get_speeds()

    def update_agent_objects(self, new_position, new_theta):
        # Update agent line
        self.lineObject.update_coordinates(new_position)
        if new_theta != self.theta:
            self.lineObject.rotate(new_theta)

        # Update agent circle 
        self.circleObject.update_coordinates(new_position)

    def update(self):
        # Update motion model
        (new_position, new_theta, change) = self.motion_model.update(self.position, self.theta)
        
        # If there is no change in movement, then just skip the update
        if change == False:
            return
        self.update_agent_objects(new_position, new_theta)


        # Update the sensor model
        self.sensor_model.update(new_position, new_theta)

        self.fitness += (abs(self.position.X - new_position.X) + abs(self.position.Y - new_position.Y))

        self.theta = new_theta
        self.position = new_position

    def on_key_press(self, key):
        # React to the key press
        try:
            action, args = self.agent_actions[key]
            action(*args)
        except Exception:
            # ignore it
            pass
