import curses
from phoebe_status_handler_py.status_state import StatusState


class StrStatus(object):
    def __init__(self, screen: curses.window, row: int, col: int, content: str = ""):
        self.screen = screen
        self.row = row
        self.col = col
        self.content = content

    def draw(self, attributes):
        self.screen.addstr(self.row, self.col, self.content, attributes)


class WheelStatus(StrStatus):
    def __init__(self, screen, row, col):
        super().__init__(screen, row, col)

    def draw(self, upper_attributes, lower_attributes=None, value=" "):
        self.screen.addstr(self.row, self.col, value, upper_attributes)
        self.screen.addstr(self.row, self.col+2, value,
                           lower_attributes if lower_attributes else upper_attributes)


class StatusNcursesFrontend(object):
    body = ("-----------------------",
            "|                      \\",
            "|                       |",
            "|                      /",
            "-----------------------"
            )
    BODY_START_ROW = 4
    BODY_END_ROW = BODY_START_ROW + len(body)
    BODY_START_COL = 4
    BODY_END_COL = BODY_START_COL + len(body[0])

    def __init__(self):
        self.screen_ = curses.initscr()
        curses.noecho()
        curses.curs_set(0)    # Make the cursor invisible
        curses.start_color()
        curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(4, curses.COLOR_BLUE, curses.COLOR_BLACK)
        curses.init_pair(5, curses.COLOR_BLACK, curses.COLOR_BLACK)
        curses.init_pair(6, curses.COLOR_YELLOW, curses.COLOR_BLACK)

        self.colors = {
            "grey":         (curses.color_pair(1) | curses.A_DIM),
            "white":        (curses.color_pair(1) | curses.A_BOLD),
            "green":        curses.color_pair(2),
            "red":          curses.color_pair(3),
            "blue":         curses.color_pair(4),
            "black":        curses.color_pair(5),
            "yellow":       curses.color_pair(6),

        }

        # Shorthands for the bulkier but more descriptive names
        start_row = self.BODY_START_ROW
        end_row = self.BODY_END_ROW
        start_col = self.BODY_START_COL
        end_col = self.BODY_END_COL

        self.status_objects = {
            "leftRear":   WheelStatus(self.screen_, start_row-1, start_col-1),
            "leftFront":  WheelStatus(self.screen_, start_row-1, end_col-2),
            "rightRear":  WheelStatus(self.screen_, end_row,     start_col-1),
            "rightFront": WheelStatus(self.screen_, end_row,     end_col-2),
            "battery":      StrStatus(self.screen_, start_row+1, start_col+2, " BAT "),
            "charging":     StrStatus(self.screen_, start_row+3, start_col+2, " CHG "),
            "drivingLeft":  StrStatus(self.screen_, start_row-1, end_col+3,   "-->"),
            "drivingRight": StrStatus(self.screen_, end_row,     end_col+3,   "-->")
        }

        self.logger = None
        self.update_count = 0
        self.draw_robot()

    def draw_robot(self):
        self.screen_.clear()

        # Draw title
        self.screen_.addstr(0, 10, "Phoebe Status",
                            self.colors["grey"] | curses.A_UNDERLINE)

        # Draw body
        row = self.BODY_START_ROW
        for line in self.body:
            self.screen_.addstr(row, self.BODY_START_COL,
                                line, self.colors["grey"])
            row += 1

        # Draw status objects
        self.update_all_corner_lighting("grey")
        self.update_battery("grey")
        self.update_charging_state("grey")
        self.update_driving_state("black")
        self.screen_.refresh()

    def set_logger(self, logger):
        self.logger = logger

    def fix_attr(self, attributes, is_blinking):
        if is_blinking and self.update_count % 2:
            return self.colors["black"]
        return attributes

    def update_battery(self, color: str, is_blinking=False):
        attributes = self.fix_attr(
            self.colors[color] | curses.A_REVERSE, is_blinking)
        self.status_objects["battery"].draw(attributes)

    def update_charging_state(self, color: str, is_blinking=False):
        attributes = self.fix_attr(
            self.colors[color] | curses.A_REVERSE, is_blinking)
        self.status_objects["charging"].draw(attributes)

    def update_driving_state(self, color: str, is_blinking=False):
        attributes = self.fix_attr(self.colors[color], is_blinking)
        self.status_objects["drivingLeft"].draw(attributes)
        self.status_objects["drivingRight"].draw(attributes)

    def update_corner_lighting(self,
                               which_corner: str,
                               upper_color: str,
                               lower_color: str = None,
                               is_blinking=False,
                               content=" "):
        if which_corner not in self.status_objects:
            return False

        if lower_color is None:
            lower_color = upper_color
        upper_attributes = self.fix_attr(
            self.colors[upper_color] | curses.A_REVERSE, is_blinking)
        lower_attributes = self.fix_attr(
            self.colors[lower_color] | curses.A_REVERSE, is_blinking)
        self.status_objects[which_corner].draw(
            upper_attributes, lower_attributes, content)

    def update_all_corner_lighting(self,
                                   upper_color,
                                   lower_color=None,
                                   is_blinking=False,
                                   content=" "):
        self.update_corner_lighting(
            "leftRear",   upper_color, lower_color, is_blinking, content)
        self.update_corner_lighting(
            "leftFront",  upper_color, lower_color, is_blinking, content)
        self.update_corner_lighting(
            "rightRear",  upper_color, lower_color, is_blinking, content)
        self.update_corner_lighting(
            "rightFront", upper_color, lower_color, is_blinking, content)

    def update(self, state: StatusState):
        self.update_count += 1

        if state.estop_state == StatusState.ROBOT_STATE_OFF:
            self.update_all_corner_lighting("grey")
        elif state.estop_state == StatusState.ROBOT_STATE_NO_COMM:
            self.update_all_corner_lighting("red")
        elif state.estop_state == StatusState.ROBOT_STATE_ESTOPPED:
            self.update_all_corner_lighting("red", is_blinking=True)
        elif state.estop_state == StatusState.ROBOT_STATE_NEEDS_RESET:
            self.update_all_corner_lighting(
                "red", is_blinking=True, content="R")
        elif state.estop_state == StatusState.ROBOT_STATE_RUNNING:
            self.update_corner_lighting("leftRear", "red")
            self.update_corner_lighting("rightRear", "red")
            self.update_corner_lighting("leftFront", "white")
            self.update_corner_lighting("rightFront", "white")
        else:
            self.update_all_corner_lighting("grey")

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

        if state.charging_state == StatusState.CHARGING_STATE_OFF:
            self.update_charging_state("grey")
        elif state.charging_state == StatusState.CHARGING_STATE_ACTIVE:
            self.update_charging_state("green")
        else:
            self.update_charging_state("grey")

        if state.driving_state == StatusState.DRIVING_STATE_ON:
            self.update_driving_state("green", is_blinking=True)
        else:
            self.update_driving_state("black")

        self.screen_.refresh()

    def __del__(self):
        curses.echo()
        curses.endwin()
