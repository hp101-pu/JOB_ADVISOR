import { asyncHandler } from "../utils/asyncHandler.js";
import { ApiError }      from "../utils/apiError.js";
import { ApiResponse }   from "../utils/apiResponse.js";

import { Resume }                   from "../models/resume.model.js";
import { resumeService }            from "../services/resume.services.js";
import { uploadPdfToCloudinary }    from "../utils/cloudinary.js";

/**
 * POST /api/resume
 * Upload resume PDF → parse via MCP pipeline → store on Cloudinary → save to MongoDB
 *
 * Order is intentional:
 *   1. pipeline first  - if it fails, nothing is uploaded to Cloudinary (no orphans)
 *   2. Cloudinary next — only reached if pipeline succeeded
 *   3. MongoDB last    — only reached if both above succeeded
 */
export const uploadAndParseResume = asyncHandler(async (req, res) => {
  const userId = req.user?._id;
  if (!userId) throw new ApiError(401, "Unauthorized: user not found");

  const file = req.file;
  if (!file) throw new ApiError(400, "Resume PDF file is required");

  const ext = file.originalname?.toLowerCase().split(".").pop();
  if (file.mimetype !== "application/pdf" && file.mimetype !== "application/octet-stream" && ext !== "pdf") {
    throw new ApiError(400, "Invalid file type. Only PDF allowed.");
  }

  // Extract JWT for the orchestrator
  const token =
    req.header("Authorization")?.replace("Bearer ", "") ||
    req.cookies?.accessToken ||
    null;

  // 1) Convert buffer → base64 and run the MCP parse+score pipeline
  const file_b64 = file.buffer.toString("base64");

  const pipelineResult = await resumeService.parseResumePdf({
    userId,
    jwt:      token,
    filename: file.originalname,
    mimetype: file.mimetype,
    file_b64,
  });

  // resumeService now throws if pipeline returned success:false,
  // so reaching here means we have a real parsed result
  const parsed_resume = pipelineResult.parsed_resume;
  const score         = pipelineResult.score;

  // 2) Upload PDF to Cloudinary (overwrite:true handles re-uploads cleanly)
  const { url: cloudinaryUrl, public_id: cloudinaryPublicId } =
    await uploadPdfToCloudinary(file.buffer, `resumes/${userId}`);

  // 3) Upsert MongoDB
  const resumeDoc = await Resume.findOneAndUpdate(
    { userId },
    {
      userId,
      filename:           file.originalname,
      mimetype:           file.mimetype,
      size:               file.size,
      cloudinaryUrl,
      cloudinaryPublicId,
      uploadedAt:         new Date(),
      parsed_resume,
      score,
    },
    { upsert: true, new: true }
  );

  return res.status(200).json(
    new ApiResponse(
      200,
      {
        resume: {
          id:          resumeDoc._id,
          filename:    resumeDoc.filename,
          mimetype:    resumeDoc.mimetype,
          size:        resumeDoc.size,
          uploadedAt:  resumeDoc.uploadedAt,
          openUrl:     resumeDoc.cloudinaryUrl,
        },
        parsed_resume,
        score,
        openUrl: resumeDoc.cloudinaryUrl,
      },
      "Resume uploaded and parsed successfully"
    )
  );
});


/**
 * GET /api/resume
 * Fetch user's resume metadata + parsed result + score from MongoDB
 */
export const getMyResume = asyncHandler(async (req, res) => {
  const userId = req.user?._id;
  if (!userId) throw new ApiError(401, "Unauthorized");

  const resumeDoc = await Resume.findOne({ userId });

  if (!resumeDoc) {
    return res.status(200).json(
      new ApiResponse(200, { hasResume: false }, "No resume found")
    );
  }

  return res.status(200).json(
    new ApiResponse(
      200,
      {
        hasResume: true,
        resume: {
          id:         resumeDoc._id,
          filename:   resumeDoc.filename,
          mimetype:   resumeDoc.mimetype,
          size:       resumeDoc.size,
          uploadedAt: resumeDoc.uploadedAt,
          openUrl:    resumeDoc.cloudinaryUrl,
        },
        parsed_resume: resumeDoc.parsed_resume || {},
        score:         resumeDoc.score         || {},
        openUrl:       resumeDoc.cloudinaryUrl,
      },
      "Resume fetched successfully"
    )
  );
});


/**
 * POST /api/resume/recalculate
 * Re-score the stored parsed_resume with the latest ATS scorer (ats_v3).
 * Does NOT re-parse the PDF or re-upload to Cloudinary.
 * Use this when the scorer changes and cached scores need refreshing.
 */
export const recalculateScore = asyncHandler(async (req, res) => {
  const userId = req.user?._id;
  if (!userId) throw new ApiError(401, "Unauthorized");

  const resumeDoc = await Resume.findOne({ userId });
  if (!resumeDoc) throw new ApiError(404, "No resume found — upload a resume first");

  const parsed_resume = resumeDoc.parsed_resume;
  if (!parsed_resume || !parsed_resume.entities) {
    throw new ApiError(400, "Stored resume has no parsed data — please re-upload");
  }

  const token =
    req.header("Authorization")?.replace("Bearer ", "") ||
    req.cookies?.accessToken ||
    null;

  const result = await resumeService.rescoreResume({
    userId,
    jwt:           token,
    parsed_resume,
  });

  const newScore = result.score;

  // Update only the score field in MongoDB — parsed_resume unchanged
  await Resume.findOneAndUpdate(
    { userId },
    { score: newScore },
    { new: true }
  );

  return res.status(200).json(
    new ApiResponse(
      200,
      {
        score:         newScore,
        parsed_resume: resumeDoc.parsed_resume,
      },
      "Score recalculated with latest ATS scorer"
    )
  );
});


/**
 * DELETE /api/resume
 * Deletes the user's resume document from MongoDB.
 * Does not delete from Cloudinary (file stays there as orphan, acceptable).
 */
export const deleteMyResume = asyncHandler(async (req, res) => {
  const userId = req.user?._id;
  if (!userId) throw new ApiError(401, "Unauthorized");

  const deleted = await Resume.findOneAndDelete({ userId });
  if (!deleted) throw new ApiError(404, "No resume found");

  return res.status(200).json(
    new ApiResponse(200, {}, "Resume deleted successfully")
  );
});


/**
 * GET /api/resume/file
 * Redirects to the Cloudinary URL — browser opens the PDF directly.
 * Kept so any existing frontend link to /api/resume/file still works.
 */
export const streamMyResumeFile = asyncHandler(async (req, res) => {
  const userId = req.user?._id;
  if (!userId) throw new ApiError(401, "Unauthorized");

  const resumeDoc = await Resume.findOne({ userId });
  if (!resumeDoc?.cloudinaryUrl) throw new ApiError(404, "Resume not found");

  return res.redirect(resumeDoc.cloudinaryUrl);
});