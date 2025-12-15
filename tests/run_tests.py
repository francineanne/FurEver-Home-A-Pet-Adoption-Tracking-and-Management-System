import io
import os
import sys
import trace
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

GREEN = "\033[92m"
RESET = "\033[0m"
RED = "\033[91m"


class QuietResult(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.successes = []

    # Silence the default dot output while tracking passes
    def addSuccess(self, test):
        self.successes.append(test)

    def addFailure(self, test, err):
        super().addFailure(test, err)

    def addError(self, test, err):
        super().addError(test, err)


class QuietRunner(unittest.TextTestRunner):
    def __init__(self, *args, **kwargs):
        super().__init__(resultclass=QuietResult, stream=io.StringIO(), verbosity=0, *args, **kwargs)


def discover_suite():
    return unittest.defaultTestLoader.discover("tests", pattern="test_*.py")


def run_with_coverage(suite):
    """
    Prefer coverage.py if available; fall back to running without coverage.
    """
    try:
        import coverage  # type: ignore
    except ImportError:
        return None, None

    cov = coverage.Coverage(source=["app"])
    cov.start()
    result = QuietRunner().run(suite)
    cov.stop()
    cov.save()

    buf = io.StringIO()
    total = cov.report(file=buf, show_missing=False)
    report_text = buf.getvalue().strip()
    return result, (report_text, total)


def run_without_coverage(suite):
    tracer = trace.Trace(count=True, trace=False, ignoredirs=[sys.prefix, sys.exec_prefix])
    result = tracer.runfunc(QuietRunner().run, suite)
    results = tracer.results()

    # Approximate coverage for files under app/
    app_root = os.path.abspath(os.path.join(ROOT, "app"))
    counts = results.counts
    executed = {}
    for (filename, lineno), _ in counts.items():
        fname = os.path.abspath(filename)
        if not fname.startswith(app_root):
            continue
        executed.setdefault(fname, set()).add(lineno)

    total_lines = 0
    total_hit = 0
    for fname, hits in executed.items():
        try:
            with open(fname, "r", encoding="utf-8") as f:
                lines = f.readlines()
        except OSError:
            continue
        total_lines += len(lines)
        total_hit += len(hits)

    percent = (total_hit / total_lines * 100) if total_lines else 0.0
    return result, percent


def main():
    suite = discover_suite()

    result = None
    coverage_report = None

    result, coverage_report = run_with_coverage(suite)
    if result is None:
        # coverage.py not installed; run tests only
        result, approx_percent = run_without_coverage(suite)
        print(f"Approximate coverage (trace, app/): {approx_percent:.1f}%")
        print("Install `pip install coverage` for detailed coverage reporting.")

    # Print passed tests in green
    for test in result.successes:
        print(f"{GREEN}[PASS]{RESET} {test.id()}")

    if result.failures or result.errors:
        for test, _ in result.failures:
            print(f"{RED}[FAIL]{RESET} {test.id()}")
        for test, _ in result.errors:
            print(f"{RED}[ERROR]{RESET} {test.id()}")
        sys.exit(1)

    if coverage_report:
        report_text, total = coverage_report
        print("\nCoverage summary (source=app)")
        print(report_text)
        print(f"Total coverage: {total:.1f}%")


if __name__ == "__main__":
    main()
