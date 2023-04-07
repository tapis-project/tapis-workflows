import { ConnectionMiddleware } from '../../types.js';
import { createReadStream } from './utils/index.js';

const onExecutionResultStream: ConnectionMiddleware = (ws, req) => {
    const stream = createReadStream("execution", req.params)
    stream.on('error', function (error) {
        ws.send(`ERROR: ${error.message}`);
    })

    stream.on("data", (chunk) => {
        ws.send(chunk.toString())
    })
}

export default onExecutionResultStream