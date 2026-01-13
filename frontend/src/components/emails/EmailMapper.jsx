const mapEmailForUI = (email) => {
  const senderEmail =
    email.from?.match(/<(.+?)>/)?.[1] || email.from;

  return {
    id: email._id,
    sender: email.from,
    senderEmail,            // ✅ ADD THIS
    messageId: email.emailId,
    threadId: email.threadId,
    isStarred: email.isStarred ?? false,
    folder:email.folder,

    company:
      email.from?.split("@")[1]?.split(".")[0] || "Unknown",

    subject: email.subject || "(No subject)",
    body: email.text || "",
    preview: email.text?.slice(0, 90) || "",

    time: new Date(email.date).toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
    }),

    tag: email.type,
    tagType:
      email.type === "INTERVIEW" ? "success" :
      email.type === "OFFER"     ? "success" :
      email.type === "REJECTION" ? "error"   :
      email.type === "JOB"       ? "warning" :
      "default",

    read: email.isEmbedded,
  };
};

export default mapEmailForUI;
