import JaiaVectorLayer from "../jaia-vector-layer";
import { LayerTitles } from "../../../../types/openlayers-types";
import { layersZIndexes } from "../../zindex";
import { generateTrackFeature } from "../../../features/sentinel/track-feature";
import { sentinel } from "../../../../data/sentinel/sentinel";
import { TrackState } from "../../../../types/protobuf-types";

class SentinelLayerDead extends JaiaVectorLayer {
    constructor() {
        super(LayerTitles.SENTINEL_LAYER_DEAD, layersZIndexes.get(LayerTitles.SENTINEL_LAYER_DEAD));
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
                const trackFeature = generateTrackFeature(track);
                source.addFeature(trackFeature);
            }
        }
    }
}

export const sentinelLayerDead = new SentinelLayerDead();
