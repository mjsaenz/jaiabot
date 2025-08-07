#!/usr/bin/env python3

from osgeo import ogr, osr
from PIL import Image, ImageDraw
import os.path
from dataclasses import dataclass


WEB_MERCATOR_SPATIAL_REF = osr.SpatialReference()
WEB_MERCATOR_SPATIAL_REF.ImportFromEPSG(3857)


def get_extent_web_mercator(dataset: ogr.DataSource):
    """Gets the extent of an S-57 dataset in web mercator coordinates.

    Args:
        dataset (any): A gdal dataset representing an S-57 ENC.

    Returns:
        (tuple[float, float, float, float]): The extent as a 4-tuple.
    """
    dataset_extent: tuple[float, float, float, float] = None

    for i in range(dataset.GetLayerCount()):
        layer = dataset.GetLayerByIndex(i)

        # Get the layer definition
        layer_definition = layer.GetLayerDefn()
        geometry_type = layer_definition.GetGeomType()
        if geometry_type == ogr.wkbNone:
            # This layer has no geometry, so the extent will not be valid, carry on to the next layer
            continue

        # Get the coordinate transformation to web mercator from this layer
        spatial_ref = layer.GetSpatialRef()
        if spatial_ref is None:
                # If the S-57 has no spatial reference, let's assume it's lat/long (EPSG 4326)
                spatial_ref = osr.SpatialReference()
                spatial_ref.ImportFromEPSG(4326)

        coord_trans = osr.CoordinateTransformation(spatial_ref, WEB_MERCATOR_SPATIAL_REF)

        # Transform this layer's extent
        layer_extent = layer.GetExtent()

        # Create a point geometry
        line_string = ogr.Geometry(ogr.wkbLineString)
        line_string.AddPoint(layer_extent[0], layer_extent[2])
        line_string.AddPoint(layer_extent[1], layer_extent[3])

        # Assign the input SRS to the point
        line_string.AssignSpatialReference(spatial_ref)

        # Perform the transformation
        line_string.Transform(coord_trans)
        layer_extent_web_mercator = line_string.GetEnvelope()

        if dataset_extent is None:
            dataset_extent = layer_extent_web_mercator
        else:
            dataset_extent = (min(layer_extent_web_mercator[0], dataset_extent[0]), max(layer_extent_web_mercator[1], dataset_extent[1]), \
                            min(layer_extent_web_mercator[2], dataset_extent[2]), max(layer_extent_web_mercator[3], dataset_extent[3]))

    return dataset_extent


@dataclass
class LayerStyle:
    layer_name: str
    fill: any = 'white'
    outline: any = None
    width: float = 4


layer_styles = [
    LayerStyle('SEAARE', fill='#82bdff'),
    LayerStyle('LNDARE', fill='#cec58a'),
    LayerStyle('BUAARE', fill='lightgreen'),
    LayerStyle('ACHARE', fill=None, outline='#c743c7'),

    LayerStyle('BCNLAT', fill='pink'),
    LayerStyle('BCNSPP', fill='red'),
    LayerStyle('COALNE', fill='#2d2d22'),
    LayerStyle('BRIDGE', fill='orange'),
    LayerStyle('BUISGL', fill='yellow'),
    LayerStyle('BOYLAT', fill='lightblue'),
    LayerStyle('BOYSPP', fill='purple'),
]



