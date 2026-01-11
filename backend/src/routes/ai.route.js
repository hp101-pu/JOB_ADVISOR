import { Router } from "express";
import { verifyJWT } from "../middleware/auth.middleware.js";
import { aiExecute, aiChat } from "../controllers/ai.controller.js";

const router = Router();

router.post("/execute", verifyJWT, aiExecute);

// Chat proxy — verifyJWT reads the httpOnly cookie, then aiChat forwards
// the JWT as Bearer to the Python ask-seekr service.
router.post("/chat", verifyJWT, aiChat);

export default router;
