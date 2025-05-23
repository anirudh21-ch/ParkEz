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

// Create admin user
const createAdmin = async () => {
  try {
    await connectDB();

    // Check if admin already exists
    const adminExists = await User.findOne({ email: 'admin@parkez.com' });

    if (adminExists) {
      console.log('Admin user already exists');

      // Update admin password
      const salt = await bcrypt.genSalt(10);
      const hashedPassword = await bcrypt.hash('admin123', salt);

      adminExists.password = hashedPassword;
      await adminExists.save();

      console.log('Admin password updated');
      process.exit(0);
    }

    // Create new admin user
    const salt = await bcrypt.genSalt(10);
    const hashedPassword = await bcrypt.hash('admin123', salt);

    const admin = await User.create({
      name: 'Admin',
      email: 'admin@parkez.com',
      password: hashedPassword,
      role: 'admin',
      phone: '1234567890',
      registration_number: 'ADMIN-001' // Add a unique registration number
    });

    console.log('Admin user created successfully');
    process.exit(0);
  } catch (error) {
    console.error(`Error creating admin user: ${error.message}`);
    process.exit(1);
  }
};

// Run the function
createAdmin();
