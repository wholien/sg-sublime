import os
import re
import random
import logging
import subprocess

import sublime_plugin
import sublime

import urllib.parse
import urllib.request


SOURCEGRAPH_BASE_URL = 'http://localhost:3080'
SOURCEGRAPH_LOG_FILE = '/tmp/sourcegraph-sublime.log'
GOPATH = '/Users/john/Documents/junior/sourcegraph/gowork'

class SgDocCommand(sublime_plugin.TextCommand):
	def __init__(self, _):
		super().__init__(_)
		self.SOURCEGRAPH_CHANNEL = False
		logging.basicConfig(filename=SOURCEGRAPH_LOG_FILE,level=logging.DEBUG)
		self.open_live_channel()
		self.useShell = False if os.name != "posix" else True
		self.settings = sublime.load_settings('Sourcegraph.sublime-settings')

	def get_channel(self):
		if self.SOURCEGRAPH_CHANNEL == False:
			self.SOURCEGRAPH_CHANNEL = "%s-%06x%06x%06x%06x%06x%06x" % (os.environ.get('USER'), random.randrange(16**6), random.randrange(16**6), random.randrange(16**6), random.randrange(16**6), random.randrange(16**6), random.randrange(16**6))
		else:
			logging.info('Using existing channel: %s' % self.SOURCEGRAPH_CHANNEL)
			
	def open_live_channel(self):
		self.get_channel()
		command = 'open %s/-/live/%s' % (SOURCEGRAPH_BASE_URL, self.SOURCEGRAPH_CHANNEL)
		logging.info('Opening live channel in browser, using command: %s' % command)
		# subprocess.Popen(command, shell=self.useShell)

	def live_action_callback(self, r, *args, **kwargs):
		log.debug('Live action status code: %i' % r.status_code)
		if (r.status_code == 200):
			pass # TODO if 408, open tab again - blocked by julien

	def run(self, _, mode=''):
		gopath = self.settings.get('gopath', os.getenv('GOPATH'))
		godefpath = os.path.join('/Users/john/Documents/junior/sourcegraph/gowork', "bin", 'godef') #TODO

		# string_before = self.view.substr(sublime.Region(0, self.view.sel()[0].begin())).encode("utf-8")
		# buffer_before = bytearray(string_before, encoding="utf8")
		# filename = self.view.file_name()
		# offset = len(buffer_before)
		# godef_args = [godefpath, '-f', filename, '-o', str(offset), '-t']
		# logging.info('[Godef] Running shell command: %s' % ' '.join(args))

		filename = self.view.file_name()
		select = self.view.sel()[0]
		string_before = self.view.substr(sublime.Region(0, select.begin())).encode("utf-8")
		buffer_before = bytearray(string_before, encoding="utf8")
		offset = len(buffer_before)
		godef_args = [godefpath, "-f", filename, "-o", str(offset), '-t']
		logging.info('[Godef] Running shell command: %s' % ' '.join(args))

		env = os.environ.copy()
		env['GOPATH'] = GOPATH
		logging.debug('env: %s' % str(env))

		logging.debug('Godef args: %s' % str(godef_args))
		godef_process = subprocess.Popen(godef_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
		output, stderr = godef_process.communicate()
		if stderr:
			logging.error('[Godef] ERROR: no definition found: %s' % str(stderr))

		variable = str(output).split('\\n')[1].split()[0]
		package_dir = os.path.dirname(str(output).split(':')[0].split("'")[1])
		current_dir = os.path.dirname(self.view.file_name())

		logging.debug('[godef] Package directory: %s' % package_dir)
		logging.debug('[godef] Current directory: %s' % current_dir)

		rel_path = './%s' % (os.path.relpath(package_dir, current_dir))
		golist_command = ['/usr/local/go/bin/go', 'list', '-e', rel_path]
		logging.info('[go list] Issuing command: %s' % " ".join(golist_command))
		golist_process = subprocess.Popen(golist_command, cwd=current_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
		output, stderr = golist_process.communicate()
		logging.debug('[go list] Command output: %s' % str(output))

		repo_package = str(output).split('\\')[0].split("'")[1] # strip away subprocess junk

		logging.debug('[go list] Path to repo/package: %s' % repo_package)

		logging.debug('[godef] Variable identified: %s' % variable)

		post_url = '%s/.api/live/%s' % (SOURCEGRAPH_BASE_URL, self.SOURCEGRAPH_CHANNEL)
		payload_url = '%s/-/golang?repo=%s&pkg=%s&def=%s' % (SOURCEGRAPH_BASE_URL, repo_package, variable)
		logging.info('[curl] Sending payload URL: %s' % payload_url)
		logging.debug('[curl] Sending post request to %s' % post_url)
		curl_command = 'curl -XPOST -d --header "Content-Type:application/json" \'{"Action":{"URL":"%s"},"CheckForListeners":true}\' http://localhost:3080/.api/live/%s' % (payload_url, self.SOURCEGRAPH_CHANNEL)
		subprocess.Popen(curl_command, shell=self.useShell)