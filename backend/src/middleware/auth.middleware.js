import jwt from "jsonwebtoken";
import { User } from "../models/user.model.js";
import { asyncHandler } from "../utils/asyncHandler.js";

const verifyJWT = asyncHandler(async (req, res, next) => {

  // ✅ 1. Allow CORS preflight requests
  if (req.method === "OPTIONS") {
    return next();
  }

  const token =
    req.header("Authorization")?.replace("Bearer ", "") ||
    req.cookies?.accessToken;

  console.log("JWT MIDDLEWARE HIT:", req.method, req.originalUrl);
  console.log("TOKEN STRING:", token);
  console.log("DOT COUNT:", token ? token.split(".").length : 0);

  // ✅ 2. If no token — check if it's a trusted internal service call
  if (!token) {
    const serviceKey = req.headers["x-service-key"];
    const xUserId = req.headers["x-user-id"];
    if (serviceKey && serviceKey === process.env.SERVICE_KEY && xUserId) {
      // Attach a minimal user object so controllers can use req.user._id safely
      req.user = { _id: xUserId };
      return next();
    }
    return res.status(401).json({
    success: false,
    message: "Unauthorized: no token provided",
  });
  }

  // ✅ 3. Verify token safely
  let decoded;
  try {
    decoded = jwt.verify(token, process.env.ACCESS_TOKEN_SECRET);
  } catch (err) {
    return res.status(401).json({
      success: false,
      message: "Invalid or expired token",
    });
  }

  // ✅ 4. Attach user
  const user = await User.findById(decoded._id).select(
    "-password -refreshToken"
  );

  if (!user) {
    return res.status(401).json({
      success: false,
      message: "Unauthorized: user not found",
    });
  }

  req.user = user;
  next();
});

export { verifyJWT };
