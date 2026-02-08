import { User } from "../models/user.model.js";

/**
 * Map parsed resume data into the User schema shape.
 *
 * Resume source fields:
 *   - skills:     parsed_resume.entities.skills
 *   - headline:   parsed_resume.entities.normalized_roles[0] or latest experience role
 *   - experience: parsed_resume.structured.experience[].role, company, date, details
 *   - education:  parsed_resume.structured.education[].degree, institution, date
 */

const _isEmptyArray = (val) => !Array.isArray(val) || val.length === 0;
const _isEmptyString = (val) => !val || !String(val).trim();

function _parseDateRange(dateStr) {
  if (!dateStr) return { startDate: null, endDate: null, isCurrent: false };

  const text = String(dateStr).toLowerCase();
  const isCurrent = /present|current|now|ongoing/.test(text);

  // Try to find start year (first 4-digit year)
  const years = text.match(/\d{4}/g) || [];
  const startYear = years[0] ? Number(years[0]) : null;
  const endYear = isCurrent ? null : (years[1] ? Number(years[1]) : null);

  return {
    startDate: startYear ? new Date(`${startYear}-01-01`) : null,
    endDate: endYear ? new Date(`${endYear}-01-01`) : null,
    isCurrent,
  };
}

function _extractYearFromDate(dateStr) {
  if (!dateStr) return null;
  const years = String(dateStr).match(/\d{4}/g);
  return years ? Number(years[years.length - 1]) : null;
}

function _extractFieldOfStudy(degree) {
  if (!degree) return null;
  const match = String(degree).match(/in\s+(.+)$/i);
  return match ? match[1].trim() : null;
}

function _deriveHeadline(parsedResume) {
  const entities = parsedResume?.entities || {};
  const structured = parsedResume?.structured || {};
  const experience = structured.experience || [];

  // Prefer the latest experience role
  const latestRole = experience[experience.length - 1]?.role || experience[0]?.role;
  if (latestRole) return latestRole.trim();

  // Fallback to first normalized role
  const normalizedRoles = entities.normalized_roles || [];
  if (normalizedRoles.length > 0) return normalizedRoles[0].trim();

  // Fallback to first raw role
  const roles = entities.roles || [];
  if (roles.length > 0) return roles[0].trim();

  return null;
}

function _mapExperience(experienceItems) {
  if (!Array.isArray(experienceItems)) return [];

  return experienceItems
    .filter((item) => item.role && item.company)
    .map((item) => {
      const { startDate, endDate, isCurrent } = _parseDateRange(item.date);
      return {
        title:       String(item.role).trim(),
        company:     String(item.company).trim(),
        startDate,
        endDate,
        isCurrent,
        description: Array.isArray(item.details)
          ? item.details.join("\n").trim()
          : String(item.details || "").trim(),
      };
    });
}

function _mapEducation(educationItems) {
  if (!Array.isArray(educationItems)) return [];

  return educationItems
    .filter((item) => item.degree || item.institution)
    .map((item) => ({
      degree:       String(item.degree || "").trim(),
      fieldOfStudy: _extractFieldOfStudy(item.degree),
      institution:  String(item.institution || "").trim(),
      year:         _extractYearFromDate(item.date),
    }));
}

function _shouldUpdateField(current, overwrite) {
  if (overwrite) return true;
  if (current === null || current === undefined) return true;
  if (Array.isArray(current)) return current.length === 0;
  if (typeof current === "string") return current.trim().length === 0;
  return false;
}

/**
 * Synchronize a user profile from parsed resume data.
 *
 * @param {string} userId - MongoDB user id
 * @param {object} parsed_resume - The parsed resume object
 * @param {boolean} overwrite - If true, replace existing values; if false, only fill empty fields
 * @returns {Promise<object>} Updated user profile (sans password/refreshToken)
 */
export async function syncProfileFromResume({ userId, parsed_resume, overwrite = false }) {
  if (!userId) throw new Error("userId is required");
  if (!parsed_resume) throw new Error("parsed_resume is required");

  const user = await User.findById(userId);
  if (!user) throw new Error("User not found");

  const entities = parsed_resume.entities || {};
  const structured = parsed_resume.structured || {};

  const updates = {};

  // Skills
  const resumeSkills = entities.skills || [];
  if (resumeSkills.length > 0 && _shouldUpdateField(user.skills, overwrite)) {
    updates.skills = resumeSkills;
  }

  // Headline
  const resumeHeadline = _deriveHeadline(parsed_resume);
  if (resumeHeadline && _shouldUpdateField(user.headline, overwrite)) {
    updates.headline = resumeHeadline;
  }

  // Experience
  const resumeExperience = _mapExperience(structured.experience || []);
  if (resumeExperience.length > 0 && _shouldUpdateField(user.experience, overwrite)) {
    updates.experience = resumeExperience;
  }

  // Education
  const resumeEducation = _mapEducation(structured.education || []);
  if (resumeEducation.length > 0 && _shouldUpdateField(user.education, overwrite)) {
    updates.education = resumeEducation;
  }

  // About / summary (from sections.summary if present)
  const summary = parsed_resume.sections?.summary;
  if (summary && _shouldUpdateField(user.about, overwrite)) {
    updates.about = String(summary).trim();
  }

  // Mark profile as complete if we have meaningful data
  const hasSkills = (updates.skills || user.skills || []).length > 0;
  const hasHeadline = (updates.headline || user.headline || "").trim().length > 0;
  const hasExperience = (updates.experience || user.experience || []).length > 0;
  const hasEducation = (updates.education || user.education || []).length > 0;
  if (hasSkills && (hasHeadline || hasExperience || hasEducation)) {
    updates.isProfileComplete = true;
  }

  if (Object.keys(updates).length === 0) {
    return user;
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

  return updatedUser;
}
