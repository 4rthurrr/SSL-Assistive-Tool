const express = require("express");
const router = express.Router();
const User = require("../models/usermodel");
const UserController = require("../controllers/usercontrol");
const verifyToken = require("../middleware/auth");

// Public routes (no authentication needed)
router.post("/", UserController.addUser); // Register
router.post("/login", UserController.loginUser); // Login

// Protected routes (require authentication)
router.get("/", verifyToken, UserController.getAllUsers);
router.get("/:id", verifyToken, UserController.getById); 
router.put("/:id", verifyToken, UserController.updateUser);  
router.delete("/:id", verifyToken, UserController.deleteUser);

module.exports = router;