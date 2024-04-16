from operator import add
from pathlib import Path

import arcade

from app import hex_lib
from app.tilemap import load_tilemap

PROJECT_ROOT = Path(__file__).parent.parent.parent
ASSETS = PROJECT_ROOT / "assets"
MAP = ASSETS / "maps" / "4corners.tmj"
assert MAP.exists(), f"Map file not found: {MAP}"

HEX_LAYOUT = hex_lib.Layout(
    hex_lib.layout_pointy, hex_lib.Point(140 / 2, 140 / 2), hex_lib.Point(0, 0)
)


class Map(arcade.Section):
    """This represents the place where the game takes place"""

    def __init__(self, left: int, bottom: int, width: int, height: int, **kwargs):
        super().__init__(left, bottom, width, height, **kwargs)

        # Variable to hold our Tiled Map
        self.tile_map = None

        # Replacing all of our SpriteLists with a Scene variable
        self.scene = None

        # A variable to store our camera object
        self.camera = None

        # A variable to store our gui camera object
        self.gui_camera = None

        self.tile_class_text = arcade.Text("", x=0, y=35)
        self.world_coordinate_text = arcade.Text("", x=0, y=20)
        self.axial_coordinate_text = arcade.Text("", x=0, y=5)
        self.tile_info_text_widgets = [
            self.tile_class_text,
            self.world_coordinate_text,
            self.axial_coordinate_text,
        ]

        self.mouse_pan = False

    def setup(self):
        """Set up the game here. Call this function to restart the game."""
        # Load our TileMap
        self.tile_map = load_tilemap(
            MAP,
            hex_layout=HEX_LAYOUT,
        )

        # Create our Scene Based on the TileMap
        self.scene = arcade.Scene.from_tilemap(self.tile_map)

        # Initialize our camera, setting a viewport the size of our window.
        self.camera = arcade.camera.Camera2D()
        self.camera.zoom = 0.5

        # Initialize our gui camera, initial settings are the same as our world camera.
        self.gui_camera = arcade.camera.Camera2D()

    def on_update(self, delta_time: float):
        """Movement and Game Logic"""

    def update_coordinates_text(self, x, y):
        """Update the text for the world coordinates."""
        world_x, world_y = self.camera.map_screen_to_world_coordinate(
            (x, y),
        )
        sprites = arcade.get_sprites_at_point(
            (world_x, world_y), self.scene["Tile Layer 1"]
        )
        if sprites:
            sprite = sprites[0]
            sprite_class = sprite.properties["class"]
            self.tile_class_text.text = f"Class: {sprite_class}"

        self.world_coordinate_text.text = f"X: {world_x:.2f}, Y: {world_y:.2f}"

        hex_ = hex_lib.pixel_to_hex(HEX_LAYOUT, hex_lib.Point(world_x, world_y))
        rounded_hex = hex_lib.hex_round(hex_)
        self.axial_coordinate_text.text = f"Q: {rounded_hex.q}, R: {rounded_hex.r}"

    def on_draw(self):
        """Render the screen."""
        # Clear the screen to the background color
        self.view.clear()

        with self.camera.activate():
            self.scene.draw()

        # Activate our GUI camera
        with self.gui_camera.activate():
            # draw rectangle from bottom left corner
            # FIXME: this is not how this should be done.
            # it is centered on 0, 0, so it overflows the screen
            # it is not batched, so it is slow
            arcade.draw_rectangle_filled(0, 0, 500, 100, arcade.color.GRAY)

            # FIXME: these should probably be batched or something
            for text_widget in self.tile_info_text_widgets:
                text_widget.draw()

    def on_mouse_press(self, x: float, y: float, button: int, key_modifiers: int):
        """Called when the user presses a mouse button."""
        if button == arcade.MOUSE_BUTTON_MIDDLE:
            self.mouse_pan = True
            return

        if button == arcade.MOUSE_BUTTON_LEFT:
            # Convert screen coordinate to world coordinate
            self.update_coordinates_text(x, y)
            return

    def on_mouse_release(self, x: float, y: float, button: int, modifiers: int):
        """Called when a user releases a mouse button."""
        if button == arcade.MOUSE_BUTTON_MIDDLE:
            self.mouse_pan = False
            return

    def on_mouse_motion(self, x, y, dx, dy):
        """Called whenever the mouse moves."""
        if self.mouse_pan:
            self.camera.position = tuple(
                map(
                    add,
                    self.camera.position,
                    (-dx * 1 / self.camera.zoom, -dy * 1 / self.camera.zoom),
                )
            )
            return

    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        """Called whenever the mouse scrolls."""
        # FIXME: zoom to mouse position
        # FIXME: zoom steps need to be more smooth
        self.camera.zoom += scroll_y * 0.1

    def on_key_press(self, key, modifiers):
        """Called whenever a key is pressed."""
        if key == arcade.key.ESCAPE:
            self.close()

    def on_key_release(self, key, modifiers):
        """Called whenever a key is released."""

    def on_resize(self, width: int, height: int):
        self.width = width
        self.height = height - self.view.info_bar.height
