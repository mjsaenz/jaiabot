import { Feature } from "ol";
import { Coordinate } from "ol/coordinate";
import { fromLonLat } from "ol/proj";
import { LineString, Point } from "ol/geom";
import { Icon, Style, Text, Fill, Stroke } from "ol/style";

import { bots } from "../../../data/bots/bots";
import { view } from "../../views/view";
import { Intercept, InterceptState } from "../../../types/protobuf-types";
import { MapFeatureTypes } from "../../../types/openlayers-types";

import interceptIcon from "../../../style/icons/sentinel/intercept-icon.svg";
import { OpenLayersColors } from "../../../style/openlayers/colors";

export function generateInterceptFeature(intercept: Intercept) {
    if (!intercept.location) {
        return new Feature();
    }

    const coordinate: Coordinate = [intercept.location.lon, intercept.location.lat];
    const feature = new Feature({
        geometry: new Point(fromLonLat(coordinate, view.getProjection())),
    });
    feature.set("type", MapFeatureTypes.SENTINAL_INTERCEPT);
    feature.set("id", intercept.bot_id);
    feature.setStyle(generateInterceptStyle(intercept));
    return feature;
}

function generateInterceptStyle(intercept: Intercept) {
    let opacity = 1;
    if (intercept.state !== InterceptState.IN_PROGRESS) {
        opacity = 0.25;
    }

    return new Style({
        image: new Icon({
            src: interceptIcon,
            scale: 0.45,
            opacity: opacity,
        }),
        text: new Text({
            text: intercept.bot_id?.toString(),
            font: "bold 11pt sans-serif",
            fill: new Fill({
                color: "white",
            }),
        }),
        zIndex: intercept.bot_id,
    });
}

export function generateInterceptLineFeature(intercept: Intercept) {
    const botLocation = bots.getBot(intercept.bot_id)?.getLocation();

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
    feature.setStyle(generateInterceptLineStyle(intercept));
    return feature;
}

function generateInterceptLineStyle(intercept: Intercept) {
    return new Style({
        stroke: new Stroke({
            width: 4,
            color: OpenLayersColors.MEASURE_LINE,
            lineDash: [15, 30],
        }),
        zIndex: intercept.bot_id,
    });
}
