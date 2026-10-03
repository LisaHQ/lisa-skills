"""Scenario s7: Node CLI 'tasklog' with a flawed README (review-only mode)."""
from fixture import w, git_init

ROOT = "s7-tasklog"


def build(base):
    r = base / ROOT
    w(r / "package.json", '''\
{
  "name": "tasklog",
  "version": "1.2.0",
  "description": "Track time on tasks from your terminal.",
  "type": "module",
  "bin": {
    "tasklog": "bin/tasklog.js"
  },
  "files": ["bin", "src"],
  "engines": {
    "node": ">=20"
  },
  "scripts": {
    "test": "node --test"
  },
  "repository": {
    "type": "git",
    "url": "git+https://github.com/example-org/tasklog.git"
  },
  "license": "GPL-3.0-only"
}
''')
    w(r / "bin/tasklog.js", '''\
#!/usr/bin/env node
import { parseArgs } from "node:util";
import { start, stop, status, report } from "../src/commands.js";

const USAGE = `Usage:
  tasklog start "<task>"     Start timing a task (stops the running one)
  tasklog stop               Stop the running task
  tasklog status             Show the running task and elapsed time
  tasklog report [--week]    Total time per task for today, or the last 7 days with --week
                             Add --csv to print CSV instead of a table`;

const [command, ...rest] = process.argv.slice(2);
const { values, positionals } = parseArgs({
  args: rest,
  allowPositionals: true,
  options: { week: { type: "boolean" }, csv: { type: "boolean" } },
});

switch (command) {
  case "start":
    if (!positionals[0]) { console.error(USAGE); process.exit(2); }
    await start(positionals.join(" "));
    break;
  case "stop":
    await stop();
    break;
  case "status":
    await status();
    break;
  case "report":
    await report({ week: values.week ?? false, csv: values.csv ?? false });
    break;
  default:
    console.log(USAGE);
    process.exit(command ? 2 : 0);
}
''')
    w(r / "src/store.js", '''\
import { homedir } from "node:os";
import { join } from "node:path";
import { readFile, writeFile } from "node:fs/promises";

/** Entries live in one JSON file: $TASKLOG_FILE, or ~/.tasklog.json by default. */
export const DATA_FILE = process.env.TASKLOG_FILE ?? join(homedir(), ".tasklog.json");

export async function load() {
  try {
    return JSON.parse(await readFile(DATA_FILE, "utf8"));
  } catch (error) {
    if (error.code === "ENOENT") return { running: null, entries: [] };
    throw error;
  }
}

export async function save(data) {
  await writeFile(DATA_FILE, JSON.stringify(data, null, 2));
}
''')
    w(r / "src/commands.js", '''\
import { load, save } from "./store.js";

export async function start(task) {
  const data = await load();
  if (data.running) data.entries.push({ ...data.running, end: Date.now() });
  data.running = { task, start: Date.now() };
  await save(data);
  console.log(`Started "${task}"`);
}

export async function stop() {
  const data = await load();
  if (!data.running) return console.log("Nothing is running.");
  data.entries.push({ ...data.running, end: Date.now() });
  console.log(`Stopped "${data.running.task}"`);
  data.running = null;
  await save(data);
}

export async function status() {
  const { running } = await load();
  if (!running) return console.log("Nothing is running.");
  const minutes = Math.round((Date.now() - running.start) / 60000);
  console.log(`${running.task} - ${minutes} min`);
}

export async function report({ week, csv }) {
  const { entries } = await load();
  const since = week ? Date.now() - 7 * 864e5 : new Date().setHours(0, 0, 0, 0);
  const totals = {};
  for (const e of entries.filter((e) => e.start >= since)) {
    totals[e.task] = (totals[e.task] ?? 0) + (e.end - e.start);
  }
  const rows = Object.entries(totals).map(([task, ms]) => [task, (ms / 36e5).toFixed(2)]);
  if (csv) {
    console.log("task,hours");
    for (const [task, hours] of rows) console.log(`"${task.replaceAll('"', '""')}",${hours}`);
  } else {
    console.table(Object.fromEntries(rows.map(([task, hours]) => [task, { hours }])));
  }
}
''')
    w(r / "test/commands.test.js", '''\
import { test } from "node:test";
import assert from "node:assert/strict";

test("placeholder", () => assert.ok(true));
''')
    w(r / "docs/install.md", '''\
# Install from source

```bash
git clone https://github.com/example-org/tasklog.git
cd tasklog
npm link
```

`npm link` puts the `tasklog` command on your PATH.
''')
    w(r / "LICENSE", '''\
                    GNU GENERAL PUBLIC LICENSE
                       Version 3, 29 June 2007

 Copyright (C) 2007 Free Software Foundation, Inc. <https://fsf.org/>
 Everyone is permitted to copy and distribute verbatim copies
 of this license document, but changing it is not allowed.

                            Preamble

  The GNU General Public License is a free, copyleft license for
software and other kinds of works.

  [Remaining text of the GPL-3.0 omitted in this fixture.]
''')
    w(r / "README.md", '''\
# TaskLog

Welcome to TaskLog! In today's fast-paced world, developers juggle more tasks than ever
before, and keeping track of where your time goes has never been more important. Studies
show that people underestimate their time by up to 50%. That's why we built TaskLog, a
revolutionary, blazing-fast and incredibly simple time tracking solution that will
transform the way you work forever.

### Installation

Just install it globally:

```
$ npm install -g task-log
```

Then run it:

```
$ npm start
```

### Usage

Adding time is easy:

```
$ tasklog add "Write report" 2h
$ tasklog list
```

Your data is saved in `~/.tasklog/data.json`.

For more setup options see [the setup guide](docs/setup.md).

## License

MIT
''')
    w(r / ".gitignore", "node_modules/\n")
    git_init(r, remote="https://github.com/example-org/tasklog.git", tag="v1.2.0")
