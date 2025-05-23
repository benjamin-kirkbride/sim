"""Generate TileMap from Tiled map files.

This module provides functionality to load in JSON map files from
the Tiled Map Editor. This is achieved using the pytiled-parser
library.

For more info on Tiled see: https://www.mapeditor.org/
For more info on pytiled-parser see: https://github.com/Beefy-Swain/pytiled_parser
"""

from __future__ import annotations

import copy
import math
from collections import OrderedDict
from collections.abc import Callable
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Any,
    cast,
)

import pytiled_parser
import pytiled_parser.tiled_object
from arcade import (
    Sprite,
    SpriteList,
    TextureAnimation,
    TextureAnimationSprite,
    TextureKeyframe,
    get_window,
)
from arcade.hitbox import HitBoxAlgorithm, RotatableHitBox
from arcade.texture.loading import _load_tilemap_texture
from pytiled_parser import Color

from sim.tile import Tile, create_tile

if TYPE_CHECKING:
    from arcade import Texture, TextureAtlas

import contextlib

from arcade.math import rotate_point
from arcade.resources import resolve
from arcade.types import Point, Rect, TiledObject
from pyglet.math import Vec2

from sim import hexagon

_FLIPPED_HORIZONTALLY_FLAG = 0x80000000
_FLIPPED_VERTICALLY_FLAG = 0x40000000
_FLIPPED_DIAGONALLY_FLAG = 0x20000000

__all__ = ["TileMap", "load_tilemap", "read_tmx"]

prop_to_float = cast(Callable[[pytiled_parser.Property], float], float)


def _get_image_info_from_tileset(
    tile: pytiled_parser.Tile,
) -> tuple[int, int, int, int]:
    image_x = 0
    image_y = 0
    if tile.tileset.image is not None:
        margin = tile.tileset.margin or 0
        spacing = tile.tileset.spacing or 0
        row = tile.id // tile.tileset.columns
        image_y = margin + row * (tile.tileset.tile_height + spacing)
        col = tile.id % tile.tileset.columns
        image_x = margin + col * (tile.tileset.tile_width + spacing)

    if tile.tileset.image:
        width = tile.tileset.tile_width
        height = tile.tileset.tile_height
    else:
        image_x = tile.x
        image_y = tile.y
        width = tile.width
        height = tile.height

    return image_x, image_y, width, height


def _get_image_source(
    tile: pytiled_parser.Tile,
    map_directory: str | None,
) -> Path | None:
    if tile.image:
        image_file = tile.image
    elif tile.tileset.image:
        image_file = tile.tileset.image
    else:
        print(
            f"Warning for tile {tile.id}, no image source listed either for individual tile, or as a tileset."
        )
        return None

    if image_file.exists():
        assert isinstance(image_file, Path)  # Why is this necessary?
        return image_file

    if map_directory:
        try2 = Path(map_directory, image_file)
        if try2.exists():
            return try2

    print(f"Warning, can't find image {image_file} for tile {tile.id}")
    return None


def _may_be_flip(tile: pytiled_parser.Tile, texture: Texture) -> Texture:
    if tile.flipped_diagonally:
        texture = texture.flip_diagonally()
    if tile.flipped_horizontally:
        texture = texture.flip_horizontally()
    if tile.flipped_vertically:
        texture = texture.flip_vertically()
    return texture


