from setuptools import setup, find_packages

setup(
    name='pyconfigvars',
    version='v0.1',
    author='Reynold Tabuena',
    author_email='rynldtbuen@gmail.com',
    description=(
        '''
        Transform and simplify configuration variables.
        '''
    ),
    license='MIT',
    packages=find_packages(),
    classifiers=[
        'Programming Language :: Python :: 3.5',
        'License :: OSI Approved :: MIT License',
    ],
)
