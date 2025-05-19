const User = require('../models/User');

// @desc    Register user
// @route   POST /api/auth/register
// @access  Public
exports.register = async (req, res) => {
  try {
    const { name, email, password, role, phone } = req.body;

    console.log(`Registration attempt for email: ${email}, role: ${role}`);

    // Check if user exists
    const userExists = await User.findOne({ email });

    if (userExists) {
      console.log(`Registration failed: User with email ${email} already exists`);
      return res.status(400).json({
        success: false,
        message: 'User already exists',
      });
    }

    console.log(`Creating new user with email: ${email}, role: ${role}`);

    // Create user with explicit database specification
    const user = await User.create({
      name,
      email,
      password,
      role: role || 'user', // Default to 'user' if role is not provided
      phone,
    });

    console.log(`User created successfully with ID: ${user._id}`);

    // Send token response
    sendTokenResponse(user, 201, res);
  } catch (error) {
    console.error(`Registration error: ${error.message}`, error);
    res.status(500).json({
      success: false,
      message: error.message,
    });
  }
};

// @desc    Login user
// @route   POST /api/auth/login
// @access  Public
exports.login = async (req, res) => {
  try {
    const { email, password } = req.body;

    console.log(`Login attempt for email: ${email}`);
    console.log(`Request body:`, req.body);

    // Validate email & password
    if (!email || !password) {
      console.log('Login failed: Missing email or password');
      return res.status(400).json({
        success: false,
        message: 'Please provide an email and password',
      });
    }

    // Check for user - explicitly specify the database
    console.log(`Looking for user with email: ${email}`);
    const user = await User.findOne({ email }).select('+password');

    if (!user) {
      console.log(`Login failed: No user found with email ${email}`);
      return res.status(401).json({
        success: false,
        message: 'Invalid credentials',
      });
    }

    console.log(`User found: ${user.name}, role: ${user.role}, id: ${user._id}`);
    console.log(`Stored password hash: ${user.password}`);
    console.log(`Entered password: ${password}`);

    // Check if password matches
    try {
      console.log(`Comparing password for user: ${email}`);
      const isMatch = await user.matchPassword(password);
      console.log(`Password match result: ${isMatch}`);

      if (!isMatch) {
        console.log('Login failed: Password does not match');
        return res.status(401).json({
          success: false,
          message: 'Invalid credentials',
        });
      }

      console.log('Login successful, generating token');

      // Send token response
      sendTokenResponse(user, 200, res);
    } catch (passwordError) {
      console.error('Error during password comparison:', passwordError);
      console.error(passwordError.stack);
      return res.status(500).json({
        success: false,
        message: 'Error during authentication',
        error: passwordError.message
      });
    }
  } catch (error) {
    console.error('Login error:', error);
    console.error(error.stack);
    res.status(500).json({
      success: false,
      message: error.message,
      stack: process.env.NODE_ENV === 'production' ? null : error.stack
    });
  }
};

// @desc    Get current logged in user
// @route   GET /api/auth/me
// @access  Private
exports.getMe = async (req, res) => {
  try {
    const user = await User.findById(req.user.id);

    res.status(200).json({
      success: true,
      data: user,
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      message: error.message,
    });
  }
};

// @desc    Log user out / clear cookie
// @route   GET /api/auth/logout
// @access  Private
exports.logout = async (req, res) => {
  res.status(200).json({
    success: true,
    message: 'User logged out successfully',
  });
};

// @desc    Verify token
// @route   GET /api/auth/verify
// @access  Private
exports.verifyToken = async (req, res) => {
  try {
    // The protect middleware already verified the token
    // and attached the user to req.user
    const user = await User.findById(req.user.id);

    if (!user) {
      return res.status(404).json({
        success: false,
        message: 'User not found',
      });
    }

    res.status(200).json({
      success: true,
      user: {
        id: user._id,
        name: user.name,
        email: user.email,
        role: user.role,
        phone: user.phone,
      },
    });
  } catch (error) {
    console.error('Token verification error:', error);
    res.status(500).json({
      success: false,
      message: error.message,
    });
  }
};

// Helper function to get token from model, create cookie and send response
const sendTokenResponse = (user, statusCode, res) => {
  // Create token
  const token = user.getSignedJwtToken();

  res.status(statusCode).json({
    success: true,
    token,
    user: {
      id: user._id,
      name: user.name,
      email: user.email,
      role: user.role,
      phone: user.phone,
    },
  });
};
