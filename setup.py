#!/usr/bin/env python3

# Copyright (C) 2018 Friedrich Miescher Institute for Biomedical Research

from setuptools import setup

### This is from iotop setup.py
# Dirty hack to make setup.py install the iotop script to sbin/ instead of bin/
# while still honoring the choice of installing into local/ or not.
#if hasattr(distutils_install, 'INSTALL_SCHEMES'):
#	for d in distutils_install.INSTALL_SCHEMES.itervalues():
#		if d.get('scripts', '').endswith('/bin'):
#			d['scripts'] = d['scripts'][:-len('/bin')] + '/sbin'

setup(
	name = 'splitrsync',
	version = '0.2',
	description = 'Split rsync across multuple processes',
	long_description = 'Split rsync across multuple processes',
	author = 'Enrico Tagliavini',
	author_email = 'enrico.tagliavini@fmi.ch',
	url = '',
	packages = ['splitrsync'],
	license = '',
	platforms = 'linux',

        # nothing this is pure python only using the standard library
	#install_requires = [''],

	scripts = [
		'src/splitrsync',
	],
	zip_safe = False,
)

