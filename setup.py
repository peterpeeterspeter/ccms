#!/usr/bin/env python3
"""
CCMS Setup Script
================

Installs the ccms command globally for the single entry point.
"""

from setuptools import setup, find_packages

setup(
    name="ccms",
    version="1.0.0",
    description="CCMS Native LangChain Casino Review Pipeline",
    author="CrashCasino.io",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "click>=8.0.0",
        "langchain>=0.1.0",
        "langchain-core>=0.1.0",
        "langchain-openai>=0.1.0",
        "pydantic>=2.0.0",
        "supabase>=2.0.0",
        "requests>=2.28.0",
        "aiohttp>=3.8.0",
        "python-dotenv>=1.0.0",
    ],
    entry_points={
        "console_scripts": [
            "ccms=cli:cli",
        ],
    },
    python_requires=">=3.10",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)