from setuptools import setup, find_packages

setup(
    name = 'kvm_monitor',
    version = '0.0.1',
    keywords = ('monitor', 'kvm'),
    description = 'nvs monitor for kvm',
    license = 'NetEase',

    url = 'http://www.163.com',
    author = 'Wangpan',
    author_email = 'hzwangpan@corp.netease.com',

    packages = find_packages(),
    include_package_data = True,
    platforms = 'any',
    install_requires = ['requests', 'oslo.config'],
)
