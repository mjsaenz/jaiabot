import { useContext } from "react";
import { JaiaDispatchContext } from "../../context/JaiaContext";
import { JaiaActions } from "../../context/jaia-actions";
import { Intercept } from "../../types/protobuf-types";
import "./SentinelPanelTrack.less";

interface Props {
    intercept: Intercept;
}

export default function SentinelPanelIntercept(props: Props) {
    const jaiaDispatch = useContext(JaiaDispatchContext);

    const handleClickedCloseButton = () => {
        jaiaDispatch({ type: JaiaActions.CLOSED_SENTINEL_PANEL });
    };

    return (
        <div className="jaia-panel sentinel-panel">
            <div className="jaia-panel-title">Intercept {props.intercept.bot_id}</div>
            <div className="track-data-container">
                <div className="label">Track ID:</div>
                <div>{props.intercept?.track_id}</div>

                <div className="label">Bot ID:</div>
                <div>{props.intercept?.bot_id}</div>

                <div className="label">State:</div>
                <div>{props.intercept?.state}</div>

                <div className="label">Lat:</div>
                <div>{props.intercept?.location?.lat?.toFixed(5)}</div>

                <div className="label">Lon:</div>
                <div>{props.intercept?.location?.lon?.toFixed(5)}</div>
            </div>

            <div className="action-buttons-container">
                <button onClick={() => handleClickedCloseButton()}>Close</button>
            </div>
        </div>
    );
}
