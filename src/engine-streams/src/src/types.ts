import { WebSocket, RawData } from "ws";
import { Request } from "express-serve-static-core"

// Middleware
export type ConnectionMiddleware = (ws: WebSocket, req: Request) => void
export type ConnectionMiddlewareWithCallback = (ws: WebSocket, req: Request, next: ConnectionMiddleware) => void
export type MessageMiddleware = (ws: WebSocket, req: Request, msg: RawData) => void
export type RoutingMiddleware = (next: ConnectionMiddleware) => ConnectionMiddleware
export type Routes = {[key: string]: ConnectionMiddleware}

// Api
export type TapisApiResponse<T> = {
    status: string,
    message: string,
    version: string
    result: T,
    metadata: object
}
export type WorkflowsApi<Req, Resp> = (
    jwt: string,
    baseUrl: string,
    request: Req
) => Promise<TapisApiResponse<Resp>>