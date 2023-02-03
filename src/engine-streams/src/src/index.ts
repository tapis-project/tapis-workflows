import express from 'express';
import expressWs from "express-ws";
import { createStream } from './utils/index.js';
// import { Workflows } from '@tapis/tapis-typescript';

const { app } = expressWs(express());

// Route for pipeline run logs
app.ws('/group/:groupId/pipeline/:pipelineId/run/:pipelineRunUuid', (ws, req) => {
    ws.on('message', (msg) => {
        ws.send("Websocket connection established...\nStreaming run logs")
        
        // Validate message and check user authorization for this pipeline
        const message = JSON.parse(msg.toString())
        if (message.JWT === undefined) {
            ws.send("Access Forbidden: No JWT found in message")
            // ws.close()
        }
        
        // TODO check JWT sent in message
        const stream = createStream("run", req.params)
        stream.on('error', function (error) {
            ws.send(`ERROR: ${error.message}`);
        })

        stream.on("data", (chunk) => {
            ws.send(chunk.toString())
        })
    })

    ws.on('close', () => {
        console.log('WebSocket was closed')
    })
})

// Route for task execution .stdout
app.ws('/group/:groupId/pipeline/:pipelineId/run/:pipelineRunUuid/task/:taskId', (ws, req) => {
    ws.on('message', msg => {
        ws.send("Websocket connection established...\nStreaming task stdout")
        
        // Validate message and check user authorization for this pipeline
        const message = JSON.parse(msg.toString())
        if (message.JWT === undefined) {
            ws.send("Access Forbidden: No JWT found in message")
            // ws.close()
        }

        // Create the .stdout read stream
        const stream = createStream("execution", req.params)

        // Send message on error
        stream.on('error', function (error) {
            ws.send(`ERROR: ${error.message}`);
        })

        // Send the data to the client
        stream.on("data", (chunk) => {
            ws.send(chunk.toString())
        })
    })


    ws.on('close', () => {
        console.log('WebSocket was closed')
    })
})

// Start the server
const PORT = process.env.PORT || 8999;
app.listen(PORT, () => { console.log(`Listening on port ${PORT}`) })