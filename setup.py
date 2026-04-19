"""Package setup for cronwrap."""
from setuptools import find_packages, setup

setup(
    name="cronwrap",
    version="0.1.0",
    description="A lightweight CLI wrapper that adds logging, alerting, and retry logic to any cron job.",
    author="cronwrap contributors",
    python_requires=">=3.8",
    packages=find_packages(exclude=["tests*"]),
    install_requires=[],
    extras_require={
        "dev": [
            "pytest>=7",
            "pytest-cov",
        ]
    },
    entry_points={
        "console_scripts": [
            "cronwrap=cronwrap.cli:main",
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: System :: Systems Administration",
        "Topic :: Utilities",
    ],
)
