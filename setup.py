import setuptools

setuptools.setup(
    name="mopidy-client",
    version="0.0.1",
    license='Apache License, Version 2.0',
    author="Andrew Bates",
    author_email="abates@omeganetserv.com",
    description="A Websocket based JSON-RPC client for Mopidy",
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    url="https://github.com/abates/mopidy-client",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        "tornado>=6.0",
        "Pypubsub>=4.0",
    ],
    python_requires='>=3.7',
)
