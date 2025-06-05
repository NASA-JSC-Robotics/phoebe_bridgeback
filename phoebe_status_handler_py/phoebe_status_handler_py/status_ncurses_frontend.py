import curses
from phoebe_status_handler_py.status_state import StatusState


class StrStatus:
    """Contains a string to draw at a position"""

    def __init__(self, screen: curses.window, row: int, col: int, content: str = ""):
        """Constructor

        Args:
            screen (curses.window): The curses screen for drawing the content
            row (int): row to draw at
            col (int): column to draw at
            content (str, optional): Initial string content. Defaults to "".
        """
        self.screen = screen
        self.row = row
        self.col = col
        self.content = content

    def draw(self, attributes):
        """Draw the content with the provided color attributes

        Args:
            attributes (int): curses color attribute value
        """
        self.screen.addstr(self.row, self.col, self.content, attributes)


class WheelStatus(StrStatus):
    """Specialized drawing class for wheel status"""

    def __init__(self, screen, row, col):
        super().__init__(screen, row, col)

    def draw(self, upper_attributes, lower_attributes=None, value=" "):
        """Draw wheel state

        Args:
            upper_attributes (int): color to draw the upper wheel state
            lower_attributes (int, optional): color to draw the lower wheel state
                                              if None, uses the upper_attributes.
                                              Defaults to None.
            value (str, optional): content to draw. Defaults to " ".
        """
        self.screen.addstr(self.row, self.col, value, upper_attributes)
        self.screen.addstr(self.row, self.col + 2, value, lower_attributes if lower_attributes else upper_attributes)


