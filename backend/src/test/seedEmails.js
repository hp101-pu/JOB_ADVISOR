import mongoose from "mongoose";
import dotenv from "dotenv";
import { Email } from "../models/email.model.js";
import { User } from "../models/user.model.js";

dotenv.config();

const now = new Date();
const daysAgo = (n) => new Date(now - n * 24 * 60 * 60 * 1000);

async function seed() {
  try {
    await mongoose.connect(`${process.env.MONGO_URI}/${process.env.DB_NAME}`);
    console.log("✅ Connected to MongoDB");

    // ── AUTO-FIND YOUR USER ──────────────────────────────
    const user = await User.findOne({}).select("_id email fullname");
    if (!user) {
      console.error("❌ No user found in DB. Please register/login first.");
      process.exit(1);
    }
    const USER_ID = user._id;
    console.log(`👤 Found user: ${user.fullname} (${user.email})`);
    console.log(`🆔 userId: ${USER_ID}`);
    // ────────────────────────────────────────────────────

    const dummyEmails = [
      // INTERVIEWS
      { emailId: "dummy_001", threadId: "t001", folder: "INBOX", type: "INTERVIEW", from: "recruiter@google.com", subject: "Interview Scheduled – Software Engineer at Google", text: "We'd like to schedule a technical interview. Please confirm availability for Monday 10 AM IST.", date: daysAgo(2) },
      { emailId: "dummy_002", threadId: "t002", folder: "INBOX", type: "INTERVIEW", from: "hr@microsoft.com", subject: "Technical Round 2 – Microsoft", text: "Congratulations on clearing Round 1! Round 2 is scheduled for Friday at 3 PM via Teams.", date: daysAgo(4) },
      { emailId: "dummy_003", threadId: "t003", folder: "INBOX", type: "INTERVIEW", from: "talent@flipkart.com", subject: "Flipkart – Interview Invitation for Frontend Developer", text: "We'd like to invite you for a technical discussion for the Frontend Developer position.", date: daysAgo(6) },
      { emailId: "dummy_004", threadId: "t004", folder: "INBOX", type: "INTERVIEW", from: "hr@infosys.com", subject: "Interview Call – Infosys Digital", text: "We would like to schedule a technical interview for the position of Systems Engineer.", date: daysAgo(22) },

      // OFFERS
      { emailId: "dummy_005", threadId: "t005", folder: "INBOX", type: "OFFER", from: "hr@amazon.com", subject: "Offer Letter – SDE-1 at Amazon", text: "We are pleased to extend an offer for the position of SDE-1 at Amazon. Please respond within 5 business days.", date: daysAgo(1) },
      { emailId: "dummy_006", threadId: "t006", folder: "INBOX", type: "OFFER", from: "careers@razorpay.com", subject: "Congratulations! Offer from Razorpay", text: "We are excited to offer you the role of Frontend Engineer at Razorpay. Joining date: 1st April 2026.", date: daysAgo(3) },

      // REJECTIONS
      { emailId: "dummy_007", threadId: "t007", folder: "INBOX", type: "REJECTION", from: "noreply@meta.com", subject: "Your application at Meta", text: "After careful consideration, we have decided to move forward with other candidates at this time.", date: daysAgo(5) },
      { emailId: "dummy_008", threadId: "t008", folder: "INBOX", type: "REJECTION", from: "recruiting@uber.com", subject: "Update on your application – Uber", text: "Unfortunately, we will not be moving forward with your application for the current opening.", date: daysAgo(8) },
      { emailId: "dummy_009", threadId: "t009", folder: "INBOX", type: "REJECTION", from: "hr@swiggy.com", subject: "Swiggy – Application Status Update", text: "We regret to inform you that we are not proceeding with your candidacy at this time.", date: daysAgo(15) },
      { emailId: "dummy_010", threadId: "t010", folder: "INBOX", type: "REJECTION", from: "careers@ola.com", subject: "Ola – Application Update", text: "We regret to inform you that we won't be moving forward with your application at this stage.", date: daysAgo(25) },

      // JOB APPLICATIONS SENT (no reply yet — for follow-up testing)
      { emailId: "dummy_011", threadId: "t011", folder: "SENT", type: "JOB", from: "you@gmail.com", subject: "Application for React Developer – Zomato", text: "I am writing to express my interest in the React Developer position at Zomato. Please find my resume attached.", date: daysAgo(10) },
      { emailId: "dummy_012", threadId: "t012", folder: "SENT", type: "JOB", from: "you@gmail.com", subject: "Application – Full Stack Developer at Paytm", text: "I would like to apply for the Full Stack Developer role at Paytm. My skills in React and Node.js align well.", date: daysAgo(12) },
      { emailId: "dummy_013", threadId: "t013", folder: "SENT", type: "JOB", from: "you@gmail.com", subject: "Job Application – CRED Frontend Engineer", text: "Please find my application for the Frontend Engineer role at CRED. 2 years experience with React and TypeScript.", date: daysAgo(20) },

      // OTHER
      { emailId: "dummy_014", threadId: "t014", folder: "INBOX", type: "OTHER", from: "newsletter@linkedin.com", subject: "10 jobs picked for you this week", text: "Based on your profile: React Developer at Infosys, Node.js Engineer at TCS...", date: daysAgo(1) },
      { emailId: "dummy_015", threadId: "t015", folder: "INBOX", type: "OTHER", from: "jobs@naukri.com", subject: "New job alerts for React Developer", text: "15 new jobs matching your profile. Senior React Developer at HCL, Frontend Lead at Wipro.", date: daysAgo(3) },
    ];

    // Clear old dummy emails first
    const deleted = await Email.deleteMany({
      userId: USER_ID,
      emailId: { $regex: /^dummy_/ },
    });
    console.log(`🗑️  Cleared ${deleted.deletedCount} old dummy emails`);

    // Insert fresh
    const emails = dummyEmails.map((e) => ({ ...e, userId: USER_ID }));
    const inserted = await Email.insertMany(emails, { ordered: false });
    console.log(`✅ Seeded ${inserted.length} emails\n`);

    // Print summary
    const counts = {};
    emails.forEach((e) => { counts[e.type] = (counts[e.type] || 0) + 1; });
    console.log("📊 Breakdown:");
    Object.entries(counts).forEach(([type, count]) => {
      console.log(`   ${type.padEnd(12)}: ${count}`);
    });

    console.log("\n🎉 Done! Try these in the chatbot:");
    console.log('   "Give me my morning briefing"');
    console.log('   "How is my job search going?"');
    console.log('   "Who should I follow up with?"');
    console.log('   "Summarise my Amazon emails"');
    console.log('   "How many rejections do I have?"');

    await mongoose.disconnect();
  } catch (err) {
    console.error("❌ Seed failed:", err.message);
    process.exit(1);
  }
}

seed();