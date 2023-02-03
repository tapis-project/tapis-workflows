import fs from "fs"
import { ParamsDictionary } from "express-serve-static-core"

type Context = "run" | "execution"

type CreateStreamFn = (
    context: Context,
    params: ParamsDictionary
) => fs.ReadStream


export const createStream: CreateStreamFn = (context, params) => {
    let filename = null
    switch (context) {
        case "run":
            filename = `/mnt/pipelines/${params.groupId}/${params.pipelineId}/runs/${params.pipelineRunUuid}/logs.txt`
            break;
        case "execution":
            filename = `/mnt/pipelines/${params.groupId}/${params.pipelineId}/runs/${params.pipelineRunUuid}/${params.taskId}/output/.stdout`
            break;
    }
    
    return fs.createReadStream(filename, "utf-8")
}