import mongoose from "mongoose";

const ResumeSchema = new mongoose.Schema(
  {
    userId: {
      type: mongoose.Schema.Types.ObjectId,
      ref: "User",
      required: true,
      unique: true,
      index: true
    },

    filename:  { type: String, default: "resume.pdf" },
    mimetype:  { type: String, default: "application/pdf" },
    size:      { type: Number, default: 0 },

    // Cloudinary permanent URL — used by frontend to open the PDF
    cloudinaryUrl:      { type: String, required: true },
    // Cloudinary public_id — kept for reference / future deletion if needed
    cloudinaryPublicId: { type: String, default: "" },

    uploadedAt: { type: Date, default: Date.now },

    // output from MCP parsing pipeline
    parsed_resume: { type: mongoose.Schema.Types.Mixed, default: {} },

    // ATS score output
    score: { type: mongoose.Schema.Types.Mixed, default: {} },
  },
  { timestamps: true }
);

export const Resume = mongoose.model("Resume", ResumeSchema);