class StatusNcursesFrontend:
    """TUI for vehicle status"""

    # Static definitions
    body = (
        "-------------------------",
        "|                        \\",
        "|                         | front",
        "|                        /",
        "-------------------------",
    )
    BODY_START_ROW = 4
    BODY_END_ROW = BODY_START_ROW + len(body)
    BODY_START_COL = 4
    BODY_END_COL = BODY_START_COL + len(body[0])

    def __init__(self):
        """Constructor"""

        # Create the curses screen and define color pairings (FG, BG)
        self.screen_ = curses.initscr()
        curses.noecho()
        curses.curs_set(0)  # Make the cursor invisible
        curses.start_color()
        curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(4, curses.COLOR_BLUE, curses.COLOR_BLACK)
        curses.init_pair(5, curses.COLOR_BLACK, curses.COLOR_BLACK)
        curses.init_pair(6, curses.COLOR_YELLOW, curses.COLOR_BLACK)

        # Convenient dictionary of color name -> pairing attributes
        self.colors = {
            "grey": (curses.color_pair(1) | curses.A_DIM),
            "white": (curses.color_pair(1) | curses.A_BOLD),
            "green": curses.color_pair(2),
            "boldgreen": (curses.color_pair(2) | curses.A_BOLD),
            "red": curses.color_pair(3),
            "blue": curses.color_pair(4),
            "black": curses.color_pair(5),
            "yellow": curses.color_pair(6),
        }

        # Local shorthands for the bulkier but more descriptive names
        start_row = self.BODY_START_ROW
        end_row = self.BODY_END_ROW
        start_col = self.BODY_START_COL
        end_col = self.BODY_END_COL

        self.status_objects = {
            "leftRear": WheelStatus(self.screen_, start_row - 1, start_col - 1),
            "leftFront": WheelStatus(self.screen_, start_row - 1, end_col - 2),
            "rightRear": WheelStatus(self.screen_, end_row, start_col - 1),
            "rightFront": WheelStatus(self.screen_, end_row, end_col - 2),
            "battery": StrStatus(self.screen_, start_row + 1, start_col + 2, " BAT "),
            "battery_stats": StrStatus(self.screen_, start_row + 1, start_col + 8, ""),
            "charging": StrStatus(self.screen_, start_row + 3, start_col + 2, " CHG "),
            "drivingLeft": StrStatus(self.screen_, start_row - 1, end_col + 3, "-->"),
            "drivingRight": StrStatus(self.screen_, end_row, end_col + 3, "-->"),
        }

        # A client using this class may inject a logger via set_logger()
        self.logger = None

        # How many subscription updates have been received. This is mostly used to simulate blinking
        self.update_count = 0

        # Draw the initial robot state
        self.draw_robot()

    def draw_robot(self):
        """Draw the initial robot state"""
        self.screen_.clear()

        # Draw title
        self.screen_.addstr(0, 10, "Phoebe Status", self.colors["grey"] | curses.A_UNDERLINE)

        # Draw body
        row = self.BODY_START_ROW
        for line in self.body:
            self.screen_.addstr(row, self.BODY_START_COL, line, self.colors["grey"])
            row += 1

        # Draw status objects
        self.update_all_stop_lighting("grey")
        self.update_battery("grey")
        self.update_charging_state("grey")
        self.update_driving_state("black")  # Drawing black on black effectively hides the object
        self.screen_.refresh()  # Tell ncurses to display what has been drawn

    def set_logger(self, logger):
        """Allow a client to inject a ROS logger

        Args:
            logger (_type_): ROS logger
        """
        self.logger = logger

    def fix_attr(self, attributes, is_blinking):
        """Returns an attribute that is either what is provided, or black-on-black
        if is_blinking is set true and we are on an even update. This simulates
        blinking.

        Args:
            attributes (int): ncurses color attribute
            is_blinking (bool): whether blinking is on or off

        Returns:
            int: ncurses color attribute
        """
        if is_blinking and self.update_count % 2:
            return self.colors["black"]
        return attributes

    def update_battery(self, color: str, is_blinking=False):
        """Update and redraw battery state

        Args:
            color (str): color name
            is_blinking (bool, optional): whether the color should be blinking. Defaults to False.
        """
        attributes = self.fix_attr(self.colors[color] | curses.A_REVERSE, is_blinking)
        self.status_objects["battery"].draw(attributes)

    def update_battery_stats(self, status_msg: StatusState):
        """Update and redraw battery statistics

        Args:
            status_msg (StatusState): Status message containing battery stats
        """
        self.status_objects["battery_stats"].content = (
            f"{status_msg.battery_percent:>3.0f}% {status_msg.battery_voltage:>4.1f}V {status_msg.battery_amps:>4.1f}A"
        )
        self.status_objects["battery_stats"].draw(self.colors["white"])

    def update_charging_state(self, color: str, is_blinking=False):
        """Update and draw charging state"""
        attributes = self.fix_attr(self.colors[color] | curses.A_REVERSE, is_blinking)
        self.status_objects["charging"].draw(attributes)

    def update_driving_state(self, color: str, is_blinking=False):
        """Update and draw driving state"""
        attributes = self.fix_attr(self.colors[color], is_blinking)
        self.status_objects["drivingLeft"].draw(attributes)
        self.status_objects["drivingRight"].draw(attributes)

    def update_stop_lighting(
        self, which_corner: str, upper_color: str, lower_color: str = None, is_blinking=False, content=" "
    ):
        """Update and redraw one set of wheel stop state lights"""
        if which_corner not in self.status_objects:
            return False

        if lower_color is None:
            lower_color = upper_color
        upper_attributes = self.fix_attr(self.colors[upper_color] | curses.A_REVERSE, is_blinking)
        lower_attributes = self.fix_attr(self.colors[lower_color] | curses.A_REVERSE, is_blinking)
        self.status_objects[which_corner].draw(upper_attributes, lower_attributes, content)

    def update_all_stop_lighting(self, upper_color, lower_color=None, is_blinking=False, content=" "):
        """Update and draw all wheel stop state lights"""
        self.update_stop_lighting("leftRear", upper_color, lower_color, is_blinking, content)
        self.update_stop_lighting("leftFront", upper_color, lower_color, is_blinking, content)
        self.update_stop_lighting("rightRear", upper_color, lower_color, is_blinking, content)
        self.update_stop_lighting("rightFront", upper_color, lower_color, is_blinking, content)

    def update(self, state: StatusState):
        """Main update callback

        Args:
            state (StatusState): incoming updated state message
        """
        self.update_count += 1

        # Translate status into objects and colors
        if state.run_state == StatusState.ROBOT_STATE_NO_COMM:
            self.update_all_stop_lighting("grey")
        elif state.run_state == StatusState.ROBOT_STATE_ESTOPPED:
            self.update_all_stop_lighting("red", is_blinking=True)
        elif state.run_state == StatusState.ROBOT_STATE_NEEDS_RESET:
            self.update_all_stop_lighting("red", is_blinking=True, content="R")
        elif state.run_state == StatusState.ROBOT_STATE_RUNNING:
            self.update_stop_lighting("leftRear", "red")
            self.update_stop_lighting("rightRear", "red")
            self.update_stop_lighting("leftFront", "white")
            self.update_stop_lighting("rightFront", "white")
        else:
            self.update_all_stop_lighting("grey")

        if state.battery_state == StatusState.BATTERY_STATE_LOW:
            self.update_battery("yellow")
        elif state.battery_state == StatusState.BATTERY_STATE_OK:
            self.update_battery("green")
        elif state.battery_state == StatusState.BATTERY_STATE_FULL:
            self.update_battery("blue")
        elif state.battery_state == StatusState.BATTERY_STATE_FAULTED:
            self.update_battery("red")
        else:
            self.update_battery("grey")

        self.update_battery_stats(state)

        if state.charging_state == StatusState.CHARGING_STATE_INACTIVE:
            self.update_charging_state("black")
        elif state.charging_state == StatusState.CHARGING_STATE_ACTIVE:
            self.update_charging_state("green")
        else:
            self.update_charging_state("grey")

        if state.driving_state == StatusState.DRIVING_STATE_ON:
            self.update_driving_state("boldgreen", is_blinking=True)
        elif state.driving_state == StatusState.DRIVING_STATE_OFF:
            self.update_driving_state("yellow")
        else:
            self.update_driving_state("black")

        self.screen_.refresh()

    def __del__(self):
        """Ncurses cleanup. Needed to reset the terminal."""
        curses.echo()
        curses.endwin()
