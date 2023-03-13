import { RoutingMiddleware } from "../../types"
import { hasPipelinePerms, onClose } from "../connection/index.js"

const withHasPipelinePerms: RoutingMiddleware = (next) => {
    return (ws, req) => {
        hasPipelinePerms(ws, req, next)
        ws.on('close', onClose)
    }
}

export default withHasPipelinePerms