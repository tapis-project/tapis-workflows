import express from 'express';
import expressWs from "express-ws";
import routes from "./routes.js"
import { withHasPipelinePerms } from "./middleware/routing/index.js"


const { app } = expressWs(express());

// Initialize the routes with their message handlers
Object.keys(routes).map(key => {
    app.ws(key, (ws, req) => {
        withHasPipelinePerms(routes[key])(ws, req)
    })
})

// Start the server
const PORT = process.env.PORT || 8999;
app.listen(PORT, () => { console.log(`Listening on port ${PORT}`) })