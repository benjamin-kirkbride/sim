import arcade
from arcade.types import Color

COLOR_LIGHT = Color.from_hex_string("#D9BBA0")
COLOR_DARK = Color.from_hex_string("#0D0D0D")
COLOR_1 = Color.from_hex_string("#2A1459")
COLOR_2 = Color.from_hex_string("#4B89BF")
COLOR_3 = Color.from_hex_string("#03A688")


class InfoBar(arcade.Section):
    """This is the top bar of the screen where info is showed."""

    def on_draw(self):
        """Draw the info bar."""

    def on_resize(self, width: int, height: int):
        # stick to the top
        self.width = width
        self.bottom = height - self.view.info_bar.height