class TileMap:
    """Class that represents a fully parsed and loaded map from Tiled.

    For examples on how to use this class, see:
    https://api.arcade.academy/en/latest/examples/platform_tutorial/step_09.html


    :param Union[str, Path] map_file: A JSON map file for a Tiled map to initialize from
    :param scaling: Global scaling to apply to all Sprites.
    :param Dict[str, Dict[str, Any]] layer_options: Extra parameters for each layer.
    :param use_spatial_hash: If set to True, this will make moving a sprite
           in the SpriteList slower, but it will speed up collision detection
           with items in the SpriteList. Great for doing collision detection
           with static walls/platforms.
    :param hit_box_algorithm: The hit box algorithm to use for the Sprite's in this layer.
    :param tiled_map: An already parsed pytiled-parser map object.
           Passing this means that the ``map_file`` argument will be ignored, and the pre-parsed
           map will instead be used. This can be helpful for working with Tiled World files.
    :param offset: Can be used to offset the position of all sprites and objects
            within the map. This will be applied in addition to any offsets from Tiled. This value
            can be overridden with the layer_options dict.
    :param texture_atlas: A default texture atlas to use for the
            SpriteLists created by this map. If not supplied the global default atlas will be used.
    :param lazy: SpriteLists will be created lazily.


    The `layer_options` parameter can be used to specify per layer arguments.

    The available options for this are:

        use_spatial_hash - A boolean to enable spatial hashing on this layer's SpriteList.
        scaling - A float providing layer specific Sprite scaling.
        hit_box_algorithm - The hit box algorithm to use for the Sprite's in this layer.
        offset - A tuple containing X and Y position offsets for the layer
        custom_class - All objects in the layer are created from this class instead of Sprite. \
                       Must be subclass of Sprite.
        custom_class_args - Custom arguments, passed into the constructor of the custom_class
        texture_atlas - A texture atlas to use for the SpriteList from this layer, if none is \
                        supplied then the one defined at the map level will be used.

        For example:

        code-block::

            layer_options = {
                "Platforms": {
                    "use_spatial_hash": True,
                    "scaling": 2.5,
                    "offset": (-128, 64),
                    "custom_class": Platform,
                    "custom_class_args": {
                        "health": 100
                    }
                },
            }

    The keys and their values in each layer are passed to the layer processing functions
    using the `**` operator on the dictionary.
    """

    tiled_map: pytiled_parser.TiledMap
    """
    The pytiled-parser map object. This can be useful for implementing features
    that aren't supported by this class by accessing the raw map data directly.
    """
    width: float
    "The width of the map in tiles. This is the number of tiles, not pixels."
    height: float
    "The height of the map in tiles. This is the number of tiles, not pixels."
    tile_width: float
    "The width in pixels of each tile."
    tile_height: float
    "The height in pixels of each tile."
    background_color: Color | None
    "The background color of the map."
    scaling: float
    "A global scaling value to be applied to all Sprites in the map."
    sprite_lists: dict[str, SpriteList[Sprite]]
    """A dictionary mapping SpriteLists to their layer names. This is used
                    for all tile layers of the map."""
    object_lists: dict[str, list[TiledObject]]
    """
    A dictionary mapping TiledObjects to their layer names. This is used
    for all object layers of the map.
    """
    offset: Vec2
    "A tuple containing the X and Y position offset values."

    def __init__(
        self,
        hex_layout: hexagon.Layout,
        map_file: str | Path = "",
        scaling: float = 1.0,
        layer_options: dict[str, dict[str, Any]] | None = None,
        use_spatial_hash: bool = False,
        hit_box_algorithm: HitBoxAlgorithm | None = None,
        tiled_map: pytiled_parser.TiledMap | None = None,
        offset: Vec2 = Vec2(0, 0),
        texture_atlas: TextureAtlas | None = None,
        lazy: bool = False,
    ) -> None:
        """Initialize the TileMap."""
        if not map_file and not tiled_map:
            raise AttributeError(
                "Initialized TileMap with an empty map_file or no map_object argument"
            )

        if tiled_map:
            self.tiled_map = tiled_map
        else:
            # If we should pull from local resources, replace with proper path
            map_file = resolve(map_file)

            # This attribute stores the pytiled-parser map object
            self.tiled_map = pytiled_parser.parse_map(map_file)

        if self.tiled_map.infinite:
            msg = (
                "Attempted to load an infinite TileMap. Arcade currently cannot load "
                "infinite maps. Disable the infinite map property and re-save the file."
            )
            raise AttributeError(msg)

        if not texture_atlas:
            with contextlib.suppress(RuntimeError):
                texture_atlas = get_window().ctx.default_atlas

        self.hex_layout = hex_layout
        self.hex_tiles: dict[hexagon.Hex, Tile] = {}
        self._lazy = lazy

        # Set Map Attributes
        self.width = self.tiled_map.map_size.width
        self.height = self.tiled_map.map_size.height
        self.tile_width = self.tiled_map.tile_size.width
        self.tile_height = self.tiled_map.tile_size.height
        self.background_color = self.tiled_map.background_color

        # Global Layer Defaults
        self.scaling = scaling
        self.use_spatial_hash = use_spatial_hash
        self.hit_box_algorithm = hit_box_algorithm
        self.offset = offset

        # Dictionaries to store the SpriteLists for processed layers
        self.sprite_lists: dict[str, SpriteList[Sprite]] = OrderedDict()
        self.object_lists: dict[str, list[TiledObject]] = OrderedDict()
        self.properties = self.tiled_map.properties

        global_options = {
            "scaling": self.scaling,
            "use_spatial_hash": self.use_spatial_hash,
            "hit_box_algorithm": self.hit_box_algorithm,
            "offset": self.offset,
            "custom_class": None,
            "custom_class_args": {},
            "texture_atlas": texture_atlas,
        }

        for layer in self.tiled_map.layers:
            if (layer.name in self.sprite_lists) or (layer.name in self.object_lists):
                msg = (
                    f"You have a duplicate layer name '{layer.name}' in your Tiled map. "
                    "Please use unique names for all layers and tilesets in your map."
                )
                raise AttributeError(msg)
            self._process_layer(layer, global_options, layer_options)

    def _process_layer(
        self,
        layer: pytiled_parser.Layer,
        global_options: dict[str, Any],
        layer_options: dict[str, dict[str, Any]] | None = None,
    ) -> None:
        processed: (
            SpriteList[Sprite]
            | tuple[SpriteList[Sprite] | None, list[TiledObject] | None]
        )

        options = global_options

        if layer_options and layer.name in layer_options:
            new_options = {
                key: layer_options[layer.name].get(key, global_options[key])
                for key in global_options
            }
            options = new_options

        if isinstance(layer, pytiled_parser.TileLayer):
            processed = self._process_tile_layer(layer, **options)
            self.sprite_lists[layer.name] = processed
        elif isinstance(layer, pytiled_parser.ObjectLayer):
            processed = self._process_object_layer(layer, **options)
            if processed[0]:
                sprite_list = processed[0]
                if sprite_list:
                    self.sprite_lists[layer.name] = sprite_list
            if processed[1]:
                object_list = processed[1]
                if object_list:
                    self.object_lists[layer.name] = object_list
        elif isinstance(layer, pytiled_parser.ImageLayer):
            processed = self._process_image_layer(layer, **options)
            self.sprite_lists[layer.name] = processed
        elif isinstance(layer, pytiled_parser.LayerGroup):
            for sub_layer in layer.layers:
                self._process_layer(sub_layer, global_options, layer_options)

    def get_cartesian(
        self,
        x: float,
        y: float,
    ) -> tuple[float, float]:
        """Given a set of coordinates in pixel units, this returns the cartesian coordinates.

        This assumes the supplied coordinates are pixel coordinates, and bases the cartesian
        grid off of the Map's tile size.

        If you have a map with 128x128 pixel Tiles, and you supply coordinates 500, 250 to
        this function you'll receive back 3, 2

        :param x: The X Coordinate to convert
        :param y: The Y Coordinate to convert
        """
        x = math.floor(x / (self.tile_width * self.scaling))
        y = math.floor(y / (self.tile_height * self.scaling))

        return x, y

    def get_tilemap_layer(self, layer_path: str) -> pytiled_parser.Layer | None:
        """Get a layer from the tilemap by its path."""
        assert isinstance(layer_path, str)

        def _get_tilemap_layer(
            my_path: list[str], layers: list[pytiled_parser.Layer]
        ) -> pytiled_parser.Layer | None:
            layer_name = my_path.pop(0)
            for my_layer in layers:
                if my_layer.name == layer_name:
                    if isinstance(my_layer, pytiled_parser.LayerGroup):
                        if len(my_path) != 0:
                            return _get_tilemap_layer(my_path, my_layer.layers)
                    else:
                        return my_layer
            return None

        path = layer_path.strip("/").split("/")
        layer = _get_tilemap_layer(path, self.tiled_map.layers)
        return layer

    def _get_tile_by_gid(self, tile_gid: int) -> pytiled_parser.Tile | None:
        """Given a tile GID, return the tile object."""
        flipped_diagonally = False
        flipped_horizontally = False
        flipped_vertically = False

        if tile_gid & _FLIPPED_HORIZONTALLY_FLAG:
            flipped_horizontally = True
            tile_gid -= _FLIPPED_HORIZONTALLY_FLAG

        if tile_gid & _FLIPPED_DIAGONALLY_FLAG:
            flipped_diagonally = True
            tile_gid -= _FLIPPED_DIAGONALLY_FLAG

        if tile_gid & _FLIPPED_VERTICALLY_FLAG:
            flipped_vertically = True
            tile_gid -= _FLIPPED_VERTICALLY_FLAG

        for tileset_key, tileset in self.tiled_map.tilesets.items():
            if tile_gid < tileset_key:
                continue

            # No specific tile info, but there is a tile sheet
            # print(f"data {tileset_key} {tileset.tiles} {tileset.image} {tileset_key} {tile_gid} {tileset.tile_count}")  # noqa
            if (
                tileset.image is not None
                and tileset_key <= tile_gid < tileset_key + tileset.tile_count
            ):
                tile_id = tile_gid - tileset_key
                existing_ref = None
                if (
                    tileset.tiles is not None
                    and (tile_gid - tileset_key) in tileset.tiles
                ):
                    existing_ref = tileset.tiles[tile_id]
                    existing_ref.image = tileset.image

                # No specific tile info, but there is a tile sheet
                if existing_ref:
                    tile_ref = existing_ref
                else:
                    tile_ref = pytiled_parser.Tile(id=(tile_id), image=tileset.image)
            elif tileset.tiles is None and tileset.image is not None:
                # Not in this tileset, move to the next
                continue
            else:
                if tileset.tiles is None:
                    return None
                tile_ref = tileset.tiles.get(tile_gid - tileset_key)

            if tile_ref:
                my_tile = copy.copy(tile_ref)
                my_tile.tileset = tileset
                my_tile.flipped_vertically = flipped_vertically
                my_tile.flipped_diagonally = flipped_diagonally
                my_tile.flipped_horizontally = flipped_horizontally
                return my_tile

        print(f"Returning NO tile for {tile_gid}.")
        return None

    def _get_tile_by_id(
        self, tileset: pytiled_parser.Tileset, tile_id: int
    ) -> pytiled_parser.Tile | None:
        for cur_tileset in self.tiled_map.tilesets.values():
            if cur_tileset is tileset:
                for tile in cur_tileset.tiles.values():
                    if tile_id == tile.id:
                        return tile

        return None

    def _create_sprite_from_tile(  #
        self,
        tile: pytiled_parser.Tile,
        scaling: float = 1.0,
        hit_box_algorithm: HitBoxAlgorithm | None = None,
        custom_class: type | None = None,
        custom_class_args: dict[str, Any] = {},
    ) -> Sprite:
        """Given a tile from the parser, try and create a Sprite from it."""
        # --- Step 1, Find a reference to an image this is going to be based off of
        map_source = self.tiled_map.map_file
        map_directory = map_source.parent
        image_file = _get_image_source(tile, map_directory)

        if tile.animation:
            if not custom_class:
                custom_class = TextureAnimationSprite
            elif not issubclass(custom_class, TextureAnimationSprite):
                msg = f"""
                    Tried to use a custom class {custom_class.__name__} for animated tiles
                    that doesn't subclass TextureAnimationSprite.
                    Custom classes for animated tiles must subclass TextureAnimationSprite.
                    """
                raise RuntimeError(msg)
            args = {"path_or_texture": image_file, "scale": scaling}
            my_sprite = custom_class(**custom_class_args, **args)  # type: ignore[arg-type]
        else:
            if not custom_class:
                custom_class = Sprite
            elif not issubclass(custom_class, Sprite):
                msg = f"""
                    Tried to use a custom class {custom_class.__name__} for
                    a tile that doesn't subclass arcade.Sprite.
                    Custom classes for tiles must subclass arcade.Sprite.
                    """
                raise RuntimeError(msg)

            # Can image_file be None?
            image_x, image_y, width, height = _get_image_info_from_tileset(tile)
            assert image_file is not None
            texture = _load_tilemap_texture(
                image_file,
                x=image_x,
                y=image_y,
                width=width,
                height=height,
                hit_box_algorithm=hit_box_algorithm,
            )
            texture = _may_be_flip(tile, texture)

            args = {
                "path_or_texture": texture,  # type: ignore[dict-item]
                "scale": scaling,
            }
            my_sprite = custom_class(**custom_class_args, **args)  # type: ignore[assignment, arg-type]

        if tile.properties is not None and len(tile.properties) > 0:
            for key, value in tile.properties.items():
                my_sprite.properties[key] = value

        if tile.class_:
            my_sprite.properties["class"] = tile.class_

        # Add tile ID to sprite properties
        my_sprite.properties["tile_id"] = tile.id

        if tile.objects is not None:
            if not isinstance(tile.objects, pytiled_parser.ObjectLayer):
                print("Warning, tile.objects is not an ObjectLayer as expected.")
                return my_sprite

            if len(tile.objects.tiled_objects) > 1:
                if tile.image:
                    print(
                        f"Warning, only one hit box supported for tile with image {tile.image}."
                    )
                else:
                    print("Warning, only one hit box supported for tile.")

            for hitbox in tile.objects.tiled_objects:
                points: list[Point] = []
                if isinstance(hitbox, pytiled_parser.tiled_object.Rectangle):
                    if hitbox.size is None:
                        print(
                            "Warning: Rectangle hitbox created for without a "
                            "height or width Ignoring."
                        )
                        continue

                    sx = hitbox.coordinates.x - (my_sprite.width / (scaling * 2))
                    sy = -(hitbox.coordinates.y - (my_sprite.height / (scaling * 2)))
                    ex = (hitbox.coordinates.x + hitbox.size.width) - (
                        my_sprite.width / (scaling * 2)
                    )
                    # issue #1068
                    # fixed size of rectangular hitbox
                    ey = -(hitbox.coordinates.y + hitbox.size.height) + (
                        my_sprite.height / (scaling * 2)
                    )

                    points = [(sx, sy), (ex, sy), (ex, ey), (sx, ey)]
                elif isinstance(
                    hitbox,
                    pytiled_parser.tiled_object.Polygon
                    | pytiled_parser.tiled_object.Polyline,
                ):
                    for point in hitbox.points:
                        adj_x = (
                            point.x
                            + hitbox.coordinates.x
                            - my_sprite.width / (scaling * 2)
                        )
                        adj_y = -(
                            point.y
                            + hitbox.coordinates.y
                            - my_sprite.height / (scaling * 2)
                        )
                        adj_point = adj_x, adj_y
                        points.append(adj_point)

                    if points[0][0] == points[-1][0] and points[0][1] == points[-1][1]:
                        points.pop()
                elif isinstance(hitbox, pytiled_parser.tiled_object.Ellipse):
                    if not hitbox.size:
                        print(
                            f"Warning: Ellipse hitbox created without a height "
                            f" or width for {tile.image}. Ignoring."
                        )
                        continue

                    hw = hitbox.size.width / 2
                    hh = hitbox.size.height / 2
                    cx = hitbox.coordinates.x + hw
                    cy = hitbox.coordinates.y + hh

                    acx = cx - (my_sprite.width / (scaling * 2))
                    acy = cy - (my_sprite.height / (scaling * 2))

                    total_steps = 8
                    angles = [
                        step / total_steps * 2 * math.pi for step in range(total_steps)
                    ]
                    for angle in angles:
                        x = hw * math.cos(angle) + acx
                        y = -(hh * math.sin(angle) + acy)
                        points.append((x, y))
                else:
                    print(f"Warning: Hitbox type {type(hitbox)} not supported.")

                if tile.flipped_vertically:
                    points = [(point[0], -point[1]) for point in points]

                if tile.flipped_horizontally:
                    points = [(-point[0], point[1]) for point in points]

                if tile.flipped_diagonally:
                    points = [(point[1], point[0]) for point in points]

                my_sprite.hit_box = RotatableHitBox(
                    points=points,
                    position=my_sprite.position,
                    angle=my_sprite.angle,
                    scale=my_sprite.scale_xy,
                )

        if tile.animation:
            key_frame_list = []
            for frame in tile.animation:
                frame_tile = self._get_tile_by_gid(
                    tile.tileset.firstgid + frame.tile_id
                )
                if frame_tile:
                    image_file = _get_image_source(frame_tile, map_directory)

                    if not frame_tile.tileset.image and image_file:
                        texture = _load_tilemap_texture(
                            image_file, hit_box_algorithm=hit_box_algorithm
                        )
                    elif image_file:
                        # No image for tile, pull from tilesheet
                        (
                            image_x,
                            image_y,
                            width,
                            height,
                        ) = _get_image_info_from_tileset(frame_tile)

                        texture = _load_tilemap_texture(
                            image_file,
                            x=image_x,
                            y=image_y,
                            width=width,
                            height=height,
                            hit_box_algorithm=hit_box_algorithm,
                        )
                    else:
                        msg = (
                            f"Warning: failed to load image for animation frame for "
                            f"tile '{frame_tile.id}', '{image_file}'."
                        )
                        raise RuntimeError(msg)

                    texture = _may_be_flip(tile, texture)

                    key_frame = TextureKeyframe(
                        texture=texture, duration=frame.duration, tile_id=frame.tile_id
                    )
                    key_frame_list.append(key_frame)

                    if len(key_frame_list) == 1:
                        my_sprite.texture = key_frame.texture

            my_sprite.animation = TextureAnimation(keyframes=key_frame_list)

        return my_sprite

    def _process_image_layer(
        self,
        layer: pytiled_parser.ImageLayer,
        texture_atlas: TextureAtlas,
        scaling: float = 1.0,
        hit_box_algorithm: HitBoxAlgorithm | None = None,
        offset: Vec2 = Vec2(0, 0),
        custom_class: type | None = None,
        custom_class_args: dict[str, Any] = {},
        *,
        use_spatial_hash: bool = False,
    ) -> SpriteList[Sprite]:
        sprite_list: SpriteList[Sprite] = SpriteList(
            use_spatial_hash=use_spatial_hash,
            atlas=texture_atlas,
            lazy=self._lazy,
        )

        map_source = self.tiled_map.map_file
        map_directory = map_source.parent
        image_file = layer.image

        if not image_file.exists() and map_directory.exists():
            try2 = Path(map_directory, image_file)
            if not try2.exists():
                print(
                    f"Warning, can't find image {image_file} for Image Layer {layer.name}"
                )
            image_file = try2

        my_texture = _load_tilemap_texture(
            image_file,
            hit_box_algorithm=hit_box_algorithm,
        )

        if layer.transparent_color:
            data = my_texture.image.getdata()

            target = layer.transparent_color
            new_data = []
            for item in data:
                if (
                    item[0] == target[0]
                    and item[1] == target[1]
                    and item[2] == target[2]
                ):
                    new_data.append((255, 255, 255, 0))
                else:
                    new_data.append(item)

            my_texture.image.putdata(new_data)

        if not custom_class:
            custom_class = Sprite
        elif not issubclass(custom_class, Sprite):
            msg = f"""
                    Tried to use a custom class {custom_class.__name__} for an
                    Image Layer that doesn't subclass arcade.Sprite.
                    Custom classes for image layers must subclass arcade.Sprite.
                """
            raise RuntimeError(msg)

        args = {
            "filename": image_file,
            "scale": scaling,
            "path_or_texture": my_texture,
            "hit_box_algorithm": hit_box_algorithm,
        }

        my_sprite = custom_class(**custom_class_args, **args)

        if layer.properties:
            sprite_list.properties = layer.properties
            for key, value in layer.properties.items():
                my_sprite.properties[key] = value

        if layer.tint_color:
            my_sprite.color = layer.tint_color

        if layer.opacity:
            my_sprite.alpha = int(layer.opacity * 255)

        my_sprite.center_x = (
            (layer.offset[0] * scaling) + my_sprite.width / 2
        ) + offset[0]
        my_sprite.top = (
            self.tiled_map.map_size.height * self.tiled_map.tile_size[1]
            - layer.offset[1]
        ) * scaling + offset[1]

        sprite_list.visible = layer.visible
        sprite_list.append(my_sprite)
        return sprite_list

    def _process_tile_layer(
        self,
        layer: pytiled_parser.TileLayer,
        texture_atlas: TextureAtlas,
        scaling: float = 1.0,
        hit_box_algorithm: HitBoxAlgorithm | None = None,
        offset: Vec2 = Vec2(0, 0),
        custom_class: type | None = None,
        custom_class_args: dict[str, Any] = {},
        *,
        use_spatial_hash: bool = False,
    ) -> SpriteList[Sprite]:
        sprite_list: SpriteList[Sprite] = SpriteList(
            use_spatial_hash=use_spatial_hash,
            atlas=texture_atlas,
            lazy=self._lazy,
        )
        map_array = layer.data
        if TYPE_CHECKING:
            # Can never be None because we already detect and reject infinite maps
            assert map_array

        # FIXME: get tile size from tileset
        # FIXME: why does the tile size need to be divided by 2?
        # FIXME: why is the tile size 140^2 and not 140x120?
        # FIXME: why is there a black outline? (too big?)

        # Loop through the layer and add in the list
        for row_index, row in enumerate(reversed(map_array)):
            for column_index, item in enumerate(row):
                # Check for an empty tile
                if item == 0:
                    continue

                tile = self._get_tile_by_gid(item)
                if tile is None:
                    msg = (
                        f"Couldn't find tile for item {item} in layer "
                        f"'{layer.name}' in file '{self.tiled_map.map_file}'"
                        f"at ({column_index}, {row_index})."
                    )
                    raise ValueError(msg)

                my_sprite = self._create_sprite_from_tile(
                    tile,
                    scaling=scaling,
                    hit_box_algorithm=hit_box_algorithm,
                    custom_class=custom_class,
                    custom_class_args=custom_class_args,
                )

                if my_sprite is None:
                    print(
                        f"Warning: Could not create sprite number {item} in layer '{layer.name}' {tile.image}"
                    )
                else:
                    # FIXME: handle map scaling
                    # Convert from odd-r offset to cube coordinates
                    offset_coord = hexagon.OffsetCoord(column_index, row_index)
                    hex_ = offset_coord.to_cube("even-r")

                    # Convert hex position to pixel position
                    pixel_pos = hex_.to_pixel(self.hex_layout)
                    # FIXME: why is the y position negative?
                    pixel_pos = hexagon.Point(pixel_pos.x, pixel_pos.y)
                    my_sprite.center_x = pixel_pos.x
                    my_sprite.center_y = pixel_pos.y

                    # Tint
                    if layer.tint_color:
                        my_sprite.color = layer.tint_color

                    # Opacity
                    opacity = layer.opacity
                    if opacity:
                        my_sprite.alpha = int(opacity * 255)

                    self.hex_tiles[hex_] = create_tile(hex_=hex_, sprite=my_sprite)

                    sprite_list.visible = layer.visible
                    sprite_list.append(my_sprite)

                if layer.properties:
                    sprite_list.properties = layer.properties

        return sprite_list

    def _process_object_layer(
        self,
        layer: pytiled_parser.ObjectLayer,
        texture_atlas: TextureAtlas,
        scaling: float = 1.0,
        hit_box_algorithm: HitBoxAlgorithm | None = None,
        offset: Vec2 = Vec2(0, 0),
        custom_class: type | None = None,
        custom_class_args: dict[str, Any] | None = None,
        *,
        use_spatial_hash: bool = False,
    ) -> tuple[SpriteList[Sprite] | None, list[TiledObject] | None]:
        if custom_class_args is None:
            custom_class_args = {}
        if not scaling:
            scaling = self.scaling

        sprite_list: SpriteList[Sprite] | None = None
        objects_list: list[TiledObject] | None = []

        shape: list[Point] | Rect | Point | None = None

        for cur_object in layer.tiled_objects:
            # shape: Optional[Union[Point, PointList, Rect]] = None
            if isinstance(cur_object, pytiled_parser.tiled_object.Tile):
                if not sprite_list:
                    sprite_list = SpriteList(
                        use_spatial_hash=use_spatial_hash,
                        atlas=texture_atlas,
                        lazy=self._lazy,
                    )

                tile = self._get_tile_by_gid(cur_object.gid)
                if tile is None:
                    msg = f"Tile with gid not found: {cur_object.gid}"
                    raise RuntimeError(msg)
                my_sprite = self._create_sprite_from_tile(
                    tile,
                    scaling=scaling,
                    hit_box_algorithm=hit_box_algorithm,
                    custom_class=custom_class,
                    custom_class_args=custom_class_args,
                )

                x = (cur_object.coordinates.x * scaling) + offset[0]
                y = (
                    (
                        self.tiled_map.map_size.height * self.tiled_map.tile_size[1]
                        - cur_object.coordinates.y
                    )
                    * scaling
                ) + offset[1]

                my_sprite.width = width = cur_object.size[0] * scaling
                my_sprite.height = height = cur_object.size[1] * scaling
                # center_x = width / 2
                # center_y = height / 2
                if cur_object.rotation:
                    rotation = math.radians(cur_object.rotation)
                else:
                    rotation = 0

                angle_degrees = math.degrees(rotation)
                rotated_center_x, rotated_center_y = rotate_point(
                    width / 2, height / 2, 0, 0, angle_degrees
                )

                my_sprite.position = (x + rotated_center_x, y + rotated_center_y)
                my_sprite.angle = angle_degrees

                if layer.tint_color:
                    my_sprite.color = layer.tint_color

                opacity = layer.opacity
                if opacity:
                    my_sprite.alpha = int(opacity * 255)

                if cur_object.properties and "change_x" in cur_object.properties:
                    my_sprite.change_x = prop_to_float(
                        cur_object.properties["change_x"]
                    )

                if cur_object.properties and "change_y" in cur_object.properties:
                    my_sprite.change_y = prop_to_float(
                        cur_object.properties["change_y"]
                    )

                if cur_object.properties and "boundary_bottom" in cur_object.properties:
                    my_sprite.boundary_bottom = prop_to_float(
                        cur_object.properties["boundary_bottom"]
                    )

                if cur_object.properties and "boundary_top" in cur_object.properties:
                    my_sprite.boundary_top = prop_to_float(
                        cur_object.properties["boundary_top"]
                    )

                if cur_object.properties and "boundary_left" in cur_object.properties:
                    my_sprite.boundary_left = prop_to_float(
                        cur_object.properties["boundary_left"]
                    )

                if cur_object.properties and "boundary_right" in cur_object.properties:
                    my_sprite.boundary_right = prop_to_float(
                        cur_object.properties["boundary_right"]
                    )

                if cur_object.properties:
                    my_sprite.properties.update(cur_object.properties)

                if cur_object.class_:
                    my_sprite.properties["class"] = cur_object.class_

                if cur_object.name:
                    my_sprite.properties["name"] = cur_object.name

                sprite_list.visible = layer.visible
                sprite_list.append(my_sprite)
                continue
            elif isinstance(cur_object, pytiled_parser.tiled_object.Point):
                x = cur_object.coordinates.x * scaling
                y = (
                    self.tiled_map.map_size.height * self.tiled_map.tile_size[1]
                    - cur_object.coordinates.y
                ) * scaling

                shape = (x + offset[0], y + offset[1])
            elif isinstance(cur_object, pytiled_parser.tiled_object.Rectangle):
                if cur_object.size.width == 0 and cur_object.size.height == 0:
                    print(
                        f"WARNING: Tiled object with ID {cur_object.id} is a rectangle "
                        "with a width and height of 0. Loading it as a single point."
                    )
                    x = cur_object.coordinates.x * scaling
                    y = (
                        self.tiled_map.map_size.height * self.tiled_map.tile_size[1]
                        - cur_object.coordinates.y
                    ) * scaling

                    shape = (x + offset[0], y + offset[1])
                else:
                    sx = cur_object.coordinates.x * scaling + offset[0]
                    sy = (
                        self.tiled_map.map_size.height * self.tiled_map.tile_size[1]
                        - cur_object.coordinates.y
                    ) * scaling + offset[1]

                    ex = sx + cur_object.size.width * scaling
                    ey = sy - cur_object.size.height * scaling

                    p1 = (sx, sy)
                    p2 = (ex, sy)
                    p3 = (ex, ey)
                    p4 = (sx, ey)

                    shape = [p1, p2, p3, p4]
            elif isinstance(
                cur_object,
                pytiled_parser.tiled_object.Polygon
                | pytiled_parser.tiled_object.Polyline,
            ):
                points: list[Point] = []
                shape = points
                for point in cur_object.points:
                    x = point.x + cur_object.coordinates.x
                    y = (self.height * self.tile_height) - (
                        point.y + cur_object.coordinates.y
                    )
                    point = (x + offset[0], y + offset[1])
                    points.append(point)

                # If shape is a polyline, and it is closed, we need to remove the duplicate end point
                if points[0][0] == points[-1][0] and points[0][1] == points[-1][1]:
                    points.pop()
            elif isinstance(cur_object, pytiled_parser.tiled_object.Ellipse):
                hw = cur_object.size.width / 2
                hh = cur_object.size.height / 2
                cx = cur_object.coordinates.x + hw
                cy = cur_object.coordinates.y + hh

                total_steps = 8
                angles = [
                    step / total_steps * 2 * math.pi for step in range(total_steps)
                ]
                points = []
                shape = points
                for angle in angles:
                    x = hw * math.cos(angle) + cx
                    y = -(hh * math.sin(angle) + cy)
                    point = (x + offset[0], y + offset[1])
                    points.append(point)
            elif isinstance(cur_object, pytiled_parser.tiled_object.Text):
                pass
            else:
                continue

            if shape:
                tiled_object = TiledObject(
                    shape, cur_object.properties, cur_object.name, cur_object.class_
                )

                if not objects_list:
                    objects_list = []

                objects_list.append(tiled_object)

        return sprite_list or None, objects_list or None


