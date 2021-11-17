from pathlib import Path

from setuptools import find_packages, setup


HERE = Path(__file__).parent.resolve()


def parse_requirements_txt():
    req_txt_path = HERE / "requirements.txt"
    lines = [line.strip() for line in req_txt_path.read_text().splitlines()]
    return [
        line.partition("#")[0].rstrip()  # strip trailing comments
        for line in lines
        if all(
            (
                line,  # strip empty lines
                not line.startswith("#"),  # strip comment lines
                not line.startswith("git+ssh"),  # strip git+ssh lines
                "==" in line,  # only keep pinned dependencies
            )
        )
    ]


# Basic setup() for the package; we specify dependencies using pip-tools; see
# README.md for more information.
setup(
    name="aioniser",
    version="0.0.1",
    description="Aioniser, a tool for trigger things in cycles",
    author="Andy Gimblett",
    author_email="andy.gimblett@estima-sci.com",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    python_requires=">=3.9, <4",
    install_requires=parse_requirements_txt(),
    entry_points={
        'console_scripts': [
            'aioniser = aioniser.scripts.aioniser:main',
        ],
    },
)
