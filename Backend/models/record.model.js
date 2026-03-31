const mongoose = require("mongoose");

const recordSchema = new mongoose.Schema(
  {
    name: { type: String, required: true },
    feature1: { type: Number, required: true },
    feature2: { type: Number, required: true },
  },
  { timestamps: true }
);

module.exports = mongoose.model("Record", recordSchema);
