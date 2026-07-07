import fs from "node:fs";
import vm from "node:vm";

function extractLiteral(source, marker) {
  const start = source.indexOf(marker);
  if (start < 0) throw new Error(`Marker not found: ${marker}`);
  const open = source.indexOf("[", start);
  let depth = 0;
  let quote = null;
  let escaped = false;
  for (let i = open; i < source.length; i += 1) {
    const ch = source[i];
    if (quote) {
      if (escaped) escaped = false;
      else if (ch === "\\") escaped = true;
      else if (ch === quote) quote = null;
      continue;
    }
    if (ch === "'" || ch === '"' || ch === "`") {
      quote = ch;
      continue;
    }
    if (ch === "[") depth += 1;
    else if (ch === "]") {
      depth -= 1;
      if (depth === 0) return source.slice(open, i + 1);
    }
  }
  throw new Error(`Unterminated array: ${marker}`);
}

function readArray(file, marker) {
  const source = fs.readFileSync(file, "utf8");
  const literal = extractLiteral(source, marker);
  return vm.runInNewContext(`(${literal})`, Object.create(null), { timeout: 1000 });
}

const jobs = readArray("job-batch.html", "var JOBS =");
const apiGroups = readArray("plan-api.html", "var GROUPS =");

fs.writeFileSync(
  "tmp/prototype_data.json",
  JSON.stringify({ jobs, apiGroups }, null, 2),
  "utf8",
);

console.log(JSON.stringify({
  jobs: jobs.length,
  jobNumbers: jobs.map((job) => job.no),
  apiGroups: apiGroups.map((group) => [group.name, group.eps.length]),
  endpoints: apiGroups.reduce((sum, group) => sum + group.eps.length, 0),
}, null, 2));
