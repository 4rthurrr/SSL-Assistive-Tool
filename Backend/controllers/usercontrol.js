const express = require("express");
const User = require("../model/usermodel");

// Login user
const loginUser = async (req, res, next) => {
  const { email, password } = req.body;

  if (!email || !password) {
    return res.status(400).json({ success: false, message: "Email and password required" });
  }

  let user;
  try {
    user = await User.findOne({ email, password });
  } catch (err) {
    console.log(err);
    return res.status(500).json({ success: false, message: "Server error" });
  }

  if (!user) {
    return res.status(401).json({ success: false, message: "Invalid credentials" });
  }

  // Get game profile if exists
  const GameProfile = require("../model/GameProfile");
  let gameProfile = await GameProfile.findOne({ userId: user._id });
  
  return res.status(200).json({ 
    success: true, 
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




const getAllUsers = async (req, res, next) => {

  let users;
  try {
    users = await User.find();
  } catch (err) {
     console.log(err);
  }

  //not found
  if(!users){
    return res.status(404).json({ message: "No users found" });
  }

  //Display all users
  return res.status(200).json({ users });
};

//data insert
const addUser = async (req, res, next) => {
    const { name, email, password, age} = req.body;

    let users;

    try {
        users = new User({name, email,password, age});
        await users.save();
    } catch (err) {
        console.log(err);
    }

    //not insert users
    if(!users){
        return res.status(404).send({message: "Unable to add user" });
    }
    return res.status(200).json({ users });
};



// Get user by ID
const getById = async (req, res, next) => {
  const id = req.params.id;
  let user;
  try {
    user = await User.findById(id);
  } catch (err) {
    console.log(err);
  }

  if (!user) {
    return res.status(404).json({ message: "No user found" });
  }
  return res.status(200).json({ user });

};


// Update user
const updateUser = async (req, res, next) => {
  const id = req.params.id;
  const { name, email, password, age } = req.body;

  let users;
  try {
    users = await User.findByIdAndUpdate(
      id,
      { name:name,email:email, password:password, age:age });
    users = await users.save();
    
  } catch (err) {
    console.log(err);
  }

  if (!users) {
    return res.status(404).json({ message: "Unable to update user" });
  }
  return res.status(200).json({ users });
};

// Delete user
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
