"""Offline self-test of the harness and the suites' mechanical checks. Spends no model usage.

Usage: python selftest.py [--quick] [--suite <name>]

Runs unit tests (statistics, verdict validation, path scrubbing,
version-control fingerprints), each suite's evals/<suite>/check_cases.json
against its suite_checks.py, and, unless --quick, a full fake round of the
commit-message suite: prep, run (with testdata/fake_claude.py standing in for
Claude Code, including failures and retries), blind, judge, collect,
aggregate, checks, usage, trigger test, and an archive round trip. Everything
happens in a temporary work directory. Run it before any paid round and after
changing the harness or a suite's checks.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
TMP = Path(tempfile.mkdtemp(prefix="lisa-selftest-"))
os.environ["LISA_EVAL_WORK"] = str(TMP / "work")
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
sys.dont_write_bytecode = True
sys.path.insert(0, str(HERE))

import evalenv  # noqa: E402  (after LISA_EVAL_WORK is set)
import stats  # noqa: E402
from blind import scrub  # noqa: E402
from fixture import ENV, w  # noqa: E402

ONLY_SUITE, ARGS = evalenv.split_flag(sys.argv[1:], "--suite")
QUICK, ARGS = evalenv.pop_switch(ARGS, "--quick")
if ARGS or (ONLY_SUITE is not None and ONLY_SUITE not in evalenv.suites()):
    raise SystemExit(f"{__doc__}\n--suite must be one of: {', '.join(evalenv.suites())}")
FAKE = HERE / "testdata" / "fake_claude.py"


def script(name, *args, env=None, check=True):
    """Run a harness script with the fake CLI; return (exit code, output)."""
    full_env = dict(os.environ, CLAUDE_BIN=str(FAKE), **(env or {}))
    proc = subprocess.run([sys.executable, str(HERE / name), *args], cwd=HERE, env=full_env, capture_output=True,
                          text=True, encoding="utf-8", errors="replace")
    out = proc.stdout + proc.stderr
    if check and proc.returncode != 0:
        raise AssertionError(f"{name} {' '.join(args)} exited {proc.returncode}:\n{out}")
    return proc.returncode, out


class Units(unittest.TestCase):
    def test_sign_test_and_paired(self):
        self.assertAlmostEqual(stats.sign_test(8, 1), 0.0390625)
        r = stats.paired([0.5, 0.4, 0.6, 0.5])
        self.assertEqual((r["wins"], r["losses"]), (4, 0))
        self.assertGreater(r["low"], 0)
        self.assertIn("inconclusive", stats.paired_line("b - a", [0.3, -0.3, 0.1]))

    def test_verdict_problems(self):
        weights = {"A": 3, "B": 2}
        good = {"X": {"scores": {"A": 5, "B": 4}, "errors": []}, "Y": {"scores": {"A": 3, "B": 3}},
                "ranking": ["X", "Y"]}
        self.assertEqual(evalenv.verdict_problems(good, ["X", "Y"], weights), [])
        bad = json.loads(json.dumps(good))
        bad["Y"]["scores"]["B"] = "3"
        bad["X"]["errors"] = [{"severity": "Major"}]
        bad["ranking"] = ["X", "X"]
        problems = evalenv.verdict_problems(bad, ["X", "Y"], weights)
        self.assertEqual(len(problems), 3, problems)
        self.assertEqual(evalenv.verdict_problems({"X": good["X"]}, ["X", "Y"], weights, ranking=False),
                         ["Y: no scores"])

    def test_read_json_encodings(self):
        folder = TMP / "enc"
        folder.mkdir(parents=True, exist_ok=True)
        for name, encoding in (("a.json", "utf-16"), ("b.json", "utf-8-sig"), ("c.json", "utf-8")):
            (folder / name).write_text(json.dumps({"k": name}), encoding=encoding)
            self.assertEqual(evalenv.read_json(folder / name), {"k": name})
        self.assertEqual(evalenv.read_json(folder / "missing.json"), {})

    def test_scrub(self):
        cases = {
            r"B:\Temp\lisa-evals\cm\runs\r1\c1-shipcalc\B\shipcalc\x.py": "<run-dir>",
            "/b/Temp/lisa-evals/cm/runs/r1/c1-shipcalc/B/shipcalc": "<run-dir>",
            "see runs/r1/c1-shipcalc/B/shipcalc/README.md": "<run-dir>",
            "compared with ../B/shipcalc": "<run-dir>/shipcalc",
            "C:/w/skill-snapshots/cand/commit-message/SKILL.md": "<instructions-dir>",
        }
        for text, marker in cases.items():
            out = scrub(text, "r1", "c1-shipcalc", "B")
            self.assertIn(marker, out, text)
            self.assertNotIn("/B/", out.replace("\\", "/"), text)
        url = "https://github.com/o/r/actions/runs/42/jobs/7/logs"
        self.assertEqual(scrub(url, "r1", "c1-shipcalc", "B"), url)

    def test_vcs_fingerprint(self):
        repo = TMP / "vcs" / "repo"
        w(repo / "a.txt", "a\n")
        for args in (["init", "-q", "-b", "main"], ["add", "-A"], ["commit", "-q", "-m", "init"]):
            subprocess.run(["git", *args], cwd=repo, env=ENV, check=True, capture_output=True)
        for mutation in (["tag", "v1"], ["branch", "other"], ["remote", "add", "origin", "https://x.invalid/r.git"],
                         ["update-index", "--assume-unchanged", "a.txt"], ["config", "user.name", "Someone"]):
            copy = TMP / "vcs" / ("m-" + mutation[0])
            shutil.copytree(repo, copy)
            subprocess.run(["git", *mutation], cwd=copy, env=ENV, check=True, capture_output=True)
            self.assertIn("CHANGED", evalenv.vcs_report(repo, copy), mutation)
        same = TMP / "vcs" / "same"
        shutil.copytree(repo, same)
        self.assertNotIn("CHANGED", evalenv.vcs_report(repo, same))
        gone = TMP / "vcs" / "gone"
        shutil.copytree(repo, gone)
        evalenv.force_rmtree(gone / ".git")
        self.assertEqual(evalenv.vcs_report(repo, gone), "vcs checkout: REMOVED\n")


def case_tests(suite_name):
    """One test per suite: every case in check_cases.json gives the expected check results."""
    def test(self):
        cases_file = evalenv.EVALS / suite_name / "check_cases.json"
        if not cases_file.exists():
            self.skipTest(f"{suite_name} has no check_cases.json")
        work = TMP / "cases"
        script("build_scenarios.py", suite_name, env={"LISA_EVAL_WORK": str(work)})
        code = (
            "import json, shutil, subprocess, sys, evalenv\n"
            "from checks import RunContext\n"
            f"suite = evalenv.Suite({suite_name!r})\n"
            "from suite_checks import CHECKS\n"
            "fails = []\n"
            "for i, case in enumerate(json.loads((suite.dir / 'check_cases.json').read_text(encoding='utf-8'))):\n"
            "    scen = case['scenario']\n"
            "    arm = suite.work / 'runs' / 'cases' / scen / f'k{i}'\n"
            "    folder = arm / evalenv.folder_of(scen)\n"
            "    shutil.copytree(suite.work / 'scenarios' / scen, folder, symlinks=True)\n"
            "    for rel, text in (case.get('files') or {}).items():\n"
            "        (folder / rel).parent.mkdir(parents=True, exist_ok=True)\n"
            "        (folder / rel).write_text(text, encoding='utf-8', newline='\\n')\n"
            "    for rel in case.get('deleted') or []:\n"
            "        (folder / rel).unlink()\n"
            "    if case.get('vcs_changed'):\n"
            "        if (folder / '.git').exists():\n"
            "            subprocess.run(['git', '-c', 'user.name=x', '-c', 'user.email=x@example.invalid', 'commit',\n"
            "                            '-q', '--allow-empty', '-m', 'case'], cwd=folder, env=evalenv.SESSION_ENV,\n"
            "                           check=True, capture_output=True)\n"
            "        else:\n"
            "            listing = subprocess.run(['svn', 'ls', '-R'], cwd=folder, env=evalenv.SESSION_ENV,\n"
            "                                     check=True, capture_output=True, text=True).stdout.split()\n"
            "            target = next(f for f in listing if not f.endswith('/'))  # a versioned file\n"
            "            subprocess.run(['svn', 'changelist', 'case', target], cwd=folder,\n"
            "                           env=evalenv.SESSION_ENV, check=True, capture_output=True)\n"
            "    (arm / 'notes.md').write_text(case.get('notes', ''), encoding='utf-8')\n"
            "    meta = {'status': 'ok', 'subtype': 'success', 'is_error': False, 'denials': [], 'commands': []}\n"
            "    meta.update(case.get('meta') or {})\n"
            "    (arm / 'meta.json').write_text(json.dumps(meta), encoding='utf-8')\n"
            "    try:\n"
            "        got = CHECKS[scen](RunContext(suite, scen, arm))\n"
            "    except Exception as exc:\n"
            "        fails.append(f\"{scen} [{case['name']}]: crashed: {exc!r}\")\n"
            "        continue\n"
            "    for check, want in case['expect'].items():\n"
            "        value = got.get(check, '<missing>')\n"
            "        if value != want:\n"
            "            fails.append(f\"{scen} [{case['name']}]: {check} expected {want} got {value}\")\n"
            "print('\\n'.join(fails))\n"
            "sys.exit(1 if fails else 0)\n"
        )
        env = dict(os.environ, LISA_EVAL_WORK=str(work))
        proc = subprocess.run([sys.executable, "-c", code], cwd=HERE, env=env, capture_output=True, text=True,
                              encoding="utf-8", errors="replace")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
    return test


class SuiteCases(unittest.TestCase):
    pass


for _name in evalenv.suites():
    if ONLY_SUITE in (None, _name):
        setattr(SuiteCases, f"test_cases_{_name.replace('-', '_')}", case_tests(_name))


class FakeRound(unittest.TestCase):
    """A whole round of the commit-message suite against the fake CLI."""

    suite = "commit-message"
    only = "c1-shipcalc,c6-todo-cli,c10-reports,c14-pressline,c16-inventory"

    @classmethod
    def setUpClass(cls):
        if QUICK:
            raise unittest.SkipTest("--quick")
        cls.work = Path(os.environ["LISA_EVAL_WORK"]) / cls.suite
        script("build_scenarios.py", cls.suite)
        script("snapshot_skill.py", cls.suite, "head", "--ref", "HEAD")

    def test_round(self):
        s, only = self.suite, self.only
        script("prep_runs.py", s, "r1", "A", "B", "--only", only)
        code, out = script("run_arms.py", s, "r1", "A=none", "B=head", "--only", only, "--jobs", "4",
                           env={"FAKE_CLAUDE_MODES": "c6-todo-cli/B=error,c10-reports/A=denial"}, check=False)
        self.assertEqual(code, 1, out)
        self.assertIn("--retry-failed", out)
        failed = self.work / "runs/r1/c6-todo-cli/B"
        self.assertTrue((failed / "failed-result.md").exists())
        self.assertFalse((failed / "notes.md").exists())
        code, out = script("blind.py", s, "r1", "A", "B", check=False)
        self.assertEqual(code, 1, out)
        self.assertIn("c6-todo-cli: B: error", out)
        _, out = script("run_arms.py", s, "r1", "A=none", "B=head", "--only", only, "--retry-failed")
        self.assertIn("skip c1-shipcalc/A: done (ok)", out)
        meta = json.loads((failed / "meta.json").read_text(encoding="utf-8"))
        self.assertEqual((meta["status"], meta["usage"]["cache_read"], meta["models"]), ("ok", 3000, ["claude-fake-1"]))
        _, out = script("blind.py", s, "r1", "A", "B")
        mapping = json.loads((self.work / "runs/r1/mapping.json").read_text(encoding="utf-8"))
        self.assertEqual(set(mapping), set(only.split(",")))
        changes = [p.read_text(encoding="utf-8") for p in (self.work / "blind/r1/c10-reports").glob("*/changes.txt")]
        self.assertTrue(any("denied attempts:\n  git add -A" in c for c in changes), changes)
        _, out = script("judge.py", s, "r1", "--jobs", "3")
        self.assertIn("5 of 5 scenarios judged", out)
        _, out = script("judge.py", s, "r1")  # resumes: nothing left to judge
        self.assertIn("skip c1-shipcalc: already judged", out)
        _, out = script("collect.py", s, "r1")
        self.assertIn("5 of 5 scenarios judged", out)
        self.assertIn("token use and cost by round", out)
        _, out = script("aggregate.py", s, "r1:A=none,B=head")
        self.assertIn("head - none: n=5", out)
        _, out = script("checks.py", s, "r1", "--json", str(TMP / "full.json"))
        _, out = script("usage.py", s)
        self.assertIn("r1", out)
        self.assertIn("judge", out)
        # A tagged pairwise re-judge resolves its own mapping.
        script("blind.py", s, "r1", "B", "A", "--tag", "rj")
        script("judge.py", s, "r1-rj")
        _, out = script("aggregate.py", s, "r1:A=none,B=head", "r1-rj:A=none,B=head")
        self.assertIn("n=10", out)
        # Re-blinding keeps labels and replaces the whole scenario folder: no stale label survives.
        stale = self.work / "blind/r1-rj/c1-shipcalc/Z"
        stale.mkdir()
        script("blind.py", s, "r1", "B", "A", "--tag", "rj", "--only", "c1-shipcalc")
        self.assertFalse(stale.exists())
        self.assertTrue((self.work / "judgments/r1-rj/c1-shipcalc.json").exists())  # same content: not stale
        # Invalid verdicts fail loudly and never replace a valid one.
        code, out = script("judge.py", s, "r1", "--only", "c1-shipcalc", "--retries", "0", "--rejudge",
                           env={"FAKE_CLAUDE_MODE": "bad_verdict"}, check=False)
        self.assertEqual(code, 1, out)
        self.assertIn("an earlier verdict was kept", out)
        # A judgments folder of another blind set is never reused, and no blind set takes its name.
        code, out = script("judge.py", s, "r1", "--out", "r1-rj", check=False)
        self.assertEqual(code, 1, out)
        self.assertIn("holds verdicts of blind set r1-rj", out)
        script("judge.py", s, "r1", "--out", "r1-noise", "--only", "c1-shipcalc")
        code, out = script("blind.py", s, "r1", "B", "A", "--tag", "noise", check=False)
        self.assertEqual(code, 1, out)
        self.assertIn("judgments/r1-noise holds verdicts of blind set r1", out)
        # Another judge model is not 'already judged'.
        _, out = script("judge.py", s, "r1", "--only", "c1-shipcalc", "--model", "sonnet")
        self.assertNotIn("already judged", out)
        # A prepared but unrun round adds no sessions to the usage report.
        script("prep_runs.py", s, "r9", "A", "--only", "c1-shipcalc")
        _, out = script("usage.py", s)
        self.assertNotIn("r9", out)
        # A refused rebuild keeps both the scenarios and the SVN repositories run copies point at.
        prints_file = self.work / "runs/r1/scenarios.json"
        original = prints_file.read_text(encoding="utf-8")
        tampered = json.loads(original)
        tampered["c10-reports"]["tree"] = "0" * 64
        prints_file.write_text(json.dumps(tampered), encoding="utf-8")
        code, out = script("build_scenarios.py", s, check=False)
        prints_file.write_text(original, encoding="utf-8")
        self.assertEqual(code, 1, out)
        self.assertIn("scenarios/ is unchanged", out)
        self.assertTrue((self.work / "svn-repos/c10-reports").is_dir())
        self.assertFalse((self.work / "svn-repos.bak").exists())
        # Archive round trip into a separate root: Git checkouts survive, and slim checks match full checks.
        archive = TMP / "archive.zip"
        script("export_archive.py", s, str(archive))
        restored = TMP / "restored"
        with zipfile.ZipFile(archive) as zf:
            zf.extractall(restored / s)
        env = {"LISA_EVAL_WORK": str(restored)}
        script("checks.py", s, "r1", "--json", str(TMP / "slim.json"), env=env)
        full = json.loads((TMP / "full.json").read_text(encoding="utf-8"))
        slim = json.loads((TMP / "slim.json").read_text(encoding="utf-8"))
        self.assertEqual(full, slim)
        _, out = script("collect.py", s, "r1", env=env)
        self.assertIn("5 of 5 scenarios judged", out)
        _, out = script("blind.py", s, "r1", "A", "B", "--tag", "again", env=env)
        self.assertIn("c16-inventory", out)

    def test_failures(self):
        s, only = self.suite, "c1-shipcalc,c2-notes-api,c3-csvtool"
        script("prep_runs.py", s, "r2", "A", "B", "--only", only)
        modes = "c1-shipcalc/A=sleep,c2-notes-api/A=nonjson,c3-csvtool/A=max_turns"
        code, out = script("run_arms.py", s, "r2", "A=none", "B=head", "--only", only, "--timeout", "3",
                           env={"FAKE_CLAUDE_MODES": modes}, check=False)
        self.assertEqual(code, 1, out)
        status = {scen: json.loads((self.work / f"runs/r2/{scen}/A/meta.json").read_text(encoding="utf-8"))["status"]
                  for scen in only.split(",")}
        self.assertEqual(status, {"c1-shipcalc": "timeout", "c2-notes-api": "no_result", "c3-csvtool": "max_turns"})
        code, out = script("run_arms.py", s, "r2", "A=none", "B=head", "--only", only, "--model", "opus",
                           check=False)
        self.assertIn("settings differ", out)
        code, out = script("blind.py", s, "r2", "A", "B", check=False)
        self.assertEqual(code, 1, out)
        self.assertIn("blinded: c3-csvtool", out)
        changes = "".join(p.read_text(encoding="utf-8") for p in (self.work / "blind/r2/c3-csvtool").glob("*/*.txt"))
        self.assertIn("stopped at the turn limit", changes)
        code, out = script("judge.py", s, "r2", "--retries", "1", env={"FAKE_CLAUDE_MODE": "no_verdict"}, check=False)
        self.assertEqual(code, 1, out)
        self.assertIn("FAILED after 2 attempt(s)", out)
        code, out = script("judge.py", s, "r2", "--retries", "0", env={"FAKE_CLAUDE_MODE": "error"}, check=False)
        self.assertEqual(code, 1, out)
        _, out = script("judge.py", s, "r2")
        self.assertIn("1 of 1 scenarios judged", out)

    def test_trigger(self):
        code, out = script("trigger_test.py", self.suite, "head", "--jobs", "4",
                           env={"FAKE_CLAUDE_MODES": "trigger/q0=error"}, check=False)
        self.assertEqual(code, 1, out)
        self.assertIn("ERR", out)
        results = json.loads((self.work / "trigger-results-head.json").read_text(encoding="utf-8"))
        self.assertEqual(sum(r["meta"]["status"] != "ok" for r in results), 1)
        self.assertTrue(all("skill_calls" in r for r in results if r["status"] == "ok"))


def main():
    loader = unittest.TestLoader()
    tests = unittest.TestSuite([loader.loadTestsFromTestCase(c) for c in (Units, SuiteCases, FakeRound)])
    outcome = unittest.TextTestRunner(verbosity=2).run(tests)
    evalenv.force_rmtree(TMP)
    sys.exit(0 if outcome.wasSuccessful() else 1)


if __name__ == "__main__":
    main()
