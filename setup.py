import setuptools
import ibm_ocp_appsim_cli

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="ibm-ocp-appsim-cli",
    version=ibm_ocp_appsim_cli.__version__,
    author="The ocpappsim crew",
    author_email="daniel.michel@de.ibm.com",
    description="OCP AppSim CLI",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.ibm.com/spectrum-fusion/ocpappsim",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    install_requires=[
        "Click",
        "openshift",
        "requests",
        "texttable",
        "urllib3",
    ],
    entry_points={
        'console_scripts': [
            'ocpappsim = ibm_ocp_appsim_cli.commands:cli',
        ],
    },
)
