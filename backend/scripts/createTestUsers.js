const mongoose = require('mongoose');
const bcrypt = require('bcryptjs');
const dotenv = require('dotenv');

// Load environment variables
dotenv.config({ path: './.env' });

// Import User model
const User = require('../models/User');

// Connect to MongoDB
const connectDB = async () => {
  try {
    await mongoose.connect(process.env.MONGO_URI, {
      useNewUrlParser: true,
      useUnifiedTopology: true,
      ssl: true,
      retryWrites: true,
      w: 'majority'
    });
    console.log('MongoDB Connected');
  } catch (error) {
    console.error(`Error connecting to MongoDB: ${error.message}`);
    process.exit(1);
  }
};

// Create test users
const createTestUsers = async () => {
  try {
    await connectDB();

    // Create a regular user
    const userExists = await User.findOne({ email: 'user@parkez.com' });
    if (!userExists) {
      const salt = await bcrypt.genSalt(10);
      const hashedPassword = await bcrypt.hash('user123', salt);
      
      await User.create({
        name: 'Test User',
        email: 'user@parkez.com',
        password: hashedPassword,
        role: 'user',
        phone: '1234567890'
      });
      
      console.log('Test user created successfully');
    } else {
      console.log('Test user already exists');
    }

    // Create an operator
    const operatorExists = await User.findOne({ email: 'operator@parkez.com' });
    if (!operatorExists) {
      const salt = await bcrypt.genSalt(10);
      const hashedPassword = await bcrypt.hash('operator123', salt);
      
      await User.create({
        name: 'Test Operator',
        email: 'operator@parkez.com',
        password: hashedPassword,
        role: 'operator',
        phone: '9876543210'
      });
      
      console.log('Test operator created successfully');
    } else {
      console.log('Test operator already exists');
    }

    process.exit(0);
  } catch (error) {
    console.error(`Error creating test users: ${error.message}`);
    process.exit(1);
  }
};

// Run the function
createTestUsers();
