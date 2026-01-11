import dotenv from "dotenv";
dotenv.config();

import { v2 as cloudinary } from "cloudinary";
import fs from "fs";
import streamifier from "streamifier";

// Configure cloudinary once
cloudinary.config({
  cloud_name: process.env.CLOUDINARY_CLOUD_NAME,
  api_key: process.env.CLOUDINARY_API_KEY,
  api_secret: process.env.CLOUDINARY_API_SECRET,
});

/*
-----------------------------------------
1. Upload using local file path
-----------------------------------------
*/
const uploadOnCloudinary = async (localFilePath) => {
  if (!localFilePath) return null;

  try {
    const response = await cloudinary.uploader.upload(localFilePath, {
      resource_type: "auto",
    });

    console.log("UPLOADED SUCCESSFULLY", response.secure_url);
    return response;
  } catch (error) {
    console.error("Cloudinary upload error:", error);
    throw error;
  } finally {
    // delete temp file
    try {
      await fs.unlink(localFilePath);
    } catch (err) {
      console.warn("Error deleting temp file:", err.message);
    }
  }
};

/*
-----------------------------------------
2. Upload PDF using buffer stream
-----------------------------------------
*/
const uploadPdfToCloudinary = async (buffer, publicId) => {
  return new Promise((resolve, reject) => {
    const uploadStream = cloudinary.uploader.upload_stream(
      {
        resource_type: "raw",
        public_id: publicId,
        overwrite: true,
      },
      (error, result) => {
        if (error)
          return reject(
            new Error(`Cloudinary upload failed: ${error.message}`)
          );

        resolve({
          url: result.secure_url,
          public_id: result.public_id,
        });
      }
    );

    streamifier.createReadStream(buffer).pipe(uploadStream);
  });
};

export { uploadOnCloudinary, uploadPdfToCloudinary };