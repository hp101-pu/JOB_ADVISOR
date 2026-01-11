import { User } from "../models/user.model.js";
import { asyncHandler } from "../utils/asyncHandler.js";

const DEFAULT_PREFS = {
  interviewAlerts: true,
  rejectionAlerts: true,
  offerAlerts: true,
  assessmentAlerts: false,
  weeklyDigest: false,
};

/* GET /api/notifications/preferences */
export const getNotificationPrefs = asyncHandler(async (req, res) => {
  const user = await User.findById(req.user._id).select("notificationPrefs");
  if (!user) return res.status(404).json({ success: false, message: "User not found" });

  res.json({
    success: true,
    prefs: user.notificationPrefs ?? DEFAULT_PREFS,
  });
});

/* PATCH /api/notifications/preferences */
export const updateNotificationPrefs = asyncHandler(async (req, res) => {
  const allowed = ["interviewAlerts", "rejectionAlerts", "offerAlerts", "assessmentAlerts", "weeklyDigest"];
  const updates = {};

  for (const key of allowed) {
    if (req.body[key] !== undefined) {
      updates[`notificationPrefs.${key}`] = Boolean(req.body[key]);
    }
  }

  if (Object.keys(updates).length === 0) {
    return res.status(400).json({ success: false, message: "No valid fields provided" });
  }

  const user = await User.findByIdAndUpdate(
    req.user._id,
    { $set: updates },
    { new: true, select: "notificationPrefs" }
  );

  res.json({
    success: true,
    message: "Preferences saved",
    prefs: user.notificationPrefs,
  });
});
