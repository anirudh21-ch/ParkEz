const mongoose = require('mongoose');

// MongoDB Atlas connection function
const connectDB = async () => {
  try {
    // MongoDB connection options
    const options = {
      useNewUrlParser: true,
      useUnifiedTopology: true,
      connectTimeoutMS: 30000,
      socketTimeoutMS: 45000,
      serverSelectionTimeoutMS: 30000,
    };

    // Connect to MongoDB Atlas
    console.log('Connecting to MongoDB Atlas...');
    const conn = await mongoose.connect(process.env.MONGO_URI, options);
    console.log(`MongoDB Connected: ${conn.connection.host}`);
    return conn;
  } catch (error) {
    console.error(`Error connecting to MongoDB: ${error.message}`);
    console.error('Please check your MongoDB Atlas connection string and make sure your IP is whitelisted.');
    console.error('For more information, visit: https://www.mongodb.com/docs/atlas/security-whitelist/');
    process.exit(1); // Exit the process if MongoDB connection fails
  }
};

module.exports = connectDB;
