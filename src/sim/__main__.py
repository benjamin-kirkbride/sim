"""Main module for the app."""

import arcade

from sim.infobar import InfoBar
from sim.map import Map

# Constants
SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080
SCREEN_TITLE = "Sim"

INFO_BAR_HEIGHT = 100


class GameView(arcade.View):
    """The game itself."""

    def __init__(self) -> None:
        """Initialize the game."""
        super().__init__()

        # we set accept_keyboard_events to False (default to True)
        self.info_bar = InfoBar(
            0,
            self.window.height - INFO_BAR_HEIGHT,
            self.window.width,
            INFO_BAR_HEIGHT,
            accept_keyboard_keys=False,
        )

        self.map = Map(0, 0, self.window.width, self.window.height - INFO_BAR_HEIGHT)

        # add the sections
        self.section_manager.add_section(self.info_bar)
        self.section_manager.add_section(self.map)
        self.map.setup()

    def on_draw(self) -> None:
        """Draw everything."""
        arcade.start_render()


def _main() -> None:
    """Main function."""
    window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE, resizable=True)
    game = GameView()
    window.show_view(game)
    window.run()


if __name__ == "__main__":
    _main()
