import asyncio
import websockets
import json
import numpy as np

# from .constants import (
#     INITIALIZE,
#     NODE_CLICKED,
#     VALID_START_NODE,
#     INVALID_START_NODE,
#     VALID_END_NODE,
#     INVALID_END_NODE,
#     GAME_OVER,
#     VALID_START_NODE_MESSAGE,
#     INVALID_START_NODE_MESSAGE,
#     INVALID_END_NODE
# )


# (R. Friel - December 07, 2020) - Define constants if import errors.
# Client payload messages.
INITIALIZE = 'INITIALIZE'
NODE_CLICKED = 'NODE_CLICKED'

# Server response messages.
VALID_START_NODE = 'VALID_START_NODE'
INVALID_START_NODE = 'INVALID_START_NODE'
VALID_END_NODE = 'VALID_END_NODE'
INVALID_END_NODE = 'INVALID_END_NODE'
GAME_OVER = 'GAME_OVER'
VALID_START_NODE_MESSAGE = 'Select a second node to complete the line.'
INVALID_START_NODE_MESSAGE = 'Not a valid starting position.'
INVALID_END_NODE_MESSAGE = 'Invalid move!'


class ConnectTheDots():

    async def echo(self, websocket, path):
        # (R. Friel - December 07, 2020) - Start websocket server.
        async for message in websocket:

            client_response: str = self.process_incoming_message(message = message)

            await websocket.send(client_response)


    def process_incoming_message(self, message: str) -> str:
        # (R. Friel - December 07, 2020) - Process the message.
        # Turn string into a dictionary, and process based on the msg.
        # Return the client_response.

        self.original_payload: dict = json.loads(message)
        self.payload: dict = json.loads(message)
        payload_message: str = self.payload.get('msg')
        client_response = ''

        if payload_message == INITIALIZE:
            # (R. Friel - December 09, 2020) - Initilize the game. Values will be stored in self.game_state.
            self.process_initialize()

        elif payload_message == NODE_CLICKED:
            processed_node: dict = self.process_node_clicked()

        else:
            # (R. Friel - December 07, 2020) - Handle unknown request payloads and errors.
            # Just pring the message for now.
            # print(message)
            pass

        client_response: str = self.generate_client_response()

        return client_response


    def process_node_clicked(self) -> str:


        # (R. Friel - December 09, 2020) - Okay our first conditional needs to check
        # if there have been any moves. If not, then it's a valid move for a node start.

        if not self.game_state.get('current_selection'):
            if self.game_state.get('total_moves') == 0:

                # Player 1 is selecting the first node of the game.
                self.game_state['new_line'] = None
                self.game_state['heading'] = f"Player {self.game_state['player_turn']}"
                self.game_state['message'] = VALID_START_NODE_MESSAGE

                self.payload['msg'] = VALID_START_NODE

                self.game_state['current_selection'] = {}
                self.game_state['current_selection']['x'] = self.payload.get('body').get('x')
                self.game_state['current_selection']['y'] = self.payload.get('body').get('y')

                self.game_state['line_end_one']['x'] = self.payload.get('body').get('x')
                self.game_state['line_end_one']['y'] = self.payload.get('body').get('y')

                self.game_state['line_end_two']['x'] = self.payload.get('body').get('x')
                self.game_state['line_end_two']['y'] = self.payload.get('body').get('y')



            # (R. Friel - December 09, 2020) - If there is no current selection, we need to make sure that
            # the player selects one of the end points the previous player made available.
            elif (
                self.payload['body']['x'] == self.game_state['line_end_one']['x'] and self.payload['body']['y'] == self.game_state['line_end_one']['y']
                ) or (
                self.payload['body']['x'] == self.game_state['line_end_two']['x'] and self.payload['body']['y'] == self.game_state['line_end_two']['y']
                ):

                self.game_state['total_moves'] += 1
                self.game_state['new_line'] = None
                self.game_state['heading'] = f"Player {self.game_state['player_turn']}"
                self.game_state['message'] = VALID_START_NODE_MESSAGE
                self.payload['msg'] = VALID_START_NODE

                self.game_state['current_selection'] = {}
                self.game_state['current_selection']['x'] = self.payload.get('body').get('x')
                self.game_state['current_selection']['y'] = self.payload.get('body').get('y')

                # (R. Friel - December 09, 2020) - Remove the current selection from the invalid_points.
                remove_from_invalid_selection: list = [self.game_state['current_selection']['x'], self.game_state['current_selection']['y']]
                if remove_from_invalid_selection in self.game_state['invalid_points']:
                    self.game_state['invalid_points'].remove(remove_from_invalid_selection)

            else:
                self.game_state['total_moves'] += 1
                self.game_state['new_line'] = None
                self.game_state['heading'] = f"Player {self.game_state['player_turn']}"
                self.game_state['message'] = INVALID_START_NODE_MESSAGE
                self.payload['msg'] = INVALID_START_NODE

                self.game_state['current_selection'] = None



        # There is a current selection. Ensure we are not selecting the same current selection.
        elif self.payload['body']['x'] == self.game_state['current_selection']['x'] and self.payload['body']['y'] == self.game_state['current_selection']['y']:
            self.game_state['total_moves'] += 1
            self.game_state['new_line'] = None
            self.game_state['heading'] = f"Player {self.game_state['player_turn']}"
            self.game_state['message'] = INVALID_END_NODE_MESSAGE
            self.payload['msg'] = INVALID_END_NODE
            self.game_state['current_selection'] = None


            print("not selecting the same current selection.")

        elif self.validate_line():

            # (R. Friel - December 09, 2020) - The line has been validated as 0, 45, or 90 degree angle.
            # Now we need to make sure the start and end points do not overlap with other lines.
            # We manage a list of invalid_points to do so.
            if self.add_points_to_store_and_validate():

                # The start and end points are finalized and valid.
                self.game_state['total_moves'] += 1
                self.game_state['heading'] = f"Player {self.game_state['player_turn']}"
                self.game_state['message'] = None
                self.payload['msg'] = VALID_END_NODE


                # (R. Friel - December 09, 2020) - Create the new_line for the client response.
                self.game_state['new_line'] = {}
                self.game_state['new_line']['start'] = {}
                self.game_state['new_line']['end'] = {}

                self.game_state['new_line']['start']['x'] = self.game_state['current_selection']['x']
                self.game_state['new_line']['start']['y'] = self.game_state['current_selection']['y']
                self.game_state['new_line']['end']['x'] = self.payload['body']['x']
                self.game_state['new_line']['end']['y'] = self.payload['body']['y']

                # (R. Friel - December 09, 2020) - We need to keep track of the ending points of the lines.
                if self.game_state['line_end_one']['x'] == self.game_state['current_selection']['x'] and self.game_state['line_end_one']['y'] == self.game_state['current_selection']['y']:
                    self.game_state['line_end_one']['x'] = self.payload['body']['x']
                    self.game_state['line_end_one']['y'] = self.payload['body']['y']
                else:
                    self.game_state['line_end_two']['x'] = self.payload['body']['x']
                    self.game_state['line_end_two']['y'] = self.payload['body']['y']

                # (R. Friel - December 09, 2020) - We have made a valid selection, so set the current_selection to None.
                self.game_state['current_selection'] = None

                # Change the player turn. Will cycle between 1 and 2.
                self.game_state["player_turn"] = (self.game_state["player_turn"] % 2) + 1

            else:
                # Lines are intersecting. Invalid end node.
                self.game_state['total_moves'] += 1
                self.game_state['new_line'] = None
                self.game_state['heading'] = f"Player {self.game_state['player_turn']}"
                self.game_state['message'] = INVALID_END_NODE_MESSAGE
                self.payload['msg'] = INVALID_END_NODE
                self.game_state['current_selection'] = None

                print("Lines are intersecting. Invalid end node.")


        else:
            # The line is not a 0, 45, or 90 degree angle.
            self.game_state['total_moves'] += 1
            self.game_state['new_line'] = None
            self.game_state['heading'] = f"Player {self.game_state['player_turn']}"
            self.game_state['message'] = INVALID_END_NODE_MESSAGE
            self.payload['msg'] = INVALID_END_NODE
            self.game_state['current_selection'] = None

            print("Line is not horizontal or verticle or diagonal.")


        # print(self.game_state)
        # print(self.payload)


    def validate_line(self) -> bool:

        # Take values from dictionaries to reduce length of conditionals. Easier to read.
        end_x: int = self.payload['body']['x']
        end_y: int = self.payload['body']['y']

        start_x: int = self.game_state['current_selection']['x']
        start_y: int = self.game_state['current_selection']['y']


        # (R. Friel - December 09, 2020) - We need to calculate the angle of the lines.
        # Only 0, 90, and 45 degree lines are valid.

        diff_x: int = abs(start_x - end_x)
        diff_y: int = abs(start_y - end_y)

        # If the difference on x axis is 0 we have Verticle line. y axis is 0 we have Horizontal line.
        if diff_x == 0 or diff_y ==0:
            return True

        # Should calculate 45 degree lines. Above if statement checks for divide by 0.
        if (diff_x / diff_y == 0) or (diff_x / diff_y == 1):
            return True

        return False


    def add_points_to_store_and_validate(self) -> bool:
        # (R. Friel - December 09, 2020) - Here I need to handle when lines intersect essentially
        # by keeping track of previous moves.

        end_x: int = self.payload['body']['x']
        end_y: int = self.payload['body']['y']

        start_x: int = self.game_state['current_selection']['x']
        start_y: int = self.game_state['current_selection']['y']

        max_x: int = max(end_x, start_x)
        max_y: int = max(end_y, start_y)
        min_x: int = min(end_x, start_x)
        min_y: int = min(end_y, start_y)

        diff_x: int = start_x - end_x
        diff_y: int = start_y - end_y

        list_of_points: list = []


        # Horizontal Line and Verticle Line.
        if start_y == end_y or end_x == start_x:

            for x in range(min_x, (max_x + 1)):
                for y in range(min_y, (max_y + 1)):

                    # (R. Friel - December 09, 2020) - We can't add the start positions to the invalid points.
                    # if (x != end_x and y != end_y) and (x != start_x and y != start_y):
                    list_of_points.append([x, y])

        # Diagonal Line.
        else:

            # Need trusty math here.
            # y = m*x + b is the formula.

            m: int = 0
            b: int = 0
            m = diff_y / diff_x # Slope
            b = ((start_x * end_y) - (end_x * start_y)) / diff_x # y intercept.

            for x in range(min_x, (max_x + 1)):
                y = int(m * x + b)
                list_of_points.append([x, y])

                # (R. Friel - December 09, 2020) - Due to the structure of the matrix, I need to find the half way points
                # between the points prevent line intersection.
                if x != max_x:
                    y = float(m * (float(x + 0.5)) + b)
                    list_of_points.append([float(x+0.5), y])


        # Now check if the list of points have already been added to the invalid_points list in the game state.
        for points in list_of_points:
            if points in self.game_state['invalid_points']:
                return False


        # If none of the points are invalid, loop again and add to the invalid_points in game state.
        # Can't do this in the above statement.
        if self.game_state['add_to_invalid_points']:
            for points in list_of_points:
                if points not in self.game_state['invalid_points']:
                    self.game_state['invalid_points'].append(points)


        return True


    def process_initialize(self):
        # (R. Friel - December 07, 2020) - Start the game.
        # Keep track of game state via game_state dictionary.
        self.game_state: dict = {}
        self.old_state: dict = {}

        self.game_state['new_line'] = None
        self.game_state['heading'] = 'Player 1'
        self.game_state['message'] = "Awaiting Player 1's Move"
        self.game_state['current_selection'] = None
        self.game_state['total_moves'] = 0
        self.game_state['player_turn'] = 1
        self.game_state['invalid_points'] = []
        self.game_state['matrix_options'] = []
        self.game_state['line_end_one'] = {}
        self.game_state['line_end_two'] = {}
        self.game_state['add_to_invalid_points'] = True


        # (R. Friel - December 09, 2020) - This is used to determine game over. If a player has any potential options.
        matrix_options: list = []
        for x in range(0, 4):
            for y in range(0, 4):
                matrix_options.append([x, y])

        self.game_state['matrix_options'] = matrix_options


    def generate_client_response(self) -> str:
        # (R. Friel - December 07, 2020) - Create string json for the client.
        client_response = {}

        client_response['id'] = self.payload.get('id')
        client_response['msg'] = self.payload.get('msg')
        client_response['body'] = {}
        client_response['body']['newLine'] = self.game_state.get('new_line')
        client_response['body']['heading'] = self.game_state.get('heading')
        client_response['body']['message'] = self.game_state.get('message')

        return json.dumps(client_response)


# Initilize the class.
connect_the_dots = ConnectTheDots()

# (R. Friel - December 07, 2020) - Change port to 8081 for Konica Minolta asssessment.
start_server = websockets.serve(connect_the_dots.echo, "localhost", 8081)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()