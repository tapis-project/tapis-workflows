import { Routes } from "./types.js"
import { onRunLogStream, onExecutionResultStream } from "./middleware/connection/index.js"

const routes: Routes = {
    '/group/:groupId/pipeline/:pipelineId/run/:pipelineRunUuid': onRunLogStream,
    '/group/:groupId/pipeline/:pipelineId/run/:pipelineRunUuid/task/:taskId': onExecutionResultStream,
}

export default routes