def convert_to_tiles(s57_file_path: str, tiles_root_path: str, meters_per_pixel=5.0):
    basename = os.path.basename(s57_file_path)

    ogr.UseExceptions()
    dataset: ogr.DataSource = ogr.Open(s57_file_path)

    if dataset is None:
        raise Exception(f"Could not open: {s57_file_path}")


    extent_web_mercator = get_extent_web_mercator(dataset)
    size = (int(round((extent_web_mercator[1] - extent_web_mercator[0]) / meters_per_pixel)), \
            int(round((extent_web_mercator[3] - extent_web_mercator[2]) / meters_per_pixel)))


    image = Image.new(mode='RGB', size=size)
    draw = ImageDraw.Draw(image)


    for i in range(dataset.GetLayerCount()):
        layer: ogr.Layer = dataset.GetLayerByIndex(i)
        print(layer.GetName())


    for layer_style in layer_styles:
        layer: ogr.Layer = dataset.GetLayerByName(layer_style.layer_name)

        # Get the coordinate transformation to web mercator from this layer
        spatial_ref = layer.GetSpatialRef()
        if spatial_ref is None:
                # If the S-57 has no spatial reference, let's assume it's lat/long (EPSG 4326)
                spatial_ref = osr.SpatialReference()
                spatial_ref.ImportFromEPSG(4326)

        coord_trans = osr.CoordinateTransformation(spatial_ref, WEB_MERCATOR_SPATIAL_REF)


        def get_points_pixcoords(geom: ogr.Geometry):
            geom.Transform(coord_trans)
            for i in range(geom.GetPointCount()):
                point = geom.GetPoint_2D(i)
                yield ((point[0] - extent_web_mercator[0]) / meters_per_pixel, \
                        (extent_web_mercator[3] - point[1]) / meters_per_pixel)


        for feature in layer:
            feature:ogr.Feature
            geom: ogr.Geometry = feature.GetGeometryRef()
            geom_type = geom.GetGeometryType()

            if geom_type == ogr.wkbLineString:
                vertices = tuple(get_points_pixcoords(geom))
                draw.line(vertices, fill=layer_style.fill, width=layer_style.width)
            
            elif geom_type == ogr.wkbPolygon:
                # Exterior ring
                exterior_ring_geom = geom.GetGeometryRef(0)
                vertices = tuple(get_points_pixcoords(exterior_ring_geom))
                draw.polygon(vertices, fill=layer_style.fill, outline=layer_style.outline, width=layer_style.width)
            
            elif geom_type == ogr.wkbPoint:
                center = tuple(get_points_pixcoords(geom))[0]
                vertices = ((center[0] - layer_style.width, center[1] - layer_style.width),
                            (center[0] + layer_style.width, center[1] + layer_style.width))
                draw.ellipse(vertices, fill=layer_style.fill, width=layer_style.width)

            else:
                print(f'Unknown geometry type: {geom.GetGeometryName()}')


    image.show()
    # image.save(open(f"{tiles_root_path}/{basename}.png", "wb"), "PNG")


    #         spatial_ref = layer.GetSpatialRef()
    #         if spatial_ref is None:
    #              # If the S-57 has no spatial reference, let's assume it's lat/long (EPSG 4326)
    #              spatial_ref = osr.SpatialReference()
    #              spatial_ref.ImportFromEPSG(4326)
    #         epsg_code = spatial_ref.GetAttrValue("AUTHORITY", 1)

    #         coord_trans = osr.CoordinateTransformation(spatial_ref, WEB_MERCATOR_SPATIAL_REF)

    #         # print(f"Layer Name: {layer_name}")
    #         # print(f'  extent: {layer.GetExtent()}')
    #         # print(f'  epsg code: {epsg_code}')

    #         for feature in layer:
    #             try:
    #                 obj_name = feature.GetField("OBJNAM")
    #                 # print(obj_name)
    #             except KeyError:
    #                 pass
                
    #             # Access geometry
    #             geom = feature.GetGeometryRef()
    #             if geom:
    #                 geom.Transform(coord_trans)
    #                 # print(f"  Geometry Type: {geom.GetGeometryName()}")
    #                 # print(f'  Geometry: {geom}')



def create_tileset_main():
    import sys

    s57_file_path, tiles_root_path = sys.argv[1:]

    convert_to_tiles(s57_file_path, tiles_root_path)


if __name__ == '__main__':
    create_tileset_main()

