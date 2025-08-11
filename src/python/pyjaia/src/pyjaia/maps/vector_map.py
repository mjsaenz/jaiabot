from dataclasses import dataclass
from typing import Literal


Coordinate = tuple[float, float]


@dataclass
class Geometry:
    type: Literal["Point", "LineString", "Polygon"]
    coordinates: Coordinate | list[Coordinate]


@dataclass
class Feature:
    type: str
    properties: dict[str, any]
    geometry: Geometry


@dataclass
class Style:
    fill: any = 'white'
    outline: any = None
    width: float = 4


@dataclass
class MapStyle:
    sea_area: Style


ecdis_style = {
    "sea_area": Style(fill='#82bdff'),
    "land_area": Style(fill='#cec58a'),
    "coastline": Style(fill='#2d2d22'),
    "anchor_area": Style(fill=None, outline='#c743c7')
}


@dataclass
class VectorMap:
    extent: tuple[float, float, float, float]
    features: list[Feature]


    def draw_to_png(self, png_path: str, extent: list[float]=None, style:dict[str, Style]=ecdis_style, meters_per_pixel=5.0, oversampling=2):
        from PIL import Image, ImageDraw

        if extent is None:
            extent = self.extent

        size = (oversampling * int(round((extent[1] - extent[0]) / meters_per_pixel)), \
                oversampling * int(round((extent[3] - extent[2]) / meters_per_pixel)))

        image = Image.new(mode='RGB', size=size)
        draw = ImageDraw.Draw(image)

        def get_pixcoords(point: Coordinate):
            return ((point[0] - extent[0]) / meters_per_pixel, \
                    (extent[3] - point[1]) / meters_per_pixel)

        for feature in self.features:
            feature_style = style.get(feature.type)
            if feature_style:
                geom_type = feature.geometry.type
                if geom_type == 'Polygon':
                    pixcoords = tuple(map(get_pixcoords, feature.geometry.coordinates))
                    draw.polygon(pixcoords, fill=feature_style.fill, outline=feature_style.outline, width=feature_style.width)
                elif geom_type == 'LineString':
                    pixcoords = tuple(map(get_pixcoords, feature.geometry.coordinates))
                    draw.line(pixcoords, fill=feature_style.fill, width=feature_style.width)
                elif geom_type == 'Point':
                    center = get_pixcoords(feature.geometry.coordinates)
                    vertices = ((center[0] - feature_style.width, center[1] - feature_style.width),
                                (center[0] + feature_style.width, center[1] + feature_style.width))
                    draw.ellipse(vertices, fill=feature_style.fill, width=feature_style.width)
                else:
                    print(f'Unknown geometry type: {geom_type}')
        
        image = image.resize((size[0] // oversampling, size[1] // oversampling))

        image.show()

    