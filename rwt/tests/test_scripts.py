from __future__ import unicode_literals

import os
import textwrap
import sys
import subprocess

from rwt import scripts


def test_pkg_imported(tmpdir):
	"""
	Create a script that loads cython and ensure it runs.
	"""
	body = textwrap.dedent("""
		import path
		print("Successfully imported path.py")
		""").lstrip()
	script_file = tmpdir / 'script'
	script_file.write_text(body, 'utf-8')
	pip_args = ['path.py']
	cmd = [sys.executable, '-m', 'rwt'] + pip_args + ['--', str(script_file)]

	out = subprocess.check_output(cmd, universal_newlines=True)
	assert 'Successfully imported path.py' in out


class TestDepsReader:
	def test_reads_files_with_attribute_assignment(self):
		script = textwrap.dedent('''
			__requires__=['foo']
			x.a = 'bar'
			''')
		assert scripts.DepsReader(script).read() == ['foo']

	def test_reads_files_with_multiple_assignment(self):
		script = textwrap.dedent('''
			__requires__=['foo']
			x, a = [a, x]
			''')
		assert scripts.DepsReader(script).read() == ['foo']

	def test_single_dep(self):
		script = textwrap.dedent('''
			__requires__='foo'
			''')
		assert scripts.DepsReader(script).read() == ['foo']

	def test_index_url(self):
		script = textwrap.dedent('''
			__requires__ = ['foo']
			__index_url__ = 'https://my.private.index/'
			''')
		reqs = scripts.DepsReader(script).read()
		assert reqs.index_url == 'https://my.private.index/'

	def test_dependency_links(self):
		script = textwrap.dedent('''
			__requires__ = ['foo==0.42']
			__dependency_links__ = ['git+ssh://git@example.com/repo.git#egg=foo-0.42']
			''')
		reqs = scripts.DepsReader(script).read()
		assert reqs.dependency_links == [
			'git+ssh://git@example.com/repo.git#egg=foo-0.42']


def test_pkg_loaded_from_alternate_index(tmpdir):
	"""
	Create a script that loads cython from an alternate index
	and ensure it runs.
	"""
	body = textwrap.dedent("""
		__requires__ = ['path.py']
		__index_url__ = 'https://devpi.net/root/pypi/+simple/'
		import path
		print("Successfully imported path.py")
		""").lstrip()
	script_file = tmpdir / 'script'
	script_file.write_text(body, 'utf-8')
	cmd = [sys.executable, '-m', 'rwt', '--', str(script_file)]

	out = subprocess.check_output(cmd, universal_newlines=True)
	assert 'Successfully imported path.py' in out
	assert 'devpi.net' in out


def test_pkg_loaded_from_dependency_links(tmpdir):
	"""
	Create a script whose dependency is only installable
	from a custom dependency link and ensure it runs.
	"""
	dependency = tmpdir.ensure_dir('barbazquux-1.0')
	(dependency / 'setup.py').write_text(textwrap.dedent(
		'''
		from setuptools import setup
		setup(
			name='barbazquux', version='1.0',
			py_modules=['barbazquux'],
		)
		'''
	), 'utf-8')
	(dependency / 'barbazquux.py').write_text('', 'utf-8')
	dependency_link = 'file://%s#egg=barbazquux-1.0' % (
		dependency.strpath.replace(os.path.sep, '/'),
	)
	body = textwrap.dedent("""
		__requires__ = ['barbazquux']
		__dependency_links__ = [{dependency_link!r}]
		import barbazquux
		print("Successfully imported barbazquux.py")
		""").lstrip().format(
		dependency_link=dependency_link
	)
	script_file = tmpdir.ensure_dir('script_dir') / 'script'
	script_file.write_text(body, 'utf-8')
	cmd = [sys.executable, '-m', 'rwt', '--no-index', '--', str(script_file)]
	out = subprocess.check_output(cmd, universal_newlines=True)
	assert 'Successfully imported barbazquux.py' in out
