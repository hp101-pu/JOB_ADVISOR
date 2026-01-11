import { User } from "../models/user.model.js";
import { asyncHandler } from "../utils/asyncHandler.js";

/* ============================= */
/* GET MY PROFILE                */
/* ============================= */

const getMyProfile = asyncHandler(async (req, res) => {
  const userId = req.user?._id;

  if (!userId) {
    return res.status(401).json({
      success: false,
      message: "Unauthorized",
    });
  }

  const user = await User.findById(userId).select(
    "-password -refreshToken"
  );

  if (!user) {
    return res.status(404).json({
      success: false,
      message: "User not found",
    });
  }

  return res.status(200).json({
    success: true,
    profile: user,
  });
});

/* ============================= */
/* UPDATE MY PROFILE (PATCH)     */
/* ============================= */

const updateMyProfile = asyncHandler(async (req, res) => {
  const userId = req.user?._id;

  if (!userId) {
    return res.status(401).json({
      success: false,
      message: "Unauthorized",
    });
  }

  /**
   * Allow ONLY these fields to be updated
   * Anything else is ignored (security)
   */
  const allowedUpdates = [
    "fullname",
    "about",
    "phone",
    "openToWork",
    "avatar",
    "location",
    "socials",
    "headline",
  ];

  const updates = {};

  for (const key of allowedUpdates) {
    if (req.body[key] !== undefined) {
      updates[key] = req.body[key];
    }
  }

  if (Object.keys(updates).length === 0) {
    return res.status(400).json({
      success: false,
      message: "No valid fields provided for update",
    });
  }

  const updatedUser = await User.findByIdAndUpdate(
    userId,
    { $set: updates },
    {
      new: true,
      runValidators: true,
      select: "-password -refreshToken",
    }
  );

  return res.status(200).json({
    success: true,
    message: "Profile updated successfully",
    profile: updatedUser,
  });
});

//skills
const updateSkills = asyncHandler(async (req, res) => {
  const { skills } = req.body;

  if (!Array.isArray(skills)) {
    return res.status(400).json({
      success: false,
      message: "Skills must be an array",
    });
  }

  const user = await User.findByIdAndUpdate(
    req.user._id,
    { skills },
    { new: true }
  ).select("-password -refreshToken");

  res.json({
    success: true,
    skills: user.skills,
  });
});

//experience
// ADD
const addExperience = asyncHandler(async (req, res) => {
  const user = await User.findById(req.user._id);

  user.experience.push(req.body);
  await user.save();

  res.json({
    success: true,
    experience: user.experience,
  });
});

// UPDATE
const updateExperience = asyncHandler(async (req, res) => {
  const user = await User.findById(req.user._id);

  const exp = user.experience.id(req.params.id);
  if (!exp) {
    return res.status(404).json({
      success: false,
      message: "Experience not found",
    });
  }

  Object.assign(exp, req.body);
  await user.save();

  res.json({
    success: true,
    experience: user.experience,
  });
});

// DELETE
const deleteExperience = asyncHandler(async (req, res) => {
  const user = await User.findById(req.user._id);

  const exp = user.experience.id(req.params.id);
  if (!exp) {
    return res.status(404).json({
      success: false,
      message: "Experience not found",
    });
  }

  user.experience.pull(req.params.id);
  await user.save();

  res.json({
    success: true,
    experience: user.experience,
  });
});


//education
// ADD
const addEducation = asyncHandler(async (req, res) => {
  const user = await User.findById(req.user._id);

  user.education.push(req.body);
  await user.save();

  res.json({
    success: true,
    education: user.education,
  });
});

// UPDATE
const updateEducation = asyncHandler(async (req, res) => {
  const user = await User.findById(req.user._id);

  const edu = user.education.id(req.params.id);
  if (!edu) {
    return res.status(404).json({
      success: false,
      message: "Education not found",
    });
  }

  Object.assign(edu, req.body);
  await user.save();

  res.json({
    success: true,
    education: user.education,
  });
});

// DELETE
const deleteEducation = asyncHandler(async (req, res) => {
  const user = await User.findById(req.user._id);

  const edu = user.education.id(req.params.id);
  if (!edu) {
    return res.status(404).json({
      success: false,
      message: "Education not found",
    });
  }

 user.education.pull(req.params.id);

  await user.save();

  res.json({
    success: true,
    education: user.education,
  });
});

//change password

const changePassword = asyncHandler(async (req, res) => {
  const userId = req.user?._id;
  const { currentPassword, newPassword } = req.body;

  // Validation
  if (!currentPassword || !newPassword) {
    return res.status(400).json({
      success: false,
      message: "Both current and new password are required",
    });
  }

  if (newPassword.length < 6) {
    return res.status(400).json({
      success: false,
      message: "New password must be at least 6 characters long",
    });
  }

  if (currentPassword === newPassword) {
    return res.status(400).json({
      success: false,
      message: "New password must be different from current password",
    });
  }

  // Find user with password field
  const user = await User.findById(userId).select("+password");

  if (!user) {
    return res.status(404).json({
      success: false,
      message: "User not found",
    });
  }

  // Check if user registered with Google (no password)
  if (user.provider === "google" && !user.password) {
    return res.status(400).json({
      success: false,
      message: "Cannot change password for Google-authenticated accounts. Please use Google to manage your password.",
    });
  }

  // Verify current password
  const isPasswordValid = await user.isPasswordCorrect(currentPassword);

  if (!isPasswordValid) {
    return res.status(401).json({
      success: false,
      message: "Current password is incorrect",
    });
  }

  // Update password (will be hashed by pre-save hook)
  user.password = newPassword;
  await user.save();

  return res.status(200).json({
    success: true,
    message: "Password changed successfully",
  });
});

// Upload avatar
const uploadAvatar = asyncHandler(async (req, res) => {
  if (!req.file) {
    return res.status(400).json({ success: false, message: "No file uploaded" });
  }

  const avatarUrl = `/uploads/avatars/${req.file.filename}`;

  const user = await User.findByIdAndUpdate(
    req.user._id,
    { avatar: avatarUrl },
    { new: true, select: "-password -refreshToken" }
  );

  return res.status(200).json({
    success: true,
    avatarUrl: user.avatar,
  });
});

export {
  getMyProfile,
  updateMyProfile,
  uploadAvatar,
  updateSkills,
  addExperience,
  updateExperience,
  deleteExperience,
  addEducation,
  updateEducation,
  deleteEducation,
  changePassword,
};
