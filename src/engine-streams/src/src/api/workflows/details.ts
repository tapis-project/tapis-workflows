import axios from "axios"
import { errorDecoder } from "../utils/index.js"
import { WorkflowsApi, TapisApiResponse } from "../../types.js"

type ReqGetPipeline = {
    params: { 
        groupId: string,
        pipelineId: string
    }
}

interface RespGetPipeline {
    id: string
    groupId: string
}

const getPipeline: WorkflowsApi<ReqGetPipeline, RespGetPipeline> = (jwt, baseUrl, req) => {
    const axiosConfig = {
        
    };
    
    return errorDecoder<TapisApiResponse<RespGetPipeline>>(() => {
        return axios.get(
            `${baseUrl}/v3/workflows/groups/${req.params.groupId}/pipelines/${req.params.pipelineId}`,
            {
                headers: {
                    'X-Tapis-Token': jwt
                }
            }
        )
    })
}

export default getPipeline