import express from "express";
import { serviceAuth } from "../middleware/service_auth.js";
import { OAuthToken } from "../models/oauth_token.model.js";

const router = express.Router();

import { google } from "googleapis";

router.post("/gmail/token", serviceAuth, async (req, res) => {
  try {
    const { userId } = req.body;

    if (!userId) {
      return res.status(400).json({ error: "userId is required" });
    }

    console.log(`🔍 Fetching Gmail token for user: ${userId}`);

    const tokenDoc = await OAuthToken.findOne({
      userId,
      provider: "google"
    });

    if (!tokenDoc) {
      console.log(`❌ No Gmail token found for user: ${userId}`);
      return res.status(404).json({ 
        error: "Gmail not connected",
        message: "User needs to connect Gmail first"
      });
    }

    console.log(`✅ Token found for user: ${userId}`);

    const oauth2Client = new google.auth.OAuth2(
      process.env.GOOGLE_SYNC_ID,
      process.env.GOOGLE_SYNC_SECRET,
      process.env.GOOGLE_SYNC_URI
    );

    oauth2Client.setCredentials({
      access_token: tokenDoc.accessToken,
      refresh_token: tokenDoc.refreshToken,
      expiry_date: tokenDoc.expiryDate,
    });

    // 🔁 Refresh if expired
    if (tokenDoc.expiryDate && tokenDoc.expiryDate < Date.now()) {
      console.log(`🔄 Token expired, refreshing...`);
      
      try {
        const { credentials } = await oauth2Client.refreshAccessToken();

        tokenDoc.accessToken = credentials.access_token;
        tokenDoc.expiryDate = credentials.expiry_date;
        await tokenDoc.save();

        console.log(`✅ Token refreshed successfully`);
      } catch (refreshError) {
        console.error(`❌ Token refresh failed:`, refreshError);
        return res.status(401).json({ 
          error: "Token refresh failed",
          message: "User needs to re-authenticate with Gmail"
        });
      }
    }

    res.json({
      accessToken: tokenDoc.accessToken
    });

  } catch (error) {
    console.error("❌ Error in /internal/google/gmail/token:", error);
    return res.status(500).json({ 
      error: "Failed to get Gmail token",
      details: error.message 
    });
  }
});

export default router;
