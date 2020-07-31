from setuptools import setup, find_packages

setup(name='singtcommon',
      version='0.6.0',
      packages=["singtcommon"],
      include_package_data=True,
      install_requires=[
          "numpy",
          "twisted"
      ]
)
