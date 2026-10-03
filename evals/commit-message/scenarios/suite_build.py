"""Build the sixteen commit-message scenarios (called by evals/harness/build_scenarios.py)."""
import git_scenarios
import svn_scenario

BUILDERS = [git_scenarios.build_c1, git_scenarios.build_c2, git_scenarios.build_c3,
            git_scenarios.build_c4, git_scenarios.build_c5, git_scenarios.build_c6,
            git_scenarios.build_c7, git_scenarios.build_c8, git_scenarios.build_c9,
            svn_scenario.build_c10, git_scenarios.build_c11, git_scenarios.build_c12,
            git_scenarios.build_c13, svn_scenario.build_c14, git_scenarios.build_c15,
            git_scenarios.build_c16]


def build_all(base, ref):
    return [build(base) for build in BUILDERS]
