import pytest
import coverage


cov = coverage.Coverage(
    source_pkgs=["qml_transpiler"],
    omit=[
        "topological_compression.py",
        "dynamical_decoupling.py",
        "transpile_part.py"
    ])

cov.start()

pytest.main([
    '--verbosity=2', 
    # '--exitfirst', 
    '--failed-first',
    # '--capture=no', 
    # '--collect-only',
    # '--durations=0',
    
    # 'test_transpiler.py',
    # 'test_stacks.py',
])

cov.stop()
cov.save()

cov.report(show_missing=True, skip_empty=True)

cov.html_report(directory='html_coverage_report')