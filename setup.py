import os
import shutil

from setuptools import setup, find_packages
from setuptools.command.install import install
from setuptools.command.test import test

version = '1.2.0'


class InstallScripts(install):
    """
    install scripts
    """

    def run(self):
        install.run(self)


class TestCommand(test):
    """
    test cases
    """

    def run_tests(self):
        os.system("py.test-%s %s" % (3, "tests"))


s = setup(name='atune_collector',
          version=version,
          description="The tool for data collection and analysis",
          classifiers=[],
          keywords='collection analysis',
          url='',
          license='MulanPSL-2.0',
          packages=find_packages(".", exclude=['tests']),
          data_files=[('/etc/atune_collector', ['atune_collector/collect_data.json',
                                                'atune_collector/plugin/configurator/bootloader/grub2.json'])],
          include_package_data=True,
          zip_safe=False,
          install_requires=['dict2xml'],
          cmdclass={
              'install': InstallScripts,
              'test': TestCommand,
          },
          )
if 'install' in s.command_obj:
    src_dir = "atune_collector/scripts"
    dst_dir = os.path.join(s.command_obj['install'].install_lib, src_dir)
    shutil.rmtree(dst_dir, ignore_errors=True)
    shutil.copytree(src_dir, dst_dir)
    os.system("chmod -R 750 %s" % dst_dir)
