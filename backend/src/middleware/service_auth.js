export const serviceAuth = (req, res, next) => {
  if (req.headers["x-service-key"] !== process.env.SERVICE_KEY) {
    return res.status(401).json({ error: "Unauthorized service" });
  }
  next();
};
