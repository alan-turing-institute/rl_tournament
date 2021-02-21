import os
import setuptools

# Get dependencies from requirements.txt
SETUP_DIR = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(SETUP_DIR, "requirements.txt"), "r") as f:
    REQUIRED_PACKAGES = f.read().splitlines()

setuptools.setup(
    name="battleground",
    version="0.0.1",
    license="MIT",
    install_requires=REQUIRED_PACKAGES,
    packages=setuptools.find_packages(),
)
