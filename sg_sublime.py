import os
import re
import random
import logging
import subprocess

import sublime_plugin
import sublime

import urllib.parse
import urllib.request

import datetime

settings = sublime.load_settings('Sourcegraph.sublime-settings')

SOURCEGRAPH_BASE_URL = settings.get('SG_BASE_URL', 'http://sourcegraph.com') #TODO change for production
SOURCEGRAPH_LOG_FILE = settings.get('SG_LOG_FILE', '/tmp/sourcegraph-sublime.log')
logging.basicConfig(filename=SOURCEGRAPH_LOG_FILE, level=logging.DEBUG)

GOPATH = settings.get('GOPATH', '~/go')
GOROOT = settings.get('GOROOT', '/usr/local/go')

SOURCEGRAPH_CHANNEL = None

def get_channel():
	global SOURCEGRAPH_CHANNEL
	if SOURCEGRAPH_CHANNEL == None:
		SOURCEGRAPH_CHANNEL = '%s-%06x%06x%06x%06x%06x%06x' % (os.environ.get('USER'), \
			random.randrange(16**6), random.randrange(16**6), random.randrange(16**6), \
			random.randrange(16**6), random.randrange(16**6), random.randrange(16**6))
	else:
		logging.info('Using existing channel: %s' % SOURCEGRAPH_CHANNEL)

def open_live_channel():
	get_channel()
	command = ['open', '%s/-/live/%s' % (SOURCEGRAPH_BASE_URL, SOURCEGRAPH_CHANNEL)]
	logging.info('[open_live] Opening live channel in browser: %s' % command)
	subprocess.Popen(command)

class SgOpenLiveCommand(sublime_plugin.WindowCommand):
	def run(self):
		open_live_channel()

class SgOpenLogCommand(sublime_plugin.WindowCommand):
	def run(self):
		self.window.open_file(SOURCEGRAPH_LOG_FILE)

class SgDocCommand(sublime_plugin.EventListener):
	def __init__(self):
		super().__init__()
		global SOURCEGRAPH_CHANNEL
		SOURCEGRAPH_CHANNEL = None
		self.HAVE_OPENED_LIVE_CHANNEL = False
		self.godefpath = os.path.join(GOPATH, "bin", 'godef')
		self.env = os.environ.copy()
		self.env['GOPATH'] = GOPATH
		self.last_var_lookup = None
		self.last_repo_package_lookup = None
		logging.debug('env: %s' % str(self.env))

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
		logging.debug('[go list] Command output: %s' % golist_output.decode())
		return golist_output.decode().split('\n')[0]

	def cursor_offset(self):
		string_before = self.view.substr(sublime.Region(0, self.view.sel()[0].begin()))
		string_before.encode('utf-8')
		buffer_before = bytearray(string_before, encoding="utf8")
		return str(len(buffer_before))

	def run_godef(self, view):
		godef_args = [self.godefpath, '-i', '-o', self.cursor_offset(), '-t']
		logging.info('[godef] Running shell command: %s' % ' '.join(godef_args))

		godef_process = subprocess.Popen(godef_args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=self.env)
		godef_output, stderr = godef_process.communicate(input=str.encode(view.substr(sublime.Region(0, view.size()))))

		if stderr:
			logging.info('[godef] No definition found, returning. Message: %s' % stderr.decode())
		else:
			logging.info("[godef] Output: " + godef_output.decode())
		return stderr, godef_output

	def issue_live_update(self, variable, repo_package):
		post_url = '%s/.api/live/%s' % (SOURCEGRAPH_BASE_URL, SOURCEGRAPH_CHANNEL)
		payload_url = '%s/-/golang?repo=%s&pkg=%s&def=%s' % (SOURCEGRAPH_BASE_URL, repo_package, repo_package, variable)
		logging.info('[curl] Sending payload URL: %s' % payload_url)
		logging.debug('[curl] Sending post request to %s' % post_url)
		curl_command = ['curl', '-XPOST', '-d', '{"Action":{"URL":"%s"},"CheckForListeners":true}' % (payload_url), '%s/.api/live/%s' % (SOURCEGRAPH_BASE_URL, SOURCEGRAPH_CHANNEL)]
		subprocess.Popen(curl_command)

	def on_selection_modified_async(self, view):
		if view.file_name() == None:
			return
		if not view.file_name().endswith("go"):
			return
		self.view = view

		stderr, godef_output = self.run_godef(view)

		if stderr or godef_output.decode() == '':
			return

		if not self.HAVE_OPENED_LIVE_CHANNEL:
			open_live_channel()
			self.HAVE_OPENED_LIVE_CHANNEL = True

		variable = godef_output.decode().split('\n')[1].split()[0]
		if variable == 'type':
			variable = godef_output.decode().split('\n')[1].split()[1]

		logging.debug('[godef] Variable identified: %s' % variable)

		repo_package = self.get_repo_package(godef_output.decode().split(':')[0])
		logging.debug('[go list] Path to repo/package: %s' % repo_package)

		if repo_package != self.last_repo_package_lookup or variable != self.last_var_lookup:
			self.last_var_lookup = variable
			self.last_repo_package_lookup = repo_package
			self.issue_live_update(variable, repo_package)