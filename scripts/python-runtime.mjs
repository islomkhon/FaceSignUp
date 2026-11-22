import { existsSync } from "node:fs";
import { resolve } from "node:path";

export function pythonExecutable(root = process.cwd()) {
  const candidates =
    process.platform === "win32"
      ? [resolve(root, ".venv/Scripts/python.exe"), "python", "py"]
      : [resolve(root, ".venv/bin/python"), "python3", "python"];
  return candidates.find((candidate) => !candidate.includes("/") || existsSync(candidate))
    ?? candidates.at(-1);
}
