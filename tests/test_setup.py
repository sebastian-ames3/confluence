"""
Placeholder test to ensure CI pipeline passes during Phase 0 setup.
This test will be replaced with real tests in Phase 1+.
"""
import pytest


def test_project_setup():
    """Verify basic project setup is complete."""
    # Verify project structure exists
    import os

    # Check key directories exist
    assert os.path.exists('agents'), "agents/ directory should exist"
    assert os.path.exists('collectors'), "collectors/ directory should exist"
    assert os.path.exists('backend'), "backend/ directory should exist"
    assert os.path.exists('database'), "database/ directory should exist"
    assert os.path.exists('frontend'), "frontend/ directory should exist"
    assert os.path.exists('tests'), "tests/ directory should exist"
    assert os.path.exists('scripts'), "scripts/ directory should exist"
    assert os.path.exists('config'), "config/ directory should exist"
    assert os.path.exists('docs'), "docs/ directory should exist"


def test_required_files_exist():
    """Verify required configuration files exist."""
    import os

    assert os.path.exists('README.md'), "README.md should exist"
    assert os.path.exists('CHANGELOG.md'), "CHANGELOG.md should exist"
    assert os.path.exists('requirements.txt'), "requirements.txt should exist"
    assert os.path.exists('.gitignore'), ".gitignore should exist"
    assert os.path.exists('.env.example'), ".env.example should exist"
    assert os.path.exists('railway.json'), "railway.json should exist"


def test_documentation_exists():
    """Verify key documentation files exist."""
    import os

    assert os.path.exists('docs/CLAUDE.md'), "docs/CLAUDE.md should exist"
    assert os.path.exists('docs/PRD_MASTER.md'), "docs/PRD_MASTER.md should exist"
    assert os.path.exists('docs/PRD-001.md'), "docs/PRD-001.md should exist"
    assert os.path.exists('docs/PRD-002.md'), "docs/PRD-002.md should exist"
    assert os.path.exists('docs/PRD-003.md'), "docs/PRD-003.md should exist"
    assert os.path.exists('docs/PRD-004.md'), "docs/PRD-004.md should exist"


def test_python_packages_initialized():
    """Verify Python packages have __init__.py files."""
    import os

    assert os.path.exists('agents/__init__.py'), "agents/__init__.py should exist"
    assert os.path.exists('collectors/__init__.py'), "collectors/__init__.py should exist"
    assert os.path.exists('backend/__init__.py'), "backend/__init__.py should exist"
    assert os.path.exists('tests/__init__.py'), "tests/__init__.py should exist"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
