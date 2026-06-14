from setuptools import setup, find_packages

setup(
    name="fable-orchestrator",
    version="1.0.0",
    author="Nick Smith",
    author_email="nick@pointclearadvisory.com",
    description="Open-source Fable-mode execution engine for Hermes Agent",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/iamnickthegeek/fable-orchestrator",
    packages=find_packages(),
    scripts=["scripts/fable_daemon.py"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.10",
    install_requires=[],
    entry_points={
        "console_scripts": [
            "fable=fable_engine.cli:main",
        ],
    },
)
