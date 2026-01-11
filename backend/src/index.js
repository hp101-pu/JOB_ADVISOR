import dotenv from "dotenv";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
dotenv.config({ path: path.resolve(__dirname, "../.env") });
import {app} from "./app.js";


// import dotenv from "dotenv";
// dotenv.config();
// import {app} from "./app.js";


import express from "express";
import mongoose from "mongoose";
import connectDB from "./db/index.js";
import { cronService } from "./services/cron.service.js";
import { startEmailSyncJob } from "./jobs/emailSync.job.js";

connectDB()
.then(async ()=>{
    // Drop the stale userId_1_googleEventId_1 index if it still exists.
    // This index was created in an earlier schema version and causes
    // E11000 duplicate key errors when saving calendar events without
    // a Google Calendar ID (googleEventId: null).
    try {
      const { CalendarEvent } = await import("./models/calendarEvent.model.js");
      const db = mongoose.connection.db;
      const col = db.collection("calendarevents");
      const indexes = await col.indexes();
      console.log("📋 [Startup] calendarevents indexes:", indexes.map(i => i.name));

      // 1. Drop stale index from old schema if it still exists
      const staleIndex = indexes.find(i => i.name === "userId_1_googleEventId_1");
      if (staleIndex) {
        await col.dropIndex("userId_1_googleEventId_1");
        console.log("🗑️  Dropped stale index: userId_1_googleEventId_1");
      }

      // 2. Remove duplicate emailId:null documents so the unique sparse
      //    index on {userId, emailId} can be built without conflicts.
      //    For each user, keep the most recent null-emailId doc and delete the rest.
      const nullEmailDocs = await col
        .find({ emailId: null })
        .sort({ createdAt: -1 })
        .toArray();

      const seenUsers = new Set();
      const toDelete = [];
      for (const doc of nullEmailDocs) {
        const key = doc.userId?.toString();
        if (seenUsers.has(key)) {
          toDelete.push(doc._id);
        } else {
          seenUsers.add(key);
        }
      }
      if (toDelete.length > 0) {
        await col.deleteMany({ _id: { $in: toDelete } });
        console.log(`🗑️  Removed ${toDelete.length} duplicate null-emailId calendarevents doc(s)`);
      }

      // 3. Sync schema indexes
      await CalendarEvent.syncIndexes();
      console.log("✅ [Startup] calendarevents indexes synced");
    } catch (indexErr) {
      console.warn("⚠️  Index sync skipped:", indexErr.message);
    }

    app.listen(process.env.PORT || 5000,()=>{
        console.log(`Server is running on port ${process.env.PORT || 5000}`);
        startEmailSyncJob(); // Start the email sync cron job when the server starts
        
         // Start cron jobs
      console.log("🚀 Initializing cron jobs...");
      //cronService.startEmailSyncJob();
    });
})
.catch((err)=>{
    console.log("Failed due to error",err)
    throw err
});


process.on('SIGTERM', () => {
    console.log('⚠️  SIGTERM received: shutting down gracefully');
    cronService.stopAllJobs();
    mongoose.connection.close(() => {
      console.log('📦 Database connection closed');
      process.exit(0);
    });
  });
  
  process.on('SIGINT', () => {
    console.log('⚠️  SIGINT received: shutting down gracefully');
    cronService.stopAllJobs();
    mongoose.connection.close(() => {
      console.log('📦 Database connection closed');
      process.exit(0);
    });
  });