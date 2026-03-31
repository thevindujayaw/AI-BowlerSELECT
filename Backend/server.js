const express = require("express");
const cors = require("cors");
const dotenv = require("dotenv");
const connectDB = require("./config/db");

dotenv.config();

const app = express();
app.use(cors());
app.use(express.json());

// Connect DB
connectDB();

// Routes
app.use("/api/auth", require("./routes/auth.routes"));
app.use("/api/records", require("./routes/record.routes"));
app.use("/api/predict", require("./routes/predict.routes"));
app.use("/api/options", require("./routes/options.routes"));
app.use("/api/account", require("./routes/account.routes"));

// Home route
app.get("/", (req, res) => {
  res.send("Backend Running (MongoDB + Express)");
});

const PORT = process.env.PORT || 5001;
app.listen(PORT, () => console.log(`Server running on http://localhost:${PORT}`));
