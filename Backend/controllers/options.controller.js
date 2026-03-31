const path = require("path");
const fs = require("fs");
const csv = require("csv-parser");

let cachedOptions = null;

function uniqueSorted(arr) {
  return [...new Set(arr.map(v => String(v).trim()).filter(Boolean))].sort();
}

exports.getOptions = async (req, res) => {
  try {
    // return cached to avoid reading CSV on every request
    if (cachedOptions) return res.json(cachedOptions);

    const csvPath = path.join(__dirname, "..", "..", "..", "Book2.csv"); 
    // adjust if Book2.csv is in another location

    const options = {
      match_type: [],
      pitch_type: [],
      weather: [],
      ground: [],
      your_team: [],
      opposition_team: [],
      bowler_type: [],
    };

    fs.createReadStream(csvPath)
      .pipe(csv())
      .on("data", (row) => {
        options.match_type.push(row.match_type);
        options.pitch_type.push(row.pitch_type);
        options.weather.push(row.weather);
        options.ground.push(row.ground);
        options.your_team.push(row.your_team);
        options.opposition_team.push(row.opposition_team);
        options.bowler_type.push(row.bowler_type);
      })
      .on("end", () => {
        // normalize + dedupe + sort
        const cleaned = {};
        for (const key of Object.keys(options)) {
          cleaned[key] = uniqueSorted(options[key]);
        }

        cachedOptions = cleaned;
        return res.json(cleaned);
      })
      .on("error", (err) => {
        return res.status(500).json({ message: "CSV read failed", error: err.message });
      });

  } catch (err) {
    return res.status(500).json({ message: err.message });
  }
};