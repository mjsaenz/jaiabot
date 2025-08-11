#!/usr/bin/env python3

from osgeo import ogr, osr
from PIL import Image, ImageDraw
import os.path
from dataclasses import dataclass
from .vector_map import *


ogr.UseExceptions()
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


layer_to_type_map = {
    "SEAARE": "sea_area",
    "LNDARE": "land_area",
    "ACHARE": "anchor_area",
    "COALNE": "coastline"
}


def read_s57(s57_file_path: str) -> VectorMap:
    basename = os.path.basename(s57_file_path)
    dataset: ogr.DataSource = ogr.Open(s57_file_path)

    if dataset is None:
        raise Exception(f"Could not open: {s57_file_path}")


    extent_web_mercator = get_extent_web_mercator(dataset)


    features: list[Feature] = []
    for layer_name in layer_to_type_map:
        layer: ogr.Layer = dataset.GetLayerByName(layer_name)

        if layer is None:
            print(f"Missing layer {layer_name}")
            continue

        feature_type = layer_to_type_map[layer_name]

        # Get the coordinate transformation to web mercator from this layer
        spatial_ref = layer.GetSpatialRef()
        if spatial_ref is None:
                # If the S-57 has no spatial reference, let's assume it's lat/long (EPSG 4326)
                spatial_ref = osr.SpatialReference()
                spatial_ref.ImportFromEPSG(4326)

        coord_trans = osr.CoordinateTransformation(spatial_ref, WEB_MERCATOR_SPATIAL_REF)


        def get_web_mercator_coordinates(geom: ogr.Geometry):
            geom.Transform(coord_trans)
            for i in range(geom.GetPointCount()):
                point = geom.GetPoint_2D(i)
                yield point


        for ogr_feature in layer:
            ogr_feature:ogr.Feature
            ogr_geom: ogr.Geometry = ogr_feature.GetGeometryRef()
            ogr_geom_type = ogr_geom.GetGeometryType()

            if ogr_geom_type == ogr.wkbLineString:
                geom_type = 'LineString'
                coordinates = tuple(get_web_mercator_coordinates(ogr_geom))
            elif ogr_geom_type == ogr.wkbPolygon:
                geom_type = 'Polygon'
                # Exterior ring
                exterior_ring_geom = ogr_geom.GetGeometryRef(0)
                coordinates = tuple(get_web_mercator_coordinates(exterior_ring_geom))
            elif ogr_geom_type == ogr.wkbPoint:
                geom_type = 'Point'
                coordinates = tuple(get_web_mercator_coordinates(ogr_geom))[0]
            else:
                print(f'Unknown geometry type: {ogr_geom.GetGeometryName()}')

            features.append(Feature(type=feature_type, properties={}, geometry=Geometry(geom_type, coordinates)))

    map = VectorMap(features=features, extent=extent_web_mercator)
    return map


def tilify(s57_file_path: str, tiles_root_path: str):
    vector_map = read_s57(s57_file_path)
    vector_map.draw_to_png(tiles_root_path + 'map.png')


def dump_json(s57_file_path: str):
    import json
    dataset: ogr.DataSource = ogr.Open(s57_file_path)

    if dataset is None:
        raise Exception(f"Could not open: {s57_file_path}")


    # Read layer data
    def get_layer_json(layer: ogr.Layer):
        layer_defn: ogr.FeatureDefn = layer.GetLayerDefn()

        defn_json = []
        for i in range(layer_defn.GetFieldCount()):
            field_defn: ogr.FieldDefn = layer_defn.GetFieldDefn(i)
            defn_json.append({
                "name": field_defn.GetName(),
                "type": field_defn.GetTypeName(),
                "width": field_defn.GetWidth(),
                "precision": field_defn.GetPrecision()
            })

        return {
            "name": layer.GetName(),
            "definition": defn_json,
            "geom_type": ogr.GeometryTypeToName(layer_defn.GetGeomType())
        }


    json_layers = []
    for i in range(dataset.GetLayerCount()):
        layer: ogr.Layer = dataset.GetLayerByIndex(i)
        json_layers.append(get_layer_json(layer))


    # Dump to json file
    json_object = {
        "layers": json_layers
    }
    output_path = os.path.basename(s57_file_path) + '.json'
    print(output_path)
    json.dump(json_object, open(output_path, 'w'), indent=2)


def main():
    import argparse
    parser = argparse.ArgumentParser('jaia-s57-tool', description='Work with S57 ENCs.')
    parser.add_argument('action', help='Action [dump_json, tilify]')
    parser.add_argument('s57_file_path')
    parser.add_argument('-o', dest='output_path')

    @dataclass
    class Args:
        action: str
        s57_file_path: str
        output_path: str

    args: Args = parser.parse_args()

    if args.action == 'dump_json':
        dump_json(args.s57_file_path)
    elif args.action == 'tilify':
        tilify(args.s57_file_path, args.output_path)
    else:
        print('Unknown option: ' + args.action)
        exit(1)


if __name__ == '__main__':
    main()

