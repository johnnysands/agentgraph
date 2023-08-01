from setuptools import setup

readme = ""
with open("README.md") as f:
    readme = f.read()
    readme = readme.split("\n")
    readme = [line for line in readme if "<img" not in line]
    readme = "\n".join(readme)

setup(
    name="agentgraph",
    version="0.0.3",
    description="A simple graph-based execution engine for Python",
    long_description=readme,
    long_description_content_type="text/markdown",
    url="https://github.com/johnnysands/agentgraph",
    author="Johnny Sands",
    author_email="johnnysands@users.noreply.github.com",
    license="MIT",
    packages=["agentgraph"],
    install_requires=[],
    readme="README.md",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows",
    ],
)
