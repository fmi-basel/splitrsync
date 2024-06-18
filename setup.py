#!/usr/bin/env python3

# Copyright (C) 2020 Friedrich Miescher Institute for Biomedical Research

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

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
	version = '0.2.4',
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

