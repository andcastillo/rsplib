from setuptools import setup, find_packages

setup(name='rsplib',
      version='0.2.6',
      description='RSP python library',
      url='https://github.com/riccardotommasini/rsplib',
      author='Riccardo Tommasini',
      author_email='riccardo.tommasini@polimi.it',
      license='MIT',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False)