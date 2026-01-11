import { callMCP } from "./mcp.service.js";

export async function executePipeline({
  endpoint,
  args = {},
  userId,
  jwt
}) {
  if (!endpoint) {
    throw new Error("endpoint is required");
  }

  if (!userId) {
    throw new Error("userId is required");
  }

  if (!jwt) {
    throw new Error("jwt is required");
  }

 
  return callMCP({
    endpoint,
    args,
    userId,
    jwt
  });
}
