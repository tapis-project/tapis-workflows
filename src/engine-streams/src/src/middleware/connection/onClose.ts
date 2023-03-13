import { ConnectionMiddleware } from "../../types.js"

const onClose: ConnectionMiddleware = () => {
    console.log("Wesbocket closed")
}

export default onClose