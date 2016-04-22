import os
import re
import random
import logging
import subprocess

import sublime_plugin
import sublime

import urllib.parse
import urllib.request

SOURCEGRAPH_BASE_URL = 'http://localhost:3080' #TODO change for production
SOURCEGRAPH_LOG_FILE = os.path.join(sublime.packages_path(), 'User', 'Sourcegraph', 'sourcegraph-sublime.log')
GOPATH = os.getenv('GOPATH', '/Users/john/Documents/junior/sourcegraph/gowork') #TODO generalize
GOROOT = os.getenv('GOROOT', '/usr/local/go')

class SgOpenLogCommand(sublime_plugin.WindowCommand):
	def run(self, log):
		self.window.open_file(os.path.join(sublime.packages_path(), 'User', 'Sourcegraph', log))

class SgDocCommand(sublime_plugin.TextCommand):
	def __init__(self, _):
		super().__init__(_)
		logging.basicConfig(filename=SOURCEGRAPH_LOG_FILE, level=logging.DEBUG)
		self.HAVE_OPENED_LIVE_CHANNEL = False
		self.SOURCEGRAPH_CHANNEL = None
		self.settings = sublime.load_settings('Sourcegraph.sublime-settings')
		self.godefpath = os.path.join(GOPATH, "bin", 'godef')
		self.env = os.environ.copy()
		self.env['GOPATH'] = GOPATH
		logging.debug('env: %s' % str(self.env))

	def useShell(self):
		return False if os.name != "posix" else True

	def get_channel(self):
		if self.SOURCEGRAPH_CHANNEL == None:
			self.SOURCEGRAPH_CHANNEL = '%s-%06x%06x%06x%06x%06x%06x' % (os.environ.get('USER'),\
				random.randrange(16**6), random.randrange(16**6), random.randrange(16**6), \
				random.randrange(16**6), random.randrange(16**6), random.randrange(16**6))
		else:
			logging.info('Using existing channel: %s' % self.SOURCEGRAPH_CHANNEL)
			
	def open_live_channel(self):
		self.get_channel()
		command = 'open %s/-/live/%s' % (SOURCEGRAPH_BASE_URL, self.SOURCEGRAPH_CHANNEL)
		logging.info('Opening live channel in browser: %s' % command)
		subprocess.Popen(command, shell=self.useShell())

	def live_action_callback(self, r, *args, **kwargs):
		log.debug('Live action status code: %i' % r.status_code)
		if (r.status_code == 200):
			pass # TODO if 408, open tab again - blocked by julien

	def get_repo_package(self, package_path):
		package_dir = os.path.dirname(package_path)
		logging.debug('[godef] Package directory: %s' % package_dir)
		current_dir = os.path.dirname(self.view.file_name())
		logging.debug('[godef] Current directory: %s' % current_dir)

		rel_path = './%s' % (os.path.relpath(package_dir, current_dir))
		golist_command = ['%s/bin/go' % GOROOT, 'list', '-e', rel_path]
		logging.info('[go list] Issuing command: %s' % ' '.join(golist_command))
		golist_process = subprocess.Popen(golist_command, cwd=current_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=self.env)
		golist_output, stderr = golist_process.communicate()
		logging.debug('[go list] Command output: %s' % str(golist_output))

		return str(golist_output).split('\\')[0].split("'")[1] # strip away subprocess junk

	def cursor_offset(self):
		string_before = self.view.substr(sublime.Region(0, self.view.sel()[0].begin()))
		string_before.encode('utf-8')
		buffer_before = bytearray(string_before, encoding="utf8")
		return str(len(buffer_before))

	def run_godef(self):
		godef_args = [self.godefpath, '-f', self.view.file_name(), '-o', self.cursor_offset(), '-t']
		logging.info('[Godef] Running shell command: %s' % ' '.join(godef_args))

		godef_process = subprocess.Popen(godef_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=self.env)
		godef_output, stderr = godef_process.communicate()
		if stderr:
			logging.info('[godef] ERROR: no definition found: %s' % str(stderr))
		return godef_output

	def issue_live_update(self, variable, repo_package):
		post_url = '%s/.api/live/%s' % (SOURCEGRAPH_BASE_URL, self.SOURCEGRAPH_CHANNEL)
		payload_url = '%s/-/golang?repo=%s&pkg=%s&def=%s' % (SOURCEGRAPH_BASE_URL, repo_package, repo_package, variable)
		logging.info('[curl] Sending payload URL: %s' % payload_url)
		logging.debug('[curl] Sending post request to %s' % post_url)
		curl_command = 'curl -XPOST -d \'{"Action":{"URL":"%s"},"CheckForListeners":true}\' http://localhost:3080/.api/live/%s' % (payload_url, self.SOURCEGRAPH_CHANNEL)
		subprocess.Popen(curl_command, shell=self.useShell)

	def run(self, _):
		if not self.HAVE_OPENED_LIVE_CHANNEL:
			self.open_live_channel()
			self.HAVE_OPENED_LIVE_CHANNEL = True

		godef_output = self.run_godef()

		variable = str(godef_output).split('\\n')[1].split()[0]
		logging.debug('[godef] Variable identified: %s' % variable)

		repo_package = self.get_repo_package(str(godef_output).split(':')[0].split("'")[1])
		logging.debug('[go list] Path to repo/package: %s' % repo_package)

		self.issue_live_update(variable, repo_package)