#  config_diff_soso/config_diff_soso/__init__.py
#
#  Copyright 2026 Leon Dionne <ldionne@dridesign.sh.cn>
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#
"""
This script uses debsums to extract the package maintainer's config file for
every package on your system, and compares it to the version on your machine,
saving a copy of each with another file showing the differences between them.
"""
import logging, sys
from argparse import ArgumentParser
from subprocess import run
from pathlib import Path
from shutil import rmtree, copy2
from tempfile import TemporaryDirectory
from datetime import datetime
from socket import gethostname
from rich.console import Console


__version__ = "1.0.2"


def rprint(string):
	if not hasattr(rprint, 'console'):
		rprint.console = Console(highlight = False)
	rprint.console.print(string)

def get_user_confirmation(prompt = 'Are you sure', default_true = False):
	"""
	Prints a description of what the script wants to do and the prompt, then waits
	for the user to press either the 'y' or 'n' key.

	Returns True if user pressed 'y'. If the user presses ENTER, returns the value
	of "default_true".
	"""
	yn = 'Y/n' if default_true else 'y/N'
	while True:
		print(f'  {prompt}? [{yn}] ', end = '')
		key = input()
		if not key:
			print()
			return default_true
		if key.lower() in ('y', 'n'):
			print()
			return key.lower() == 'y'
		print('  (Enter either "y" or "n")', end = '')

def stdrun(args):
	"""
	Returns tuple (returncode, stdout, stderr)
	"""
	rprint('[grey58]' + ' '.join(args) + '[/grey58]')
	cp = run(args, text = True, capture_output = True, check = False)
	return (cp.returncode, cp.stdout.strip(), cp.stderr.strip())

def get_shell(args):
	returncode, stdout, stderr = stdrun(args)
	if returncode == 0:
		return stdout
	raise RuntimeError(stderr)

def run_check(args):
	rprint('[grey58]' + ' '.join(args) + '[/grey58]')
	run(args, check = True)

def get_apt_var(args):
	stdout = get_shell(args)
	return stdout.split('=', 1).pop().strip('\'"')

def get_cache():
	# This command gives the base directory for all the caches
	if not hasattr(get_cache, 'cached_value'):
		get_cache.cached_value = Path('/') / get_apt_var(
			['apt-config', 'shell', 'CACHE', 'Dir::Cache'])
	return get_cache.cached_value

def get_archive():
	# This command gives the path to the archives, starting from the base directory
	if not hasattr(get_archive, 'cached_value'):
		get_archive.cached_value = get_cache() / get_apt_var(
			['apt-config', 'shell', 'ARCHIVES', 'Dir::Cache::archives'])
	return get_archive.cached_value

def dpkg_list():
	return [ line for line in get_shell(['dpkg', '-l']).split('\n') if line.startswith('ii') ]

def installed_packages():
	return [ line.split().pop(1) for line in dpkg_list() ]

def changed_files(package):
	args = ['sudo', 'debsums', '-ce', package]
	returncode, stdout, _ = stdrun(args)
	if returncode == 2:
		return stdout.split('\n')
	return None

def cached_debs(package):
	return [ path for path in get_archive().iterdir() if path.name.startswith(package) ]

def download(package):
	run_check(['sudo', 'apt-get', '-qq', 'install', '--reinstall', '--download-only', package])

def debfiles(package):
	debs = cached_debs(package)
	if not debs:
		download(package)
	return cached_debs(package)

def extract_deb(debfile, tempdir):
	run_check(['dpkg-deb', '--extract', debfile, tempdir])

def main():
	parser = ArgumentParser()
	parser.add_argument('--verbose', '-v', action = 'store_true',
		help = 'Show more detailed debug information')
	parser.epilog = __doc__
	options = parser.parse_args()
	logging.basicConfig(
		level=logging.DEBUG if options.verbose else logging.ERROR,
		format="[%(filename)24s:%(lineno)3d] %(levelname)-8s %(message)s"
	)

	date_string = datetime.now().strftime('%Y-%m-%d-%H-%M')
	root_path = Path(f'{gethostname()}-config-diff-{date_string}')
	if root_path.exists():
		print(f'"{root_path}" exists. Do you want to delete and replace its contents?')
		if not get_user_confirmation():
			return 1
		rmtree(root_path)
	print(f'Saving to "{root_path}"')

	if get_archive().exists():
		print('Apt archives are at:', get_archive())
	else:
		raise RuntimeError('No archive dir found at: ' + str(get_archive()))

	for package in installed_packages():
		changed_filenames = changed_files(package)
		if not changed_filenames:
			continue
		print(f'{package} changed')
		with TemporaryDirectory() as tempdir:
			tempdir_path = Path(tempdir)
			for debfile in debfiles(package):
				extract_deb(str(debfile), tempdir)
			for changed_filename in changed_filenames:
				changed_filename_relative = changed_filename.lstrip('/')
				extracted_path = tempdir_path / changed_filename_relative
				if not extracted_path.exists():
					rprint(f'[red][bold]"{extracted_path}"[/bold] was not found.[/red]')
					rprint('[red]This indicates a very severe error...[/red]')
					rprint('[red]ALL changed files should be in the original package![/red]')
					print()
					continue
				change_dir = root_path / changed_filename_relative
				if not change_dir.exists():
					change_dir.mkdir(parents = True)
				copy2(extracted_path, change_dir / 'original')
				copy2(changed_filename, change_dir / 'yours')
				returncode, stdout, stderr = stdrun(['diff', '--suppress-common-lines',
					str(change_dir / 'original'), str(change_dir / 'yours')])
				if returncode == 1:
					diff_file = change_dir / 'diff'
					diff_file.write_text(stdout)
				else:
					print(f'"diff" reported an error? "{stderr}"')
	return 0

if __name__ == "__main__":
	try:
		sys.exit(main() or 0)
	except KeyboardInterrupt:
		print()
		sys.exit(9)


#  end config_diff_soso/config_diff_soso/__init__.py
