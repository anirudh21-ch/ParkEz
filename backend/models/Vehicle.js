const mongoose = require('mongoose');

const VehicleSchema = new mongoose.Schema(
  {
    user: {
      type: mongoose.Schema.Types.ObjectId,
      ref: 'User',
      required: true,
    },
    vehicleNumber: {
      type: String,
      required: [true, 'Please add a vehicle number'],
      unique: true,
      trim: true,
    },
    vehicleType: {
      type: String,
      required: [true, 'Please add a vehicle type'],
      enum: ['car', 'motorcycle', 'truck', 'other'],
    },
    make: {
      type: String,
      required: [true, 'Please add vehicle make'],
    },
    model: {
      type: String,
      required: [true, 'Please add vehicle model'],
    },
    color: {
      type: String,
      required: [true, 'Please add vehicle color'],
    },
    qrCode: {
      type: String,
      unique: true,
    },
  },
  {
    timestamps: true,
  }
);

// Generate QR code before saving
VehicleSchema.pre('save', function (next) {
  // Generate a unique QR code based on vehicle number and user ID
  if (!this.qrCode) {
    this.qrCode = `PARKEZ-${this.vehicleNumber}-${this.user}`;
  }
  next();
});

module.exports = mongoose.model('Vehicle', VehicleSchema);
