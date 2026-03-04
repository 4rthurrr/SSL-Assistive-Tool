const jwt = require("jsonwebtoken");

const JWT_SECRET = process.env.JWT_SECRET || "Hf7&9dJk2!vLxQp8rTgMzS4wYb6eW1u3";

// Middleware to verify JWT token
const verifyToken = (req, res, next) => {
  // Get token from header
  const token = req.header("Authorization")?.replace("Bearer ", "");

  if (!token) {
    return res.status(401).json({ message: "No token, authorization denied" });
  }

  try {
    // Verify token
    const decoded = jwt.verify(token, JWT_SECRET);
    req.userId = decoded.id; // Add user id to request
    next();
  } catch (err) {
    res.status(401).json({ message: "Token is not valid" });
  }
};

module.exports = verifyToken;