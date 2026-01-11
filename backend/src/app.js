import path from "path";
import express from "express";
import cookieParser from "cookie-parser";
import cors from "cors";

const app = express();

// --------------------
// Middleware
// --------------------
app.use(
  cors({
    origin: process.env.CORS_ORIGIN || "http://localhost:5173",
    credentials: true,
    methods: ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allowedHeaders: ["Content-Type", "Authorization", "X-Service-Key"],
  })
);

app.use(cookieParser());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(express.static("public"));
app.use("/uploads", express.static("public/uploads"));

// --------------------
// Route imports
// --------------------
import userRouter from "./routes/user.route.js";
import userAuthRouter from "./routes/google_auth.route.js"
import emailRoutes from "./routes/email.route.js";
import internalGoogleRoutes from "./routes/internal_google.route.js";
import googleSyncRoutes from "./routes/google_sync.route.js";
import jobsRouter from "./routes/jobs.route.js";
import calendarRouter from "./routes/calendar.route.js";
import profileRoutes from "./routes/profile.route.js";
import aiRoutes from "./routes/ai.route.js"
import notificationsRouter from "./routes/notifications.route.js"
import resumeRouter from "./routes/resume.route.js";
import { sseService } from "./services/sse.service.js";
import { verifyJWT } from "./middleware/auth.middleware.js";
// --------------------
// Route mounting
// --------------------
app.use("/api/user", userRouter);
app.use("/api/profile", profileRoutes);
app.use("/api/calendar", calendarRouter);
// auth = login / register / me
app.use("/api/auth", userAuthRouter);

app.use("/api/jobs", jobsRouter);

// emails CRUD
app.use("/api/emails", emailRoutes);




// 🔐 INTERNAL SERVICE ROUTES (VERY IMPORTANT)
app.use("/internal/google", internalGoogleRoutes);

app.use("/sync/google",googleSyncRoutes)

app.use("/api/ai",aiRoutes)
app.use("/api/notifications", notificationsRouter)

// Resume upload + parse routes
app.use("/api/resume", resumeRouter);
// SSE — real-time push to browser when cron syncs new emails
app.get("/api/sse", verifyJWT, (req, res) => {
  if (!req.user?._id) {
    return res.status(401).json({ message: "Unauthorized" });
  }
  const userId = String(req.user._id);
  sseService.addClient(userId, res);
  req.on("close", () => sseService.removeClient(userId));
});

// --------------------
// Health check
// --------------------
app.get("/", (req, res) => {
  res.send("Hey Ladies");
});

// --------------------
// 404 handler
// --------------------
app.use((req, res) => {
  res.status(404).json({
    success: false,
    message: `Route ${req.originalUrl} not found`,
  });
});

// --------------------
// Global error handler
// --------------------
app.use((err, req, res, next) => {
  console.error("=== GLOBAL ERROR HANDLER ===");
  console.error(err);

  res.status(err.statusCode || 500).json({
    success: false,
    message: err.message || "Internal Server Error",
    ...(process.env.NODE_ENV === "development" && { stack: err.stack }),
  });
});

export { app };
