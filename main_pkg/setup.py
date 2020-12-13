import setuptools


with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="covid_clock_pkg_Joshua_Prout", # Replace with your own username
    version="0.0.1",
    author="Joshua Prout",
    author_email="jnp207@exeter.ac.uk",
    description="A smart alarm clock and notifications hub",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.8',
)