
import fetch from "node-fetch";

const BASE_URL = "http://localhost:9001"; 
const ENDPOINT = "/ask-seekr";

const JWT = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJfaWQiOiI2OTc5MGI0YTc4ZTVhMTRjYmRkMzZmMjMiLCJlbWFpbCI6ImRhdmlkQGV4YW1wbGUuY29tIiwiZnVsbG5hbWUiOiJkYXZpZCIsImlhdCI6MTc2OTU0MDc3OCwiZXhwIjoxNzY5NjI3MTc4fQ.diKFpbHYb0TCn4GmeU5XAUL4QGcWak4mlEPQOfbzsK0";


const CONVERSATION_ID = "e2e-test-convo-1";

async function sendMessage(text, metadata = {}) {
  const res = await fetch(`${BASE_URL}${ENDPOINT}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${JWT}`,
    },
    body: JSON.stringify({
      text,
      conversation_id: CONVERSATION_ID,
      metadata,
    }),
  });

  const data = await res.json();
  return data;
}

async function runTest() {
  console.log("🚀 Starting Ask Seekr E2E test");
  console.log("Conversation ID:", CONVERSATION_ID);
  console.log("-".repeat(60));


  let response = await sendMessage("hi");

  console.log("USER: hi");
  console.log("BOT RESPONSE:");
  console.log(response);
  console.log("-".repeat(60));

  response = await sendMessage(
    "Find me Python backend jobs in Bangalore"
  );

  console.log("USER: Find me Python backend jobs in Bangalore");
  console.log("BOT RESPONSE:");
  console.log(response);
  console.log("-".repeat(60));


  response = await sendMessage(
    "Sync my job emails"
  );

  console.log("USER: Sync my job emails");
  console.log("BOT RESPONSE:");
  console.log(response);
  console.log("-".repeat(60));

  console.log("✅ E2E test completed");
}

runTest().catch((err) => {
  console.error("❌ E2E test failed:", err.message);
});
