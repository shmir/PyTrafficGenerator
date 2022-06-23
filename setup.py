#!/usr/bin/env python
# encoding: utf-8
"""
Package PyTrafficGenerator for distribution.
"""
from setuptools import find_packages, setup


def main() -> None:
    """Package script."""
    with open("requirements.txt", "r") as requirements:
        install_requires = requirements.read().splitlines()
    with open("README.md", "r") as readme:
        long_description = readme.read()

    setup(
        name="pytrafficgen",
        description="Base Python OO API package to automate traffic generators (Spirent, Ixia, Xena etc.)",
        url="https://github.com/shmir/PyTrafficGenerator/",
        use_scm_version={"root": ".", "relative_to": __file__, "local_scheme": "node-and-timestamp"},
        license="Apache Software License",
        author="Yoram Shamir",
        author_email="yoram@ignissoft.com",
        platforms="any",
        install_requires=install_requires,
        packages=find_packages(include=["trafficgenerator"]),
        include_package_data=True,
        long_description=long_description,
        long_description_content_type="text/markdown",
        keywords="ixia spirent xena trex byteblower l2l3 l47 test automation",
        classifiers=[
            "Development Status :: 5 - Production/Stable",
            "Natural Language :: English",
            "License :: OSI Approved :: Apache Software License",
            "Intended Audience :: Developers",
            "Operating System :: OS Independent",
            "Topic :: Software Development :: Testing",
            "Programming Language :: Python :: 3.7",
            "Programming Language :: Python :: 3.8",
            "Programming Language :: Python :: 3.9",
        ],
    )


if __name__ == "__main__":
    main()
