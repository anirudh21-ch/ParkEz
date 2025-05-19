const mongoose = require('mongoose');

const ZoneSchema = new mongoose.Schema(
  {
    name: {
      type: String,
      required: [true, 'Please add a zone name'],
      trim: true,
    },
    address: {
      type: String,
      required: [true, 'Please add an address'],
    },
    operator: {
      type: mongoose.Schema.Types.ObjectId,
      ref: 'User',
      required: true,
    },
    totalSlots: {
      type: Number,
      required: [true, 'Please add total number of slots'],
    },
    availableSlots: {
      type: Number,
      default: function () {
        return this.totalSlots;
      },
    },
    hourlyRate: {
      type: Number,
      required: [true, 'Please add hourly rate'],
    },
    status: {
      type: String,
      enum: ['pending', 'approved', 'rejected'],
      default: 'pending',
    },
    location: {
      type: {
        type: String,
        enum: ['Point'],
        default: 'Point',
      },
      coordinates: {
        type: [Number],
        index: '2dsphere',
      },
    },
  },
  {
    timestamps: true,
  }
);

module.exports = mongoose.model('Zone', ZoneSchema);
