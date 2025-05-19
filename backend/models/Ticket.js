const mongoose = require('mongoose');

const TicketSchema = new mongoose.Schema(
  {
    user: {
      type: mongoose.Schema.Types.ObjectId,
      ref: 'User',
      required: true,
    },
    vehicle: {
      type: mongoose.Schema.Types.ObjectId,
      ref: 'Vehicle',
      required: true,
    },
    zone: {
      type: mongoose.Schema.Types.ObjectId,
      ref: 'Zone',
      required: true,
    },
    slotNumber: {
      type: String,
      required: [true, 'Please add a slot number'],
    },
    entryTime: {
      type: Date,
      default: Date.now,
    },
    exitTime: {
      type: Date,
    },
    status: {
      type: String,
      enum: ['active', 'completed', 'expired'],
      default: 'active',
    },
    isReservation: {
      type: Boolean,
      default: false,
    },
    reservationTime: {
      type: Date,
    },
    amount: {
      type: Number,
    },
    paymentStatus: {
      type: String,
      enum: ['pending', 'completed'],
      default: 'pending',
    },
  },
  {
    timestamps: true,
  }
);

// Calculate amount before saving if ticket is completed
TicketSchema.pre('save', function (next) {
  if (this.status === 'completed' && this.exitTime && !this.amount) {
    // Calculate duration in hours
    const entryTime = new Date(this.entryTime);
    const exitTime = new Date(this.exitTime);
    const durationHours = (exitTime - entryTime) / (1000 * 60 * 60);

    // Set amount based on hourly rate (will be populated from zone)
    this.amount = durationHours * this.hourlyRate;
  }
  next();
});

module.exports = mongoose.model('Ticket', TicketSchema);
