import { spawn } from "node:child_process";
import { resolve } from "node:path";
import { pythonExecutable } from "./python-runtime.mjs";

const root = process.cwd();
const commands = [
  {
    name: "api",
    command: pythonExecutable(root),
    args: [
      "-m",
      "uvicorn",
      "backend.app:app",
      "--host",
      "127.0.0.1",
      "--port",
      "8100",
      "--reload"
    ]
  },
  {
    name: "web",
    command: process.execPath,
    args: [resolve(root, "node_modules/vite/bin/vite.js")]
  }
];

const children = commands.map(({ name, command, args }) => {
  const child = spawn(command, args, {
    cwd: root,
    env: process.env,
    stdio: "inherit",
    shell: false
  });
  child.on("exit", (code) => {
    if (code !== 0 && code !== null) {
      console.error(`${name} exited with code ${code}`);
    }
  });
  return child;
});

function shutdown() {
  for (const child of children) {
    if (!child.killed) child.kill();
  }
}

process.on("SIGINT", shutdown);
process.on("SIGTERM", shutdown);
