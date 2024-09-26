import pytest
import coverage


cov = coverage.Coverage(
    source_pkgs=["rivet_transpiler"],
    omit=[
        "dynamical_decoupling.py",
        "transpile_part.py"
    ])

cov.start()

exit_code = pytest.main([
    '--verbosity=2',
    '--failed-first',
    '--exitfirst',
    # '--capture=no',
    # '--collect-only',
    # '--durations=0',

    'tests/test_transpiler.py',
    # 'tests/test_functions.py',
    # 'tests/test_stacks.py',
    # 'tests/test_metrics.py',
])

cov.stop()
cov.save()

cov.report(show_missing=True, skip_empty=True)

# cov.html_report(directory='coverage_report_html')

quit(exit_code)
