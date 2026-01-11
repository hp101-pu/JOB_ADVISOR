import mongoose from "mongoose";

const oauthTokenSchema = new mongoose.Schema({
  userId: {
    type: mongoose.Schema.Types.ObjectId,
    ref: "User",
    required: true,
  },
  provider: {
    type: String,
    enum: ["google"],
    required: true,
  },
  accessToken: String,
  refreshToken: String,
  expiryDate: Date,
  scopes: [String],
}, { timestamps: true });

export const OAuthToken = mongoose.model("OAuthToken", oauthTokenSchema);
