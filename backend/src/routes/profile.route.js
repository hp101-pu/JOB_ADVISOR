import express from "express";
import {
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
} from "../controllers/profile.controller.js";
import { verifyJWT } from "../middleware/auth.middleware.js";
import { upload } from "../middleware/multer.middleware.js";

const router = express.Router();

router.get("/me",verifyJWT,getMyProfile);
router.patch( "/me",verifyJWT,updateMyProfile);
//skills
router.patch("/me/skills", verifyJWT, updateSkills);
//experience
router.post("/me/experience", verifyJWT, addExperience);
router.patch("/me/experience/:id", verifyJWT, updateExperience);
router.delete("/me/experience/:id", verifyJWT, deleteExperience);
//education
router.post("/me/education", verifyJWT, addEducation);
router.patch("/me/education/:id", verifyJWT, updateEducation);
router.delete("/me/education/:id", verifyJWT, deleteEducation);
// Avatar upload
router.post("/me/avatar", verifyJWT, upload.single("avatar"), uploadAvatar);
//change password
router.patch("/me/change-password", verifyJWT, changePassword);

export default router;
