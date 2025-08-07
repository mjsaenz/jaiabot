from osgeo import ogr, osr


WEB_MERCATOR_SPATIAL_REF = osr.SpatialReference()
WEB_MERCATOR_SPATIAL_REF.ImportFromEPSG(3857)


def get_extent_web_mercator(dataset: any):
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


def convert_to_tiles(s57_file_path: str, tiles_root_path: str):
    ogr.UseExceptions()
    dataset = ogr.Open(s57_file_path)

    if dataset is None:
        raise Exception(f"Could not open: {s57_file_path}")


    extent_web_mercator = get_extent_web_mercator(dataset)
    print(extent_web_mercator)

    # for i in range(dataset.GetLayerCount()):
    #         layer = dataset.GetLayerByIndex(i)
    #         layer_name = layer.GetName()

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

