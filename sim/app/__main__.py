"""Main module for the app."""

from pathlib import Path
import arcade
from app.tilemap import load_tilemap

PROJECT_ROOT = Path(__file__).parent.parent.parent
ASSETS = PROJECT_ROOT / "assets"
MAP = ASSETS / "maps" / "4corners.tmj"
assert MAP.exists(), f"Map file not found: {MAP}"

# Constants
SCREEN_WIDTH = 1900
SCREEN_HEIGHT = 1060
SCREEN_TITLE = "Sim"
# TILE_SCALING = 0.5
TILE_SCALING = 1.0


class MyGame(arcade.Window):
    """
    Main application class.
    """

    def __init__(self):

        # Call the parent class and set up the window
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE, resizable=True)

        # Variable to hold our texture for our player
        self.player_texture = None

        # Separate variable that holds the player sprite
        self.player_sprite = None

        # Variable to hold our Tiled Map
        self.tile_map = None

        # Replacing all of our SpriteLists with a Scene variable
        self.scene = None

        # A variable to store our camera object
        self.camera = None

        # A variable to store our gui camera object
        self.gui_camera = None

        # This variable will store our score as an integer.
        self.score = 0

        # This variable will store the text for score that we will draw to the screen.
        self.score_text = None

    def setup(self):
        """Set up the game here. Call this function to restart the game."""

        # Load our TileMap
        self.tile_map = load_tilemap(
            MAP,
            scaling=TILE_SCALING,
        )

        # Create our Scene Based on the TileMap
        self.scene = arcade.Scene.from_tilemap(self.tile_map)

        # self.player_texture = arcade.load_texture(
        #     ":resources:images/animated_characters/female_adventurer/femaleAdventurer_idle.png"
        # )

        # self.player_sprite = arcade.Sprite(self.player_texture)
        # self.player_sprite.center_x = 128
        # self.player_sprite.center_y = 128
        # self.scene.add_sprite("Player", self.player_sprite)

        # Initialize our camera, setting a viewport the size of our window.
        self.camera = arcade.camera.Camera2D()
        self.camera.zoom = 0.1

        # Initialize our gui camera, initial settings are the same as our world camera.
        self.gui_camera = arcade.camera.Camera2D()

    def on_draw(self):
        """Render the screen."""

        # Clear the screen to the background color
        self.clear()

        # Activate our camera before drawing
        self.camera.use()

        # Draw our Scene
        self.scene.draw()

        # Activate our GUI camera
        self.gui_camera.use()

    def on_update(self, delta_time):
        """Movement and Game Logic"""

        # # Center our camera on the player
        # self.camera.center(self.player_sprite.position)

    def on_key_press(self, key, modifiers):
        """Called whenever a key is pressed."""

        if key == arcade.key.ESCAPE:
            self.setup()

    def on_key_release(self, key, modifiers):
        """Called whenever a key is released."""


def _main():
    """Main function"""
    window = MyGame()
    window.setup()
    arcade.run()


if __name__ == "__main__":
    _main()
