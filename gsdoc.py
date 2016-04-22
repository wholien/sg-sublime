import sys
import os

st2 = (sys.version_info[0] == 2)
dist_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, dist_dir)

from gosubl import gs
from gosubl import gsq
from gosubl import mg9
import re
import sublime
import sublime_plugin

DOMAIN = 'GsDoc'

GOOS_PAT = re.compile(r'_(%s)' % '|'.join(gs.GOOSES))
GOARCH_PAT = re.compile(r'_(%s)' % '|'.join(gs.GOARCHES))
EXT_EXCLUDE = [
	'out', 'exe', 'o', 'dll', 'so', 'a', 'dynlib', 'lib', 'com', 'bin', 'pyc', 'pyo', 'cache', 'db',
	'bak', 'png', 'gif', 'jpeg', 'jpg', 'gz', 'zip', '7z', 'rar', 'tar', '1', '2', '3', 'old', 'tgz',
	'pprof', 'prof', 'mem', 'cpu', 'swap',
]

class SgDocCommand(sublime_plugin.TextCommand):
	def is_enabled(self):
		return gs.is_go_source_view(self.view)

	def show_output(self, s):
		gs.show_output(DOMAIN+'-output', s, False, 'GsDoc')

	def run(self, _, mode=''):
		view = self.view
		if (not gs.is_go_source_view(view)) or (mode not in ['goto', 'hint']):
			return

		pt = gs.sel(view).begin()
		src = view.substr(sublime.Region(0, view.size()))
		pt = len(src[:pt].encode("utf-8"))
		def f(docs, err):
			doc = ''
			if err:
				self.show_output('// Error: %s' % err)
			elif docs:
				if mode == "goto":
					fn = ''
					flags = 0
					print("DOCS = " + str(docs))
					if len(docs) > 0:
						d = docs[0]
						print("DOC = " + str(d))
						fn = d.get('fn', '')
						row = d.get('row', 0)
						col = d.get('col', 0)

						package = d.get('pkg', 0)
						name = d.get('name', 0)
						print("PKG = " + str(package))
						print("NAME = " + str(name))

						if fn:
							gs.println('opening %s:%s:%s' % (fn, row, col))
							gs.focus(fn, row, col)
							return
					self.show_output("%s: cannot find definition" % DOMAIN)
				elif mode == "hint":
					s = []
					for d in docs:
						print("NAME = " + name)
						if name:
							kind = d.get('kind', '')
							pkg = d.get('pkg', '')
							if pkg:
								name = '%s.%s' % (pkg, name)
							src = d.get('src', '')
							if src:
								src = '\n//\n%s' % src
							doc = '// %s %s%s' % (name, kind, src)

						s.append(doc)
					doc = '\n\n\n'.join(s).strip()
			self.show_output(doc or "// %s: no docs found" % DOMAIN)

		mg9.doc(view.file_name(), src, pt, f)
