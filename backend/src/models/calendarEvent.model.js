import mongoose from "mongoose";

const calendarEventSchema = new mongoose.Schema(
  {
    userId: {
      type: mongoose.Schema.Types.ObjectId,
      ref: "User",
      required: true,
      index: true,
    },

    // Which email triggered this event (null if created manually)
    emailId: {
      type: mongoose.Schema.Types.ObjectId,
      ref: "Email",
      default: null,
    },

    // Google Calendar event ID — only set if also pushed to Google Calendar
    // Optional: events can exist in our DB without being on Google Calendar
    googleEventId: {
      type: String,
      default: null,
    },

    summary: {
      type: String,
      required: true,
    },

    description: {
      type: String,
      default: "",
    },

    company: {
      type: String,
      default: "",
    },

    role: {
      type: String,
      default: "",
    },

    date: {
      type: Date,
      required: true,
    },

    startTime: {
      type: String,
      required: true,
    },

    endTime: {
      type: String,
      required: true,
    },

    timezone: {
      type: String,
      default: "Asia/Kolkata",
    },

    meetLink: {
      type: String,
      default: "",
    },

    // Direct link to the event on Google Calendar (only if pushed there)
    eventLink: {
      type: String,
      default: "",
    },

    // Source: auto-created from email, or manually added
    source: {
      type: String,
      enum: ["email", "manual"],
      default: "email",
    },

    // Soft-delete flag: user explicitly deleted this event.
    // Kept as a tombstone so it never gets recreated.
    deletedByUser: {
      type: Boolean,
      default: false,
      index: true,
    },
  },
  { timestamps: true }
);

// Prevent duplicate events per user + email — but only when emailId is set.
// Direct-created events (emailId=null) are excluded from this index so
// multiple manual events can coexist for the same user.
calendarEventSchema.index(
  { userId: 1, emailId: 1 },
  { unique: true, partialFilterExpression: { emailId: { $type: "ObjectId" } } }
);

// Fast range queries for the calendar page
calendarEventSchema.index({ userId: 1, date: 1 });

export const CalendarEvent = mongoose.model("CalendarEvent", calendarEventSchema);