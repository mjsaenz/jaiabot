import JaiaVectorLayer from "../jaia-vector-layer";
import { LayerTitles } from "../../../../types/openlayers-types";
import { InterceptState, TrackState } from "../../../../types/protobuf-types";
import { layersZIndexes } from "../../zindex";
import { generateTrackFeature } from "../../../features/sentinel/track-feature";
import {
    generateInterceptFeature,
    generateInterceptLineFeature,
} from "../../../features/sentinel/intercept-feature";
import { sentinel } from "../../../../data/sentinel/sentinel";

class SentinelLayer extends JaiaVectorLayer {
    constructor() {
        super(LayerTitles.SENTINEL_LAYER, layersZIndexes.get(LayerTitles.SENTINEL_LAYER));
    }

    override updateFeatures() {
        let source = this.getVectorLayer().getSource();
        source.clear();

        for (const [trackID, track] of sentinel.getTracks()) {
            if (
                track.track_state === TrackState.ABANDONED ||
                track.track_state === TrackState.DEAD ||
                track.track_state === TrackState.REMOVED_HIDDEN
            ) {
                continue;
            }
            const trackFeature = generateTrackFeature(track);
            source.addFeature(trackFeature);
        }

        for (const [botID, intercept] of sentinel.getIntercepts()) {
            const interceptFeature = generateInterceptFeature(intercept);
            source.addFeature(interceptFeature);

            if (intercept.state === InterceptState.IN_PROGRESS) {
                const interceptLineFeature = generateInterceptLineFeature(intercept);
                source.addFeature(interceptLineFeature);
            }
        }
    }
}

export const sentinelLayer = new SentinelLayer();
