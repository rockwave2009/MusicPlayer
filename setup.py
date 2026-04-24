from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="professional-music-player",
    version="2.0",
    author="Music Player Team",
    author_email="musicplayer@example.com",
    description="一款专业的macOS音乐播放器软件",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/example/professional-music-player",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: MacOS",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Multimedia :: Sound/Audio :: Players",
    ],
    python_requires=">=3.9",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "musicplayer=main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["resources/icons/*", "resources/themes/*", "resources/translations/*"],
    },
)