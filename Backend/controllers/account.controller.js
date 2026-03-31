const Prediction = require("../models/prediction.model");

exports.getAccountData = async (req, res) => {
  try {
    // req.user comes from protect middleware
    const user = req.user;

    // Get last 20 predictions (newest first)
    const predictions = await Prediction.find({ user: user._id })
      .sort({ createdAt: -1 })
      .limit(20);

    res.json({
      user: {
        name: user.name,
        email: user.email,
        teamType: user.teamType,
        teamName: user.teamName
      },
      predictions
    });

  } catch (error) {
    res.status(500).json({
      error: "Failed to load account data",
      details: error.message
    });
  }
};

exports.deletePrediction = async (req, res) => {
  try {
    const prediction = await Prediction.findOneAndDelete({
      _id: req.params.id,
      user: req.user._id,
    });

    if (!prediction) {
      return res.status(404).json({ error: "Prediction not found" });
    }

    res.json({ message: "Prediction deleted" });
  } catch (error) {
    res.status(400).json({
      error: "Failed to delete prediction",
      details: error.message
    });
  }
};