def load_tilemap(
    map_file: str | Path,
    hex_layout: hexagon.Layout,
    scaling: float = 1.0,
    layer_options: dict[str, dict[str, Any]] | None = None,
    hit_box_algorithm: HitBoxAlgorithm | None = None,
    offset: Vec2 = Vec2(0, 0),
    texture_atlas: TextureAtlas | None = None,
    *,
    lazy: bool = False,
    use_spatial_hash: bool = False,
) -> TileMap:
    """Given a .json map file, loads in and returns a `TileMap` object.

    A TileMap can be created directly using the classes `__init__` function.
    This function exists for ease of use.

    For more clarification on the layer_options key, see the `__init__` function
    of the `TileMap` class

    :param Union[str, Path] map_file: The JSON map file.
    :param scaling: The global scaling to apply to all Sprite's within the map.
    :param use_spatial_hash: If set to True, this will make moving a sprite
               in the SpriteList slower, but it will speed up collision detection
               with items in the SpriteList. Great for doing collision detection
               with static walls/platforms.
    :param hit_box_algorithm: The hit box algorithm to use for collision detection.
    :param Dict[str, Dict[str, Any]] layer_options: Layer specific options for the map.
    :param offset: Can be used to offset the position of all sprites and objects
            within the map. This will be applied in addition to any offsets from Tiled. This value
            can be overridden with the layer_options dict.
    :param lazy: SpriteLists will be created lazily.
    """
    return TileMap(
        map_file=map_file,
        hex_layout=hex_layout,
        scaling=scaling,
        layer_options=layer_options,
        use_spatial_hash=use_spatial_hash,
        hit_box_algorithm=hit_box_algorithm,
        offset=offset,
        texture_atlas=texture_atlas,
        lazy=lazy,
    )
