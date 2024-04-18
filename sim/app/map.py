from dataclasses import dataclass, field
from operator import add
from queue import PriorityQueue, Queue

import arcade
from sim.app import hexagon
from sim.app.tile import Tile, create_tile

from app.config import HEX_LAYOUT, MAP
from app.tilemap import load_tilemap


@dataclass(order=True)
class PrioritizedItem:
    priority: int
    tile: Tile = field(compare=False)


class HexTileMapGraph:
    """A simple graph."""

    def __init__(self, tiles: dict[hexagon.Hex, Tile]):
        """Init."""
        self.edges: dict[Tile, tuple[Tile, ...]] = {}

        for tile in tiles.values():
            edges = []
            for neighbor_hex in tile.hex.neighbors():
                neighbor_tile = tiles.get(neighbor_hex)
                if not neighbor_tile:
                    continue
                if neighbor_tile.traversable:
                    edges.append(neighbor_tile)

            self.edges[tile] = tuple(edges)

    def neighbors(self, tile: Tile) -> tuple[Tile, ...]:
        """Get the neighbors of a node."""
        return self.edges[tile]

    def cost(self, a: Tile, b: Tile) -> int:
        """Get the cost of moving from one node to another."""
        return 1


def breadth_first_search(graph: HexTileMapGraph, start: Tile, goal: Tile | None = None):
    frontier: Queue[Tile] = Queue()
    frontier.put(start)
    came_from: dict[Tile, Tile | None] = {}
    came_from[start] = None

    while not frontier.empty():
        current: Tile = frontier.get()

        if current == goal:
            break

        for tile in graph.neighbors(current):
            if tile not in came_from:
                frontier.put(tile)
                came_from[tile] = current

    return came_from


class Map(arcade.Section):
    """This represents the place where the game takes place."""

    def __init__(self, left: int, bottom: int, width: int, height: int, **kwargs):
        """Init."""
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

        self.red_highlighted_tiles: list[Tile] = []
        self.white_highlighted_tiles: list[Tile] = []
        self.updated_point = False
        self.point_a: Tile | None = None
        self.point_b: Tile | None = None

    def setup(self):
        """Set up the game here. Call this function to restart the game."""
        # Load our TileMap
        self.tile_map = load_tilemap(
            MAP,
            hex_layout=HEX_LAYOUT,
        )

        self.tiles = self.tile_map.hex_tiles

        # Create our Scene Based on the TileMap
        self.scene = arcade.Scene.from_tilemap(self.tile_map)
        self.graph = HexTileMapGraph(self.tiles)

        # Initialize our camera, setting a viewport the size of our window.
        self.camera = arcade.camera.Camera2D()
        self.camera.zoom = 0.5

        # Initialize our gui camera, initial settings are the same as our world camera.
        self.gui_camera = arcade.camera.Camera2D()

    def on_update(self, delta_time: float):
        """Logic."""
        # if self.updated_point and self.point_a and self.point_b:
        #     self.path_highlighted_tiles = hexagon.line(
        #         round(self.point_a.hex), round(self.point_b.hex)
        #     )
        #     self.updated_point = False

        if self.updated_point:
            if self.point_a and self.point_b:
                came_from = breadth_first_search(self.graph, self.point_a, self.point_b)
                reached = [tile.hex for tile in came_from if tile is not None]
                path: list[Tile] = []

                current = self.point_b
                success = True
                while current != self.point_a:
                    if current is None:
                        success = False
                        break
                    path.append(current)
                    current = came_from.get(current)

                if success:
                    self.white_highlighted_tiles = [tile.hex for tile in path]
                else:
                    self.white_highlighted_tiles = []

            elif self.point_a:
                # highlight all tiles that can be reached from point_a
                reached = [
                    tile.hex
                    for tile in breadth_first_search(self.graph, self.point_a)
                    if tile is not None
                ]

            self.red_highlighted_tiles = reached
            self.updated_point = False

    def update_coordinates_text(self, x: float, y: float):
        """Update the text for the world coordinates."""
        world_x, world_y = self.camera.map_screen_to_world_coordinate(
            (x, y),
        )
        sprites = arcade.get_sprites_at_point((world_x, world_y), self.scene["tiles"])
        if sprites:
            sprite = sprites[0]
            sprite_class = sprite.properties.get("class")
            self.tile_class_text.text = f"Class: {sprite_class}"

        self.world_coordinate_text.text = f"X: {world_x:.2f}, Y: {world_y:.2f}"

        hex_ = hexagon.pixel_to_hex(hexagon.Point(world_x, world_y), HEX_LAYOUT)
        self.axial_coordinate_text.text = f"Q: {round(hex_).q}, R: {round(hex_).r}"

    def get_clicked_tile(self, x: float, y: float) -> Tile:
        """Highlight the tile under the mouse."""
        world_x, world_y = self.camera.map_screen_to_world_coordinate(
            (x, y),
        )
        hex_ = hexagon.pixel_to_hex(hexagon.Point(world_x, world_y), HEX_LAYOUT)
        return self.tiles[round(hex_)]

    def on_draw(self):
        """Render the screen."""
        # Clear the screen to the background color
        self.view.clear()

        with self.camera.activate():
            self.scene.draw()

            if self.red_highlighted_tiles:
                highlighted_tile_corners = {
                    hexagon.polygon_corners(round(tile), HEX_LAYOUT)
                    for tile in self.red_highlighted_tiles
                }
                for tile_corners in highlighted_tile_corners:
                    arcade.draw_polygon_outline(
                        tile_corners,
                        arcade.color.RED,
                        line_width=2 * 1 / self.camera.zoom,
                    )

            if self.white_highlighted_tiles:
                highlighted_tile_corners = {
                    hexagon.polygon_corners(round(tile), HEX_LAYOUT)
                    for tile in self.white_highlighted_tiles
                }
                for tile_corners in highlighted_tile_corners:
                    arcade.draw_polygon_outline(
                        tile_corners,
                        arcade.color.WHITE,
                        line_width=2 * 1 / self.camera.zoom,
                    )

            if self.point_a:
                point_a_corners = hexagon.polygon_corners(
                    round(self.point_a.hex), HEX_LAYOUT
                )
                arcade.draw_polygon_outline(
                    point_a_corners,
                    arcade.color.BLUE,
                    line_width=2 * 1 / self.camera.zoom,
                )

            if self.point_b:
                point_b_corners = hexagon.polygon_corners(
                    round(self.point_b.hex), HEX_LAYOUT
                )
                arcade.draw_polygon_outline(
                    point_b_corners,
                    arcade.color.GREEN,
                    line_width=2 * 1 / self.camera.zoom,
                )

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
            self.point_a = self.get_clicked_tile(x, y)
            self.updated_point = True
            return

        if button == arcade.MOUSE_BUTTON_RIGHT:
            self.point_b = self.get_clicked_tile(x, y)
            self.updated_point = True
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
