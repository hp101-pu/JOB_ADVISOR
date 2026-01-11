import { Router } from "express";
import multer from "multer";

import { verifyJWT } from "../middleware/auth.middleware.js";
import {
  uploadAndParseResume,
  getMyResume,
  recalculateScore,
  deleteMyResume,
  streamMyResumeFile
} from "../controllers/resume.controller.js";

const router = Router();

const ALLOWED_MIMETYPES = new Set([
  "application/pdf",
  "application/octet-stream", // some browsers/OS send this for PDFs
]);

const upload = multer({
  storage: multer.memoryStorage(),
  limits: { fileSize: 5 * 1024 * 1024 },
  fileFilter: (req, file, cb) => {
    const ext = file.originalname?.toLowerCase().split(".").pop();
    const mimeOk = ALLOWED_MIMETYPES.has(file.mimetype);
    const extOk  = ext === "pdf";
    if (!mimeOk && !extOk) {
      return cb(new Error("Only PDF files are allowed"), false);
    }
    cb(null, true);
  },
});

// POST upload + parse
router.post("/", verifyJWT, upload.single("resume"), uploadAndParseResume);

// POST re-score stored parsed_resume with latest scorer (no re-upload)
router.post("/recalculate", verifyJWT, recalculateScore);

// GET metadata + parsed + score
router.get("/", verifyJWT, getMyResume);

// DELETE resume from MongoDB
router.delete("/", verifyJWT, deleteMyResume);

// GET pdf file
router.get("/file", verifyJWT, streamMyResumeFile);

export default router;