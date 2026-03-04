const express = require("express");
const User = require("../models/usermodel");
const jwt = require("jsonwebtoken");
const bcrypt = require("bcryptjs");

// JWT Secret Key - Store this in .env file in production
const JWT_SECRET = process.env.JWT_SECRET || "your_secret_key_here_change_in_production";

// Generate JWT Token
const generateToken = (userId) => {
  return jwt.sign({ id: userId }, JWT_SECRET, { expiresIn: "7d" });
};

// Login user with JWT
const loginUser = async (req, res, next) => {
  const { email, password } = req.body;
  
  if (!email || !password) {
    return res.status(400).json({ success: false, message: "Email and password required" });
  }

  let user;
  try {
    user = await User.findOne({ email });
  } catch (err) {
    console.log(err);
    return res.status(500).json({ success: false, message: "Server error" });
  }

  if (!user) {
    return res.status(401).json({ success: false, message: "Invalid credentials" });
  }

  // Compare hashed password
  const isPasswordValid = await bcrypt.compare(password, user.password);
  
  if (!isPasswordValid) {
    return res.status(401).json({ success: false, message: "Invalid credentials" });
  }

  // Generate JWT token
  const token = generateToken(user._id);

  // Get game profile if exists
  const GameProfile = require("../../game-engine/models/GameProfile");
  let gameProfile = await GameProfile.findOne({ userId: user._id });
  
  return res.status(200).json({ 
    success: true,
    token: token, // Send JWT token
    user: {
      _id: user._id,
      name: user.name,
      email: user.email,
      age: user.age,
      hasTakenQuiz: user.hasTakenQuiz || false,
      recommendedLevel: user.recommendedLevel || 'basic',
      gameProfile: gameProfile || null
    }
  });
};

// Register user with password hashing
const addUser = async (req, res, next) => {
  const { name, email, password, age } = req.body;
  
  try {
    // Check if user already exists
    const existingUser = await User.findOne({ email });
    if (existingUser) {
      return res.status(400).json({ message: "User already exists" });
    }

    // Hash password
    const hashedPassword = await bcrypt.hash(password, 10);
    
    // Create new user
    const user = new User({
      name,
      email,
      password: hashedPassword,
      age
    });
    
    await user.save();
    
    // Generate token for auto-login after registration
    const token = generateToken(user._id);
    
    return res.status(201).json({ 
      success: true,
      token: token,
      user: {
        _id: user._id,
        name: user.name,
        email: user.email,
        age: user.age
      }
    });
  } catch (err) {
    console.log(err);
    return res.status(500).json({ message: "Unable to add user" });
  }
};

const getAllUsers = async (req, res, next) => {
  let users;
  try {
    users = await User.find().select('-password'); // Exclude password
  } catch (err) {
    console.log(err);
  }
  
  if (!users) {
    return res.status(404).json({ message: "No users found" });
  }
  
  return res.status(200).json({ users });
};

const getById = async (req, res, next) => {
  const id = req.params.id;
  let user;
  try {
    user = await User.findById(id).select('-password'); // Exclude password
  } catch (err) {
    console.log(err);
  }
  if (!user) {
    return res.status(404).json({ message: "No user found" });
  }
  return res.status(200).json({ user });
};

const updateUser = async (req, res, next) => {
  const id = req.params.id;
  const { name, email, password, age } = req.body;
  
  try {
    const updateData = { name, email, age };
    
    // Only hash and update password if provided
    if (password) {
      updateData.password = await bcrypt.hash(password, 10);
    }
    
    const user = await User.findByIdAndUpdate(id, updateData, { new: true }).select('-password');
    
    if (!user) {
      return res.status(404).json({ message: "Unable to update user" });
    }
    
    return res.status(200).json({ user });
  } catch (err) {
    console.log(err);
    return res.status(500).json({ message: "Server error" });
  }
};

const deleteUser = async (req, res, next) => {
  const id = req.params.id;
  let user;
  try {
    user = await User.findByIdAndDelete(id);
  } catch (err) {
    console.log(err);
  }
  if (!user) {
    return res.status(404).json({ message: "Unable to delete user" });
  }
  return res.status(200).json({ message: "User deleted successfully" });
};

exports.getAllUsers = getAllUsers;
exports.addUser = addUser;
exports.getById = getById;
exports.updateUser = updateUser;
exports.deleteUser = deleteUser;
exports.loginUser = loginUser;