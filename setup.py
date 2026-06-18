from setuptools import setup, find_packages

with open("requirements.txt") as f:
    install_requires = f.read().strip().split("\n")

setup(
    name="tag_order",
    version="0.0.1",
    description="Asset Tag Order Management for Centurisk",
    author="Neil Fitzpatrick",
    author_email="neil.fitzpatrick@centurisk.com",
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    install_requires=install_requires,
)
