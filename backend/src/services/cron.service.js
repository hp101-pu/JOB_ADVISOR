import cron from "node-cron";
import pLimit from "p-limit";
import { User } from "../models/user.model.js";
import { Email } from "../models/email.model.js";
import { emailService } from "./email.service.js";
import { sseService } from "./sse.service.js";
import { calendarService } from "./calendar.service.js";

const INITIAL_LOOKBACK_DAYS = 7;
const INITIAL_MAX_RESULTS = 50;
const INCREMENTAL_LOOKBACK_DAYS = 1;
const INCREMENTAL_MAX_RESULTS = 10;

class CronService {
  constructor() {
    this.jobs = new Map();
    this.isEmailSyncRunning = false;
    this.limit = pLimit(25); 
  }

  startEmailSyncJob() {
    if (this.jobs.has("emailSync")) {
      console.log("⚠️ Email sync cron already running");
      return;
    }

    const job = cron.schedule(
      "*/2 * * * *",
      async () => {
        if (this.isEmailSyncRunning) {
          console.log("⏭️ [CRON] Email sync already running, skipping");
          return;
        }

        this.isEmailSyncRunning = true;
        console.log("🔄 [CRON] Email sync job started");

        try {
          const users = await User.find({
            isActive: true,
            isGmailConnected: true,
          }).select("_id email initialSyncDone");

          console.log(`📧 [CRON] Users to sync: ${users.length}`);

          await Promise.all(
            users.map((user) =>
              this.limit(async () => {
                try {
                  const isInitial = !user.initialSyncDone;
                  const lookback_days = isInitial ? INITIAL_LOOKBACK_DAYS : INCREMENTAL_LOOKBACK_DAYS;
                  const max_results  = isInitial ? INITIAL_MAX_RESULTS   : INCREMENTAL_MAX_RESULTS;

                  await emailService.syncEmailsInternal({
                    userId: user._id,
                    lookback_days,
                    max_results,
                  });

                  // After first successful sync, mark initial sync as done
                  if (isInitial) {
                    await User.findByIdAndUpdate(user._id, { initialSyncDone: true });
                    console.log(`🎉 [CRON] Initial sync complete for: ${user.email}`);
                  } else {
                    console.log(`✅ [CRON] Synced: ${user.email}`);
                  }

                  // Push SSE event to browser if user tab is open
                  sseService.emit(user._id, "email-synced", { ts: Date.now() });

                  // ── Step 2: auto-schedule calendar events ──────────────
                  // Find INTERVIEW emails that haven't been turned into
                  // calendar events yet and haven't been deleted by the user.
                  const pendingInterviews = await Email.find({
                    userId:                user._id,
                    type:                  "INTERVIEW",
                    calendarEventCreated:  false,
                    calendarEventDeleted:  { $ne: true },
                  }).select("_id").lean();

                  if (pendingInterviews.length > 0) {
                    console.log(`📅 [CRON] ${pendingInterviews.length} interview email(s) to schedule for: ${user.email}`);

                    for (const interview of pendingInterviews) {
                      try {
                        await calendarService.createCalendarEventFromEmail(
                          user._id,
                          interview._id
                        );
                        console.log(`✅ [CRON] Calendar event created for email: ${interview._id}`);
                      } catch (calErr) {
                        // Non-fatal — log and move on to next email
                        console.warn(`⚠️ [CRON] Calendar event failed for email ${interview._id}: ${calErr.message}`);
                      }
                    }
                  }
                  // ───────────────────────────────────────────────────────
                } catch (err) {
                  const isRevoked =
                    err.message?.includes("invalid_grant") ||
                    err.message?.includes("Token has been expired or revoked") ||
                    err.message?.includes("Gmail token expired or revoked") ||
                    err.message?.includes("User must re-authorise Gmail");

                  if (isRevoked) {
                    // Permanently revoked — stop hammering every 2 minutes
                    await User.findByIdAndUpdate(user._id, { isGmailConnected: false });
                    console.warn(`🔌 [CRON] Gmail token revoked for ${user.email} — marked as disconnected. User must re-authenticate.`);
                  } else {
                    console.error(`❌ [CRON] Failed for ${user.email}:`, err.message);
                  }
                }
              })
            )
          );

          console.log("✅ [CRON] Email sync job completed");
        } catch (error) {
          console.error(
            "❌ [CRON] Email sync job crashed:",
            error.message
          );
        } finally {
          this.isEmailSyncRunning = false;
        }
      },
      {
        timezone: "Asia/Kolkata",
      }
    );

    this.jobs.set("emailSync", job);
    console.log("✅ Email sync cron scheduled (every 15 minutes)");
    return job;
  }

  /**
   * Start email sync with custom cron expression
   */
  startCustomEmailSyncJob(schedule) {
    if (this.jobs.has("customEmailSync")) {
      console.log("⚠️ Custom email sync cron already running");
      return;
    }

    const job = cron.schedule(
      schedule,
      async () => {
        console.log(`🔄 [CRON] Custom email sync started (${schedule})`);

        try {
          const users = await User.find({
            isActive: true,
            isGmailConnected: true,
          }).select("_id email");

          await Promise.all(
            users.map((user) =>
              this.limit(async () => {
                try {
                  await emailService.syncEmailsInternal({
                    userId: user._id,
                  });

                  console.log(`✅ Synced: ${user.email}`);
                } catch (err) {
                  console.error(
                    `❌ Failed ${user.email}:`,
                    err.message
                  );
                }
              })
            )
          );

          console.log("✅ [CRON] Custom email sync completed");
        } catch (error) {
          console.error(
            "❌ [CRON] Custom email sync failed:",
            error.message
          );
        }
      },
      {
        timezone: "Asia/Kolkata",
      }
    );

    this.jobs.set("customEmailSync", job);
    console.log(`✅ Custom cron scheduled (${schedule})`);
    return job;
  }

  /**
   * Stop a specific cron job
   */
  stopJob(jobName) {
    const job = this.jobs.get(jobName);
    if (!job) return false;

    job.stop();
    this.jobs.delete(jobName);
    console.log(`🛑 Stopped cron job: ${jobName}`);
    return true;
  }

  /**
   * Stop all cron jobs
   */
  stopAllJobs() {
    this.jobs.forEach((job, name) => {
      job.stop();
      console.log(`🛑 Stopped cron job: ${name}`);
    });
    this.jobs.clear();
  }

  /**
   * Get status of running cron jobs
   */
  getJobsStatus() {
    return Array.from(this.jobs.keys()).map((name) => ({
      name,
      running: true,
    }));
  }
}

export const cronService = new CronService();