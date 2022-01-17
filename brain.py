import enum
import random
from typing import Union, TYPE_CHECKING

import numpy as np

random = random.Random()

random.seed(1)

if TYPE_CHECKING:
    from main import Board
    from creature import Creature


class Rotation(enum.Enum):
    Up = 0
    Right = 1
    Down = 2
    Left = 3


"""
This is the brain creatures use to think

Sensory neurons:
Age = age
Rnd = random input
Osc = oscillator
Pop = population density near the creature
Cfd = distance to the nearest creature in front of the creature 
Bfd = distance to the border in front of the creature 

LMy = last movement y 
LMx = last movement x
BDx = distance to closest border on x axis
BDy = distance to closest border on y axis
Lx = location x
Ly = location y 

Action outputs:
OSC = Set oscillator period
Mrn = move random
Mfd = move forward (last direction of movement)
Mrv = move reverse 
MLR = move left/right (+/-)
MX = move along the x axis (+/-)
MY = move along the y axis (+/-) 
"""


class SensoryNeuronType(enum.Enum):
    Age = 0
    Rnd = 1
    Osc = 2
    Pop = 3
    Cfd = 4
    Bfd = 5
    LMy = 6
    LMx = 7
    BDx = 8
    BDy = 9
    Lx = 10
    Ly = 11


class ActionNeuronType(enum.Enum):
    OSC = 12
    Mrn = 13
    Mfd = 14
    Mrv = 15
    MLR = 16
    MX = 17
    MY = 18


SensoryNeuronTypes = [item.value for item in SensoryNeuronType]
ActionNeuronTypes = [item.value for item in ActionNeuronType]


class Connection:
    @staticmethod
    def create_connection(inputs: list[int], weights: list[float], bias: float, output: int) -> "Connection":
        if len(inputs) != len(weights):
            raise Exception("Connection inputs and weights not the same length")
        connection = Connection()
        connection.inputs = inputs
        connection.output = output
        connection.weights = weights
        connection.bias = bias

        return connection

    @staticmethod
    def calculate_connection(connection: "Connection", inputs: list[float]) -> float:
        if len(connection.weights) != len(inputs):
            raise Exception("Connection values and weights not the same length")

        # I'm not sure if using matrices here was the best call,
        # but I have wis D and matrices are cool

        bias = connection.bias

        # This gets the list of weights, and makes it a matrix with a width of 1
        np_inputs = np.array(connection.weights)  # Makes it a numpy array
        np_weights = np_inputs.reshape(len(inputs), 1)  # Reshapes it to a matrix:
        # Example:
        # np.array([1, 2, 3, 4]).reshape((4, 1))
        # array([[1],
        #        [2],
        #        [3],
        #        [4]])

        # Now we make the inputs a matrix with a height of 1
        np_inputs = np.array(inputs)

        # And now we can the dot product:
        dot_product: float = np.dot(
            np_inputs,
            np_weights
        ).item(0)

        # Get the result by averaging the results over the inputs and adding the
        # bias to it.
        # After that constrain the result between -1 and +1 by using a hyperbolic tangent
        #
        # I used this as a guide
        # https://medium.com/coinmonks/the-mathematics-of-neural-network-60a112dd3e05
        # TODO: check if averaging it is actually needed

        result = np.tanh(
            dot_product / len(inputs)
            + bias
        )
        return result

    inputs: list[int]  # Connections use the index of a neuron in the neurons list
    output: int
    weights: list[float]
    bias: float


# todo: Create neurons that arent sensory or action neurons
def chance(value: float) -> bool:
    return value > random.random()


