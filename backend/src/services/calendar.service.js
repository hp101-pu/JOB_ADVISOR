/**
 * Calendar Service
 * ----------------
 * Flow:
 *  1. Read INTERVIEW email from MongoDB
 *  2. Groq LLM extracts date, time, company, meetLink from email body
 *  3. Save event to MongoDB CalendarEvent collection (app calendar)
 *  4. ALSO push event to user's real Google Calendar (notifications on phone/Google)
 *     - Only if user has connected Google Calendar
 *     - Non-fatal if Google Calendar push fails — DB event still saved
 *  5. Mark email as calendarEventCreated: true
 */

import Groq from "groq-sdk";
import { Email } from "../models/email.model.js";
import { CalendarEvent } from "../models/calendarEvent.model.js";
import { googleCalendarService } from "./googleCalendar.service.js";
import { User } from "../models/user.model.js";
import { ApiError } from "../utils/apiError.js";

// Groq client — lazy initialized so dotenv has time to load
let _groq = null;
function getGroq() {
  if (!_groq) {
    if (!process.env.GROQ_API_KEY) {
      throw new Error("GROQ_API_KEY is not set in backend/.env");
    }
    _groq = new Groq({ apiKey: process.env.GROQ_API_KEY });
  }
  return _groq;
}

/**
 * Extract the first JSON object from a string, stripping markdown fences.
 */
function extractJsonObject(text) {
  let cleaned = text.trim();
  if (cleaned.startsWith("```")) {
    cleaned = cleaned.replace(/```json|```/g, "").trim();
  }
  const match = cleaned.match(/\{[\s\S]*\}/);
  return match ? match[0] : cleaned;
}

class CalendarService {

  /**
   * Extract interview details from email text using Groq LLM.
   * Returns structured data or null if no date/time found.
   */
  async extractDetailsFromEmail(subject, text) {
    const prompt = `
You are an AI assistant that extracts calendar event details from interview invitation emails.

Extract the following from the email:
1. Company name
2. Job role/position
3. Interview date (format: YYYY-MM-DD)
4. Interview start time (format: HH:MM in 24-hour)
5. Interview end time (format: HH:MM in 24-hour, estimate 1 hour if not specified)
6. Meeting link (Google Meet, Zoom, Teams, etc.)
7. Timezone (default "Asia/Kolkata" if not specified)
8. Brief description

Return STRICT JSON only (no markdown, no explanation):
{
  "company": "Company Name",
  "role": "Job Title",
  "date": "YYYY-MM-DD",
  "startTime": "HH:MM",
  "endTime": "HH:MM",
  "meetLink": "https://...",
  "timezone": "Asia/Kolkata",
  "description": "Brief summary"
}

Defaults if not found:
- role: "Interview"
- endTime: 1 hour after startTime
- timezone: "Asia/Kolkata"
- description: use the subject line
- meetLink: "" (empty string)

If NO date or time is present in the email, return exactly: null

Email Subject: ${subject}
Email Body: ${text}
`.trim();

    // Retry up to 3 times on rate limit (429)
    for (let attempt = 1; attempt <= 3; attempt++) {
      try {
        const response = await getGroq().chat.completions.create({
          model: "llama-3.1-8b-instant",
          messages: [{ role: "user", content: prompt }],
          temperature: 0,
          max_tokens: 400,
        });

        const raw = response.choices[0].message.content.trim();
        console.log(`🤖 [CalendarService] LLM raw: ${raw}`);

        if (raw === "null" || raw.toLowerCase() === "null") {
          return null;
        }

        const cleaned = extractJsonObject(raw);

        let result;
        try {
          result = JSON.parse(cleaned);
        } catch (parseErr) {
          console.error(`❌ [CalendarService] JSON parse failed: ${parseErr.message}; raw='${raw}'; cleaned='${cleaned}'`);
          return null;
        }

        if (!result.date || !result.startTime || !result.endTime || !result.company) {
          console.log("⚠️ [CalendarService] Missing required fields — skipping");
          return null;
        }

        return result;

      } catch (err) {
        const is429 = err.message?.includes("429") || err.status === 429;

        if (is429 && attempt < 3) {
          const waitMs = attempt * 5000; // 5s, 10s
          console.warn(`⏳ [CalendarService] Rate limited — waiting ${waitMs/1000}s before retry ${attempt + 1}/3`);
          await new Promise(r => setTimeout(r, waitMs));
          continue;
        }

        console.error("❌ [CalendarService] LLM extraction failed:", err.message);
        return null;
      }
    }

    return null;
  }

