from setuptools import setup, find_packages

setup(
    name="ghostscale-gui",
    version="0.1.0",
    packages=find_packages(),
    install_requires=["kivy", "pyyaml"],
    entry_points={
        "gui_scripts": [
            "ghostscale-gui = ghostscale_gui.main:main"
        ]
    },
)