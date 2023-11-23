from setuptools import setup, find_packages

setup(
  name="halpert",
  version="0.0.1",
  author="David Fant",
  author_email="david@fant.io",
  description="A Python library for evaluating AI agents",
  long_description=open("README.md", "r").read(),
  long_description_content_type="text/markdown",
  url="https://github.com/davidfant/halpert",
  packages=find_packages(),
  python_requires='>=3.6',
  install_requires=[
    "pydantic",
  ],
)