  /**
   * Shared method: save event to MongoDB first, then try Google Calendar (non-fatal).
   *
   * @param {String} userId
   * @param {Object} eventData - { summary, description, company, role, date, startTime, endTime, timezone, meetLink, emailId?, source }
   * @returns {Object} { eventDoc, googleSynced, googleEventLink }
   */
  async _saveEventToDBAndGoogle(userId, eventData) {
    const {
      summary,
      description = '',
      company = '',
      role = '',
      date,
      startTime,
      endTime,
      timezone = 'Asia/Kolkata',
      meetLink = '',
      emailId = null,
      source = 'email',
    } = eventData;

    // 1. Save to MongoDB CalendarEvent collection first
    //    This always succeeds regardless of Google Calendar status
    const filter = emailId
      ? { userId, emailId }
      : { userId, date: new Date(`${date}T${startTime}`), company };

    const eventDoc = await CalendarEvent.findOneAndUpdate(
      filter,
      {
        userId,
        emailId:       emailId || null,
        googleEventId: null,
        summary,
        description,
        company,
        role,
        date:          new Date(`${date}T${startTime}`),
        startTime,
        endTime,
        timezone,
        meetLink,
        eventLink:     '',
        source,
        deletedByUser: false,
      },
      { upsert: true, new: true }
    );

    console.log(`💾 [CalendarService] Saved to MongoDB: ${eventDoc._id}`);

    // 2. Push to user's Google Calendar if connected (non-fatal)
    let googleSynced = false;
    let googleEventLink = '';

    const user = await User.findById(userId).select('googleCalendarTokens');

    if (user?.googleCalendarTokens?.access_token) {
      try {
        const googleEvent = await googleCalendarService.createEvent(userId, eventData);

        await CalendarEvent.findByIdAndUpdate(eventDoc._id, {
          googleEventId: googleEvent.id,
          eventLink:     googleEvent.htmlLink || '',
        });

        googleSynced = true;
        googleEventLink = googleEvent.htmlLink || '';
        console.log(`📅 [CalendarService] Also pushed to Google Calendar: ${googleEventLink}`);
      } catch (googleErr) {
        console.warn(`⚠️ [CalendarService] Google Calendar push failed (non-fatal): ${googleErr.message}`);
        console.warn(`   Event is saved in app DB and will still show in the app calendar.`);
      }
    } else {
      console.log(`ℹ️ [CalendarService] Google Calendar not connected for user ${userId} — saved to app only`);
    }

    return { eventDoc, googleSynced, googleEventLink };
  }

  /**
   * Main method called by the cron job.
   *
   * Steps:
   *  1. Fetch INTERVIEW email from MongoDB
   *  2. Groq LLM extracts date/time/company
   *  3. Save to MongoDB CalendarEvent + push to Google Calendar (via shared method)
   *  4. Mark email as calendarEventCreated: true
   */
  async createCalendarEventFromEmail(userId, emailId) {
    console.log(`📅 [CalendarService] Processing email: ${emailId}`);

    // 1. Fetch email from MongoDB
    const email = await Email.findOne({ _id: emailId, userId });

    if (!email) throw new ApiError(404, "Email not found");

    if (email.calendarEventCreated) {
      return { success: true, message: "Already processed" };
    }

    if (email.type !== "INTERVIEW") {
      throw new ApiError(400, `Email type is ${email.type}, not INTERVIEW`);
    }

    if (!email.subject || !email.text) {
      throw new ApiError(400, "Email has no subject or body");
    }

    // 2. Groq LLM extracts event details from email body
    const details = await this.extractDetailsFromEmail(email.subject, email.text);

    if (!details) {
      await Email.findByIdAndUpdate(emailId, { calendarEventCreated: true });
      throw new ApiError(422, "No date/time found in email");
    }

    const eventData = {
      summary:     `${details.company} Interview`,
      description: details.description || email.subject,
      company:     details.company,
      role:        details.role     || "Interview",
      date:        details.date,
      startTime:   details.startTime,
      endTime:     details.endTime,
      timezone:    details.timezone || "Asia/Kolkata",
      meetLink:    details.meetLink || "",
      emailId:     email._id,
      source:      "email",
    };

    // 3. Save to MongoDB + try Google Calendar (shared method)
    const { eventDoc, googleSynced, googleEventLink } = await this._saveEventToDBAndGoogle(userId, eventData);

    // 4. Mark email as processed so cron never touches it again
    await Email.findByIdAndUpdate(emailId, { calendarEventCreated: true });

    return {
      success:       true,
      eventId:       eventDoc._id,
      company:       details.company,
      date:          details.date,
      time:          details.startTime,
      googleSynced,
      googleEventLink,
    };
  }

  /**
   * Create a calendar event directly from structured data (not from email).
   * Used by the chatbot's calendar_create_event pipeline.
   *
   * Steps:
   *  1. Save to MongoDB CalendarEvent + push to Google Calendar (via shared method)
   *  2. Return result with googleSynced flag
   */
  async createCalendarEventDirect(userId, eventData) {
    console.log(`📅 [CalendarService] Direct create for user ${userId}: ${eventData.company} on ${eventData.date}`);

    const { eventDoc, googleSynced, googleEventLink } = await this._saveEventToDBAndGoogle(userId, {
      ...eventData,
      source: 'manual',
    });

    return {
      success:       true,
      eventId:       eventDoc._id,
      summary:       eventDoc.summary,
      date:          eventData.date,
      startTime:     eventData.startTime,
      endTime:       eventData.endTime,
      company:       eventData.company || '',
      googleSynced,
      googleEventLink,
    };
  }
}

export const calendarService = new CalendarService();