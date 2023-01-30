from setuptools import setup

setup(
    name='iris-veloquarantine-module',
    python_requires='>=3.9',
    version='0.1.0',
    packages=['iris_veloquarantine_module', 'iris_veloquarantine_module.veloquarantine_handler'],
    url='https://github.com/socfortress/iris-veloquarantine-module',
    license='MIT',
    author='SOCFortress',
    author_email='info@socfortress.co',
    description='`iris-veloquarantine-module` is a IRIS pipeline/processor module created with https://github.com/dfir-iris/iris-skeleton-module',
    install_requires=[]
)
