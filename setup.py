#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OpenSeesPy纤维截面GUI项目配置文件
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="openseespy-fiber-section-gui",
    version="1.0.0",
    author="OpenSeesPy GUI Team",
    author_email="team@openseespy.com",
    description="A GUI application for OpenSeesPy fiber section modeling",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/openseespy/fiber-section-gui",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    python_requires=">=3.7",
    install_requires=[
        "openseespy>=1.0.0",
        "PyQt5>=5.15.0",
        "numpy>=1.19.0",
        "pandas>=1.3.0",
        "openpyxl>=3.0.0",
        "matplotlib>=3.3.0",
        "scipy>=1.7.0",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov>=2.0",
            "black>=21.0",
            "flake8>=3.8",
        ],
    },
    entry_points={
        "console_scripts": [
            "openseespy-gui=main:main",
        ],
    },
)