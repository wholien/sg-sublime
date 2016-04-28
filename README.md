# Sourcegraph Live Sublime Plugin

## Overview

The Sourcegraph Sublime Plugin allows you to view Go definitions in real-time on [sourcegraph.com](http://www.sourcegraph.com) as you code, so you can stay focused on what's important: your code. When your cursor is on a certain Go symbol, it should load in a live channel in your browser:

![Sourcegraph Live Sublime Plugin](images/setup.jpg)

## Setup

1. The plugin assumes `godef` is installed in the `bin` folder of one of your `GOPATH` workspaces. If you don't already have `godef` installed, run the following command:

	`go get -u github.com/rogpeppe/godef`

2. Clone the `sg-sublime` plugin into your Sublime Text 3 Package folder:

 	OSX:

 		git clone https://github.com/luttig/sg-sublime ~/Library/Application\ Support/Sublime\ Text\ 3/Packages/sg-sublime

	Linux:

 		git clone https://github.com/luttig/sg-sublime ~/.config/sublime-text-3/Packages/sg-sublime

3. Open `Sourcegraph.sublime-settings` by clicking `Sublime Text > Preferences > Package Settings > Sourcegraph > Settings - User`, and add your GOPATH and GOROOT as follows:

	```json
	{
		"GOPATH": "/path/to/gopath",
		"GOROOT": "/usr/local/go"
	}
	```

	Similarly, if you want to try the plugin on a local Sourcegraph server, you can define its base URL in this file using the key `SG_BASE_URL`.

## Usage

The plugin should automatically open a browser tab to initialize your live session when in Go files. If, for any reason, your tab gets closed, press <kbd>&#8984;</kbd>+<kbd>.</kbd>, <kbd>&#8984;</kbd>+<kbd>0</kbd> in any file to reopen the Sourcegraph live tab. Alternatively, you can click on `Sublime Text > Preferences > Package Settings > Sourcegraph > Reopen Browser Tab`. As you navigate through Go files, your browser should automatically load the definition and references for recognized symbols.

## Support

The Sourcegraph Live Sublime Plugin has currently only been tested using Mac OS X and Sublime Text 3.