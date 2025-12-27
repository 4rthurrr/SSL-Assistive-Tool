const express = require("express");
const router = express.Router();

//Insert Model
const User = require("../model/usermodel");
//Insert User Controller
const UserController = require("../controllers/usercontrol");

//Get all users
router.get("/", UserController.getAllUsers);
router.post("/", UserController.addUser);
router.get("/:id", UserController.getById); 
router.put("/:id", UserController.updateUser);  

// Delete user
router.delete("/:id", UserController.deleteUser);

// Add login route
router.post("/login", UserController.loginUser);

//export
module.exports = router;