class Brain:
    creature: "Creature"
    sensory_neurons: list[Union[int]]
    action_neurons: list[Union[int]]
    connections: list[Connection]
    mutation_factor: float

    def __init__(self, creature: "Creature", connections: list[Connection], mutation_factor: float = 10):
        self.creature = creature
        self.mutation_factor = mutation_factor
        if not self.mutation_factor:
            self.mutation_factor = 10.0
        self.create_brain(connections)

    def create_brain(self, connections):
        self.connections = connections
        self.sensory_neurons = []
        self.action_neurons = []
        for sensory_type in SensoryNeuronTypes:
            self.sensory_neurons.append(sensory_type)
        for action_type in ActionNeuronTypes:
            self.action_neurons.append(action_type)
        if len(connections) < 1:
            self.create_random_connection()
            while chance(0.1):
                self.create_random_connection()
        else:
            self.mutate_connections()

    def create_random_connection(self):
        possible = list(range(len(self.sensory_neurons)))
        random.shuffle(possible)
        inputs: list[int] = [possible.pop()]
        weights: list[float] = [(random.random() - .5) * 2]

        while chance(0.3) and len(possible) >= 1:
            inputs.append(possible.pop())
            weights.append((random.random() - .5) * 2)

        connection = Connection.create_connection(
            inputs,
            weights,
            (random.random() - .5) * 2,
            random.randrange(0, len(self.action_neurons) - 1)
        )

        self.connections.append(connection)

    def mutate_connections(self):
        change_factor = 0.01 * self.mutation_factor
        for connection in self.connections:
            for weight_index, weight in enumerate(connection.weights):
                connection.weights[weight_index] = weight + weight * change_factor * (random.random() - 0.5)
                self.creature.mutate_color(1)
            connection.bias = connection.bias + connection.bias * change_factor * (random.random() - 0.5)
        if chance(0.01 * self.mutation_factor) and len(self.connections) > 1:
            self.creature.mutate_color()
            self.connections.pop(random.randrange(0, len(self.connections) - 0))
        if chance(0.01 * self.mutation_factor):
            self.creature.mutate_color()
            self.create_random_connection()
        self.mutation_factor = self.mutation_factor + change_factor * random.random()

    def think(self, board: "Board"):

        for connection in self.connections:
            source_types = [self.sensory_neurons[index] for index in connection.inputs]
            inputs: list[float] = []
            for source_type in source_types:
                if source_type in SensoryNeuronTypes:
                    inputs.append(self.get_sensory_data(board, source_type))
                elif source_type in ActionNeuronTypes:
                    raise Exception("Source neuron type is action type")
                else:
                    raise Exception("Source neuron type is not sensory or action")
            certainty = Connection.calculate_connection(connection, inputs)

            destination_type = self.action_neurons[connection.output]
            if destination_type in ActionNeuronTypes:
                self.perform_action(destination_type, certainty)

    def get_sensory_data(self, board: "Board", input_type: int) -> float:
        sensor_val: Union[float, None]
        if input_type == SensoryNeuronType.Age.value:
            sensor_val = self.creature.get_age() / board.get_steps_per_generation()
        elif input_type == SensoryNeuronType.Rnd.value:
            sensor_val = random.random()
        elif input_type == SensoryNeuronType.Osc.value:
            sensor_val = self.creature.get_osc()
        elif input_type == SensoryNeuronType.Lx.value:
            sensor_val = self.creature.get_pos()[0] / board.board_width
        elif input_type == SensoryNeuronType.Ly.value:
            sensor_val = self.creature.get_pos()[0] / board.board_height
        elif input_type == SensoryNeuronType.BDx.value:
            sensor_val = min(self.creature.get_distance_border_forward(board, Rotation.Left.value),
                             self.creature.get_distance_border_forward(board,
                                                                       Rotation.Right.value)) / board.board_height * 2
        elif input_type == SensoryNeuronType.BDy.value:
            sensor_val = min(self.creature.get_distance_border_forward(board, Rotation.Up.value),
                             self.creature.get_distance_border_forward(board,
                                                                       Rotation.Down.value)) / board.board_width * 2
        elif input_type == SensoryNeuronType.Bfd.value:
            sensor_val = self.creature.get_distance_border_forward(board)
        elif input_type == SensoryNeuronType.Cfd.value:
            sensor_val = self.creature.get_distance_creature_forward(board)
        elif input_type == SensoryNeuronType.LMy.value:
            rot = self.creature.get_rotation()
            if rot == Rotation.Left.value:
                sensor_val = 0.0
            elif rot == Rotation.Right.value:
                sensor_val = 1.0
            else:
                sensor_val = 0.5
        elif input_type == SensoryNeuronType.LMx.value:
            rot = self.creature.get_rotation()
            if rot == Rotation.Down.value:
                sensor_val = 0.0
            elif rot == Rotation.Up.value:
                sensor_val = 1.0
            else:
                sensor_val = 0.5
        elif input_type == SensoryNeuronType.Pop.value:
            sensor_val = self.creature.get_pop_density(board, 2, False)
        else:
            print(f"input type not found {input_type}")
            sensor_val = None
        if type(sensor_val) != float or sensor_val < -0.01 or sensor_val > 1.01:
            # print(f"sensor_val={sensor_val} for {input_type}")
            sensor_val = max(0.0, min(sensor_val, 1.0))

        return sensor_val

    def perform_action(self, action_type: int, certainty: float):
        if action_type == ActionNeuronType.OSC.value and certainty > 0:
            self.creature.set_osc(certainty)
        elif action_type == ActionNeuronType.Mrn.value and certainty > 0:
            self.creature.move(random.choice([0, 1, 2, 3]), certainty)
        elif action_type == ActionNeuronType.Mfd.value and certainty > 0:
            creature = self.creature
            creature.move(creature.get_rotation(), certainty)
        elif action_type == ActionNeuronType.Mrv.value and certainty > 0:
            creature = self.creature
            reverse = (creature.get_rotation() - 2) % 4
            creature.move(reverse, certainty)
        elif action_type == ActionNeuronType.MLR.value and not -.8 > certainty > .8:
            rotation = self.creature.get_rotation()
            direction: int
            if certainty < 0:  # left
                direction = (rotation - 1) % 4
            else:  # right
                direction = (rotation + 1) % 4
            abs_certainty = abs(certainty)
            self.creature.move(direction, abs_certainty)
        elif action_type == ActionNeuronType.MX.value and not -.8 > certainty > .8:
            direction: int
            if certainty < 0:
                direction = Rotation.Left.value
            else:  # x negative
                direction = Rotation.Right.value
            abs_certainty = abs(certainty)
            self.creature.move(direction, abs_certainty)
        elif action_type == ActionNeuronType.MY.value and not -.8 > certainty > .8:
            direction: int
            if certainty < 0:
                direction = Rotation.Up.value
            else:  # x negative
                direction = Rotation.Down.value
            abs_certainty = abs(certainty)
            self.creature.move(direction, abs_certainty)

    def get_connections(self):
        return self.connections

    def get_mutation_factor(self):
        return self.mutation_factor
#     OSC = 12
#     Mrn = 13
#     Mfd = 14
#     Mrv = 15
#     MLR = 16
#     MX = 17
#     MY = 18
