class SSEService {
  constructor() {
    // Map<userId string → { res, heartbeat }>
    this.clients = new Map();
  }

  addClient(userId, res) {
    this.removeClient(userId); // drop any stale connection for this user

    res.set({
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache",
      "X-Accel-Buffering": "no", // prevents nginx from buffering the stream
      Connection: "keep-alive",
    });
    res.flushHeaders();
    res.write(": connected\n\n");

    // Heartbeat every 25s to stop proxies killing idle connections
    const heartbeat = setInterval(() => {
      if (!res.writableEnded) res.write(": heartbeat\n\n");
    }, 25_000);

    this.clients.set(String(userId), { res, heartbeat });
    console.log(`📡 [SSE] Client connected: ${userId}`);
  }

  removeClient(userId) {
    const client = this.clients.get(String(userId));
    if (!client) return;
    clearInterval(client.heartbeat);
    this.clients.delete(String(userId));
    console.log(`📡 [SSE] Client disconnected: ${userId}`);
  }

  emit(userId, event, data = {}) {
    const client = this.clients.get(String(userId));
    if (!client || client.res.writableEnded) return;
    client.res.write(`event: ${event}\n`);
    client.res.write(`data: ${JSON.stringify(data)}\n\n`);
    console.log(`📡 [SSE] Emitted "${event}" → ${userId}`);
  }
}

export const sseService = new SSEService();
