"""Setup configuration for backward compatibility."""

from setuptools import setup, find_packages

setup(
    name="policyboom",
    use_scm_version=False,
    packages=find_packages(),
    python_requires=">=3.11",
)
