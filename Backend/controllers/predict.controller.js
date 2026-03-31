const path = require("path");
const { spawn } = require("child_process");
const Prediction = require("../models/prediction.model");

async function executePrediction(req, res, { saveToDb }) {
  try {
    const inputData = req.body;
    const scriptPath = path.join(__dirname, "..", "..", "predict_runtime.py");

    const pythonPath = path.join(__dirname, "..", "..", "venv", "bin", "python");

    const python = spawn(
      pythonPath,
      [scriptPath, JSON.stringify(inputData)],
      { windowsHide: true }
    );

    let stdout = "";
    let stderr = "";

    python.stdout.on("data", (data) => {
      stdout += data.toString();
    });

    python.stderr.on("data", (data) => {
      stderr += data.toString();
    });

    python.on("error", (err) => {
      return res.status(500).json({
        error: "Failed to start Python process",
        details: err.message,
      });
    });

    python.on("close", async (code) => {
      if (code !== 0) {
        return res.status(500).json({
          error: "Python script execution failed",
          exitCode: code,
          details: stderr || stdout,
        });
      }

      try {
        const result = JSON.parse(stdout);
        if (result && result.error) {
          return res.status(400).json(result);
        }

        if (saveToDb && req.user && req.user._id) {
          await Prediction.create({
            user: req.user._id,
            mode: inputData.mode,
            input_data: inputData,
            results: result.results
          });
        }

        return res.json(result);
      } catch (err) {
        return res.status(500).json({
          error: "Invalid JSON returned from Python",
          raw: stdout,
        });
      }
    });

  } catch (err) {
    return res.status(500).json({
      error: "Prediction controller error",
      details: err.message,
    });
  }
}

exports.runPrediction = async (req, res) => {
  if (!req.user || !req.user._id) {
    return res.status(401).json({ error: "Unauthorized" });
  }
  return executePrediction(req, res, { saveToDb: true });
};

exports.runPredictionPublic = async (req, res) => {
  return executePrediction(req, res, { saveToDb: false });
};
