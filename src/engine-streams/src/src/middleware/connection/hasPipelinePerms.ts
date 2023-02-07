import jwtDecode from "jwt-decode"
import { ConnectionMiddlewareWithCallback } from "../../types.js"
import { getPipeline } from "../../api/workflows/index.js"

interface DecodedJWT {
    iss: string
}

const hasPipelinePerms: ConnectionMiddlewareWithCallback = (ws, req, next) => {
    if (req.query.jwt === undefined) {
        ws.send("Unauthorized: Missing JWT")
        ws.close()
    }

    const jwt = req.query.jwt as string;
    const baseUrl = jwtDecode<DecodedJWT>(jwt).iss.replace("/v3/tokens", "");
    
    if (!baseUrl) {
        ws.send("Unauthorized: Malformed JWT")
        ws.close()
    }

    try {
        getPipeline(jwt, baseUrl, {
            params: {
                groupId: req.params.groupId,
                pipelineId: req.params.pipelineId
            }
        }).then((resp) => {
            next(ws, req)
        }).catch((error) => {
            console.log(error.message)
        })
    } catch (e) {
        console.log(`Error: There was an error`)
    }

    
}

export default hasPipelinePerms