import { Feature } from "ol";
import { Coordinate } from "ol/coordinate";
import { fromLonLat } from "ol/proj";
import { LineString, Point } from "ol/geom";
import { Icon, Style, Text, Fill, Stroke } from "ol/style";

import { bots } from "../../../data/bots/bots";
import { view } from "../../views/view";
import { Intercept } from "../../../types/protobuf-types";
import { MapFeatureTypes } from "../../../types/openlayers-types";

import interceptIcon from "../../../style/icons/sentinel/intercept-icon.svg";
import { OpenLayersColors } from "../../../style/openlayers/colors";

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

export function generateInterceptLineFeature(botID: number, intercept: Intercept) {
    const botLocation = bots.getBot(botID)?.getLocation();

    if (!botLocation || !intercept.location) {
        return new Feature();
    }

    const startCoordinate = fromLonLat([botLocation.lon, botLocation.lat], view.getProjection());
    const endCoordinate = fromLonLat(
        [intercept.location.lon, intercept.location.lat],
        view.getProjection(),
    );

    const feature = new Feature({
        geometry: new LineString([startCoordinate, endCoordinate]),
    });
    feature.setStyle(generateInterceptLineStyle(botID));
    return feature;
}

function generateInterceptLineStyle(botID: number) {
    return new Style({
        stroke: new Stroke({
            width: 4,
            color: OpenLayersColors.MEASURE_LINE,
            lineDash: [15, 30],
        }),
        zIndex: botID,
    });
}
