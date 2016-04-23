# Sourcegraph Live Sublime Plugin

The Sourcegraph Sublime Plugin allows you to view Go definitions in real-time on [sourcegraph.com](http://www.sourcegraph.com) as you code, so you never have to leave your editor.

## Overview

We recommend you watch the [demo screencast]() to see potential use cases for the plugin.

## Setup

 1. First, navigate to the Sublime Text Packages directory (this can be found in Sublime by clicking `Sublime Text > Preferences > Browse Packages...`) and clone the `sg-sublime` plugin:

 	`git clone https://github.com/luttig/sg-sublime`

 2. Open `Sourcegraph.sublime-settings` by clicking `Sublime Text > Preferences > Package Settings > Sourcegraph > Settings - User`, and add your GOPATH and GOROOT as follows:

```json
{
	"GOPATH": "/path/to/gopath",
	"GOROOT": "/usr/local/go"
}
```

 3. 

 ## Usage

The plugin should automatically open a browser tab to initialize your live session. If, for any reason, your tab gets closed, press &#8984;+., &#8984;+0 in any file to reopen the Sourcegraph live tab. As you navigate through Go files, the tab should automatically load the definition and references for recognized variables.