import express from "express";
import { getNotificationPrefs, updateNotificationPrefs } from "../controllers/notifications.controller.js";
import { verifyJWT } from "../middleware/auth.middleware.js";

const router = express.Router();

router.get("/preferences", verifyJWT, getNotificationPrefs);
router.patch("/preferences", verifyJWT, updateNotificationPrefs);

export default router;
