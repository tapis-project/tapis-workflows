
import { ConnectionMiddleware } from '../../types.js';
import { createReadStream } from './utils/index.js';

const onRunLogStream: ConnectionMiddleware = (ws, req) => {
    const stream = createReadStream("run", req.params)
    stream.on('error', function (error) {
        ws.send(`ERROR: ${error.message}`);
    })

    stream.on("data", (chunk) => {
        ws.send(chunk.toString())
    })
}

export default onRunLogStream