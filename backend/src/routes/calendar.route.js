import { Router } from "express";
import { verifyJWT } from "../middleware/auth.middleware.js";
import {
  createCalendarEvent,
  getCalendarAuthUrl,
  handleCalendarOAuthCallback,
  getCalendarEvents,
  getAllCalendarEvents,
  deleteCalendarEvent,
  getCalendarConnectionStatus,
  disconnectCalendar,
} from "../controllers/calendar.controller.js";

const router = Router();

/* --------------- PUBLIC (for OAuth callback) -------------- */
router.get("/oauth-callback", handleCalendarOAuthCallback);

/* --------------- PROTECTED -------------- */
router.use(verifyJWT); // Apply to all routes below

router.get("/auth-url", getCalendarAuthUrl);
router.get("/status", getCalendarConnectionStatus);
router.get("/events/all", getAllCalendarEvents);          // all DB events, no date filter
router.get("/events", getCalendarEvents);                 // date-range, syncs from Google
router.post("/events", createCalendarEvent);
router.delete("/events/:googleEventId", deleteCalendarEvent); // delete from Google + DB
router.delete("/disconnect", disconnectCalendar);

export default router;