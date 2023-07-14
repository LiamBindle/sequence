from setuptools import setup
import versioneer
setup(
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
)
