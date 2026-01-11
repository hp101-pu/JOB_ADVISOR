import { jobsService } from "../services/jobs.service.js";
import { asyncHandler } from "../utils/asyncHandler.js";
import { ApiError } from "../utils/apiError.js";
import { ApiResponse } from "../utils/apiResponse.js";

export const searchJobs = asyncHandler(async (req, res) => {
  const {
    keywords,
    location = "",
    country = "in",
    maxResults = 10,
    page = 1,
  } = req.query;

  if (!keywords) {
    throw new ApiError(400, "Keywords are required");
  }
 
 
  // Extract JWT from request
  const token = req.header("Authorization")?.replace("Bearer ", "") || req.cookies?.accessToken;
 
  const result = await jobsService.searchJobs(
    keywords,
    country,
    location, // mapped internally to MCP "where"
    Number(maxResults),
    Number(page),
    req.user?._id,  // userId (might be undefined for public routes)
    token  
  );

  return res
    .status(200)
    .json(new ApiResponse(200, result, "Jobs retrieved successfully"));
});

export const getRecommendedJobs = asyncHandler(async (req, res) => {
  const userId = req.user._id;
  const token =
    req.header("Authorization")?.replace("Bearer ", "") ||
    req.cookies?.accessToken;

  const result = await jobsService.getRecommendedJobs(userId, token);

  return res
    .status(200)
    .json(new ApiResponse(200, result, "Recommended jobs retrieved"));
});

export const getJobCategories = asyncHandler(async (req, res) => {
  const { country = "in" } = req.query;

  const result = await jobsService.getJobCategories(country);

  return res
    .status(200)
    .json(new ApiResponse(200, result, "Job categories retrieved"));
});

export const matchJobToResume = asyncHandler(async (req, res) => {
  const userId = req.user._id;
  const { jobs } = req.body;

  if (!Array.isArray(jobs) || jobs.length === 0) {
    throw new ApiError(400, "Jobs array is required");
  }

  const result = await jobsService.matchJobsToResume(userId, jobs);

  return res
    .status(200)
    .json(new ApiResponse(200, result, "Jobs matched successfully"));
});

export const saveJob = asyncHandler(async (req, res) => {
  const userId = req.user._id;
  const job = req.body;

  if (!job?.id) {
    throw new ApiError(400, "Job data with valid id is required");
  }

  const result = await jobsService.saveJob(userId, job);

  return res
    .status(200)
    .json(new ApiResponse(200, result, result.message));
});

export const getSavedJobs = asyncHandler(async (req, res) => {
  const userId = req.user._id;

  const result = await jobsService.getSavedJobs(userId);

  return res
    .status(200)
    .json(new ApiResponse(200, result, "Saved jobs retrieved"));
});

export const unsaveJob = asyncHandler(async (req, res) => {
  const userId = req.user._id;
  const { jobId } = req.params;

  if (!jobId) {
    throw new ApiError(400, "Job ID is required");
  }

  const result = await jobsService.unsaveJob(userId, jobId);

  return res
    .status(200)
    .json(new ApiResponse(200, result, result.message));
});

//rank job for relevence
export const rankJobs = asyncHandler(async (req, res) => {
  const userId = req.user._id;
  const { jobs } = req.body;

  if (!Array.isArray(jobs) || jobs.length === 0) {
    return res
      .status(200)
      .json(new ApiResponse(200, { jobs: [] }, "No jobs to rank"));
  }

  const token =
    req.header("Authorization")?.replace("Bearer ", "") ||
    req.cookies?.accessToken;

  const rankedJobs = await jobsService.rankJobsByRelevance(
    jobs,
    userId,
    token
  );

  return res
    .status(200)
    .json(new ApiResponse(200, { jobs: rankedJobs }, "Jobs ranked successfully"));
});