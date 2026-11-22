import { spawnSync } from "node:child_process";
import { pythonExecutable } from "./python-runtime.mjs";

const result = spawnSync(pythonExecutable(), process.argv.slice(2), {
  cwd: process.cwd(),
  env: process.env,
  stdio: "inherit",
  shell: false
});

if (result.error) {
  console.error(result.error.message);
  process.exit(1);
}

process.exit(result.status ?? 1);
