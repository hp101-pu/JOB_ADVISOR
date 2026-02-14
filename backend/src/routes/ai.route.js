import { Router } from "express";
import { verifyJWT } from "../middleware/auth.middleware.js";
import { aiExecute, aiChat, aiChatStream } from "../controllers/ai.controller.js";

const router = Router();

router.post("/execute", verifyJWT, aiExecute);

// Chat proxy — verifyJWT reads the httpOnly cookie, then aiChat forwards
// the JWT as Bearer to the Python ask-seekr service.
router.post("/chat", verifyJWT, aiChat);

// Streaming chat proxy — forwards Server-Sent Events from the Python service.
router.post("/chat/stream", verifyJWT, aiChatStream);

export default router;
