import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="ptlib",
    version="0.0.5",
    author="Joseph Whelan",
    author_email="",
    description="This library aims to provide efficient implementation and detaile debugging of solutions to problems in the asynchronous domain.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/jfw225/ptlib",
    project_urls={
        "Bug Tracker": "https://github.com/jfw225/ptlib/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    install_requires=[
        "numpy>=1.19.5",
        "matplotlib>=3.4.3"
    ],
    python_requires=">=3.8",
)