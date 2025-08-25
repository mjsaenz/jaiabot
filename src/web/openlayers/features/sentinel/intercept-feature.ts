import { Feature } from "ol";
import { Point } from "ol/geom";
import { Coordinate } from "ol/coordinate";
import { fromLonLat } from "ol/proj";
import { Icon, Style, Text, Fill } from "ol/style";

import { view } from "../../views/view";
import { Intercept } from "../../../types/protobuf-types";
import { MapFeatureTypes } from "../../../types/openlayers-types";

import interceptIcon from "../../../style/icons/sentinel/intercept-icon.svg";

export function generateInterceptFeature(botID: number, intercept: Intercept) {
    if (!intercept.location) {
        return new Feature();
    }

    const coordinate: Coordinate = [intercept.location.lon, intercept.location.lat];
    const feature = new Feature({
        geometry: new Point(fromLonLat(coordinate, view.getProjection())),
    });
    feature.set("type", MapFeatureTypes.SENTINAL_INTERCEPT);
    feature.set("id", botID);
    feature.setStyle(generateInterceptStyle(botID));
    return feature;
}

function generateInterceptStyle(botID: number) {
    return new Style({
        image: new Icon({
            src: interceptIcon,
            scale: 0.45,
        }),
        text: new Text({
            text: botID.toString(),
            font: "bold 11pt sans-serif",
            fill: new Fill({
                color: "white",
            }),
        }),
        zIndex: botID,
    });
}
