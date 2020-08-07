from setuptools import setup, find_packages

setup(name='singtcommon',
      version='0.10.0',
      packages=["singtcommon"],
      include_package_data=True,
      install_requires=[
          "numpy",
          "twisted"
      ]
)
