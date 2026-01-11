import { callMCP } from "./mcp.service.js";
import { User } from "../models/user.model.js";

class JobsService {
  async searchJobs(keywords, country = "in", where = "", maxResults = 10, page = 1, userId = null, jwt = null) {
    try {
      console.log(`🔍 Searching jobs: keywords="${keywords}", location="${where}"`);
      return await callMCP({
        endpoint: "/pipelines/job-search",
        args: { keywords, location: where, country, maxResults, page, useResumeMatching: false },
        userId,
        jwt
      });
    } catch (error) {
      console.error("❌ Job search error:", error);
      throw new Error("Failed to search jobs");
    }
  }

  async rankJobsByRelevance(jobs, userId, jwt) {
    try {
      console.log(`🔍 Ranking jobs: ${jobs.length} jobs for user: ${userId}`);
      const result = await callMCP({ endpoint: "/pipelines/rank-jobs", args: { jobs }, userId, jwt });
      if (result.success && result.jobs) return result.jobs;
      console.warn("⚠️ Ranking failed, returning unranked jobs");
      return jobs;
    } catch (error) {
      console.error("⚠️ Ranking error:", error);
      return jobs;
    }
  }

  async getJobCategories(country = "in", userId = null) {
    try {
      return await callMCP({ endpoint: "/pipelines/job-categories", args: { country }, userId });
    } catch (error) {
      console.error("❌ Get categories error:", error);
      throw new Error("Failed to fetch job categories");
    }
  }

  async getRecommendedJobs(userId, jwt) {
    try {
      console.log(`✨ Getting recommendations for user: ${userId}`);
      return await callMCP({ endpoint: "/pipelines/job-recommendations", args: { maxResults: 20 }, userId, jwt });
    } catch (error) {
      console.error("❌ Recommendation error:", error);
      throw new Error("Failed to get job recommendations");
    }
  }

  async matchJobsToResume(userId, jobs) {
    try {
      const user = await User.findById(userId);
      if (!user?.resume?.skills?.length) throw new Error("Resume skills not found");
      const requiredSkills = user.resume.skills.slice(0, 3);
      const preferredSkills = user.resume.skills.slice(3, 8);
      return await callMCP({ tool: "filter_jobs_by_skills", args: { jobs, required_skills: requiredSkills, preferred_skills: preferredSkills }, userId });
    } catch (error) {
      console.error("❌ Job matching error:", error);
      throw new Error("Failed to match jobs");
    }
  }

  async saveJob(userId, job) {
    try {
      const user = await User.findById(userId);
      if (!user) throw new Error("User not found");

      user.savedJobs ??= [];

      const alreadySaved = user.savedJobs.some((saved) => saved.id === job.id);
      if (alreadySaved) return { success: false, message: "Job already saved" };

      user.savedJobs.push({
        id: job.id,
        title: job.title,
        company: job.company,
        location: job.location,
        url: job.apply_url || job.url,
        description: job.description,
        salary_min: job.salary_min,
        salary_max: job.salary_max,
        contract_type: job.contract_type,
        contract_time: job.contract_time,
        category: job.category,
        created: job.created,
        source: job.source,
        matchScore: job.match_score || job.matchScore,
        matchReason: job.match_reason || job.matchReason,
        matchedSkills: job.matched_skills || job.matchedSkills || [],
        savedAt: new Date(),
      });

      await user.save();
      console.log(`💾 Job saved: ${job.id} for user ${userId}`);
      return { success: true, message: "Job saved successfully" };
    } catch (error) {
      console.error("❌ Save job error:", error);
      throw new Error("Failed to save job");
    }
  }

  async getSavedJobs(userId) {
    const user = await User.findById(userId);
    if (!user) throw new Error("User not found");

    console.log(`📋 Fetching saved jobs for user: ${userId}`);

    // Remap stored field names back to the shape JobDetails/JobCard expects
    const jobs = (user.savedJobs || []).map((j) => ({
      id: j.id,
      title: j.title,
      company: j.company,
      location: j.location,
      apply_url: j.url,
      description: j.description,
      salary_min: j.salary_min,
      salary_max: j.salary_max,
      contract_type: j.contract_type,
      contract_time: j.contract_time,
      category: j.category,
      created: j.created,
      source: j.source,
      match_score: j.matchScore,
      match_reason: j.matchReason,
      matched_skills: j.matchedSkills || [],
      savedAt: j.savedAt,
    }));

    return { success: true, jobs };
  }

  async unsaveJob(userId, jobId) {
    const user = await User.findById(userId);
    if (!user) throw new Error("User not found");

    user.savedJobs = (user.savedJobs || []).filter((job) => job.id !== jobId);
    await user.save();

    console.log(`🗑️ Job unsaved: ${jobId} for user ${userId}`);
    return { success: true, message: "Job removed from saved list" };
  }
}

export const jobsService = new JobsService();
