#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (C) 2015-2017 Datto, Inc.
# Copyright (C) 2020 Neal Gompa
#
# Fedora-License-Identifier: GPLv2+
# SPDX-2.0-License-Identifier: GPL-2.0+
# SPDX-3.0-License-Identifier: GPL-2.0-or-later
#
# This program is free software.
# For more information on the license, see COPYING.
# For more information on free software, see
# <https://www.gnu.org/philosophy/free-sw.en.html>.

# Originally grabbed from: https://www.pagure.io/obs-packaging-scripts
# Script to pull source from a Dist-Git server to push to OBS to trigger builds.
# Note that this script is intentionally designed to be generic and usable
# for both public and private Dist-Git/OBS instances.

import argparse
import glob
import pathlib
import shutil
import subprocess
import sys
import os
import tempfile

# modules provided by osc
import osc.conf
import osc.core
# modules provided by pygit2
import pygit2

# Set up argument parser
parser = argparse.ArgumentParser(description="Pull sources from Dist-Git and push to an OBS instance")

# Declare arguments

# Git server URL (note lack of trailing / and use of HTTPS)
parser.add_argument("-r", "--repo-server", help="Git Server URL", dest="git_server_addr", default="https://src.fedoraproject.org")

# Git repository path and branch
parser.add_argument("-g", "--git-repo-prefix", help="Git repository namespace prefix", dest="git_repo_prefix", default="rpms")
parser.add_argument("-n", "--git-repo-name", help="Git repository name", dest="git_repo_name", required=True)
parser.add_argument("-b", "--git-repo-branch", help="Git repository branch", dest="git_repo_branch", default="main")

# Open Build Service server URL (note lack of trailing / and use of HTTPS)
parser.add_argument("-t", "--obs-server", help="Open Build Service API address", dest="obs_server_addr", default="https://api.opensuse.org")

# OBS authentication token
#parser.add_argument("-u", "--obs-login-user", help="Open Build Service login user", dest="obs_auth_user", required=True)
#parser.add_argument("-k", "--obs-login-password", help="Open Build Service login password", dest="obs_auth_pass", required=True)

# OBS project and package
parser.add_argument("-s", "--obs-project-space", help="Open Build Service project space", dest="obs_project", required=True)
parser.add_argument("-p", "--obs-project-package", help="Open Build Service project package", dest="obs_package", required=True)

# Setup packages in OBS if they don't exist
parser.add_argument("-c", "--create-obs-pkg-if-none", help="Create package space in Open Build Service if it doesn't exist", action="store_true")

# Ignore issues with SSL certificates
#parser.add_argument("-i", "--insecure", help="Ignore issues with HTTPS (self signed certs, etc.)", action="store_true")

# Parse the arguments
args = parser.parse_args()

# Configure the Open Build Service Commander
osc.conf.get_config()

# SSL check setting
#obs_ssl_check = "1"
#if args.insecure is True:
#	obs_ssl_check = "0"

# Open Build Service Commander configuration file data
#obs_server_config = f"""
#[general]
#apiurl = {args.obs_server_addr}
#do_package_tracking = 1
#
#
#[{args.obs_server_addr}]
#user = {args.obs_auth_user}
#pass = {args.obs_auth_pass}
#keyring = 0
#sslcertck = {obs_ssl_check}
#"""

obs_newpkg_config = f"""
<package name="{args.obs_package}" project="{args.obs_project}">
  <title>{args.obs_package} for {args.obs_project}</title>
  <description>{args.obs_package} for {args.obs_project} created by jaicaa.
    Sources from {args.git_server_addr}/{args.git_repo_prefix}/{args.git_repo_name}
  </description>
</package>
"""

# Make a temporary config file to set up for using with osc and use it
#with tempfile.NamedTemporaryFile(suffix=".oscrc") as oscconf:
#	oscconf.write(obs_server_config.encode("utf-8"))
#	oscconf.flush()
#	osc.conf.get_config(override_conffile=oscconf.name)

# Check to see if the package space exists on OBS
osc_prj_packagelist = list(osc.core.meta_get_packagelist(args.obs_server_addr, prj=args.obs_project))

if args.obs_package in osc_prj_packagelist:
	print("Package is configured remotely, proceeding to upload...")
else:
	# If it doesn't exist and we are allowing arbitrary package space creation,
	# create the package space and proceed onward
	if args.create_obs_pkg_if_none is True:
		print("Package is not configured remotely, constructing package!")
		osc.core.edit_meta(metatype="pkg", data=obs_newpkg_config, edit=False, apiurl=args.obs_server_addr, path_args=(args.obs_project, args.obs_package))
		print("Package space created, continuing to upload...")
	else:
		print("Package is not configured remotely, exiting!")
		#oscconf.close()
		sys.exit(4)


# Create directory to check out package sources
pkg_checkout_dir = tempfile.mkdtemp(suffix=f"{args.obs_project}-{args.obs_package}")
git_checkout_dir = tempfile.mkdtemp(suffix=f"{args.git_repo_prefix.replace('/',':')}-{args.git_repo_name}")

# Check out the package sources
osc.core.checkout_package(apiurl=args.obs_server_addr, project=args.obs_project, package=args.obs_package, outdir=pkg_checkout_dir)

# Open OBS repo data
osc_working_pkg = osc.core.Package(workingdir=pkg_checkout_dir)

# Purge all tarballs and the _service file
prjfiles = glob.glob(f"{pkg_checkout_dir}/*")

for pf in prjfiles:
	osc_working_pkg.delete_file(pathlib.PurePath(pf).name)

# Get code from Git
git_repository = pygit2.clone_repository(f"{args.git_server_addr}/{args.git_repo_prefix}/{args.git_repo_name}.git", git_checkout_dir, checkout_branch=args.git_repo_branch)

# Get commit hash from tag
repo_commit = git_repository[git_repository.head.target].hex

# Fetch Dist-Git resources
# XXX: There's not a nice API available to do this cleanly, so subprocessing it is :(
if os.path.exists("/usr/bin/fedpkg"):
	try:
		subprocess.run("fedpkg sources", shell=True, cwd=git_checkout_dir, check=True, universal_newlines=True)
	except subprocess.CalledProcessError:
		print("Failed to fetch Dist-Git sources!")
		sys.exit(5)
else:
	print("fedpkg is missing, please install it!")
	sys.exit(6)

# Copy files to OBS checkout


# Send changes to OBS

# Add files
gitfiles = [
	str(gfp.resolve())
	for gfp in pathlib.Path(git_checkout_dir).iterdir()
	if gfp.resolve().is_file()
	and not gfp.name == "sources"
	and not gfp.name.startswith(".")
]

for gf in gitfiles:
	shutil.copy2(gf, pkg_checkout_dir)

prjfiles = glob.glob(f"{pkg_checkout_dir}/*")

for pf in prjfiles:
	try:
		osc_working_pkg.addfile(pathlib.PurePath(pf).name)
	except osc.oscerr.PackageFileConflict:
		print(f"Already tracked {pathlib.PurePath(pf).name}... continuing!")
		pass

# Commit changes
osc_working_pkg.commit(msg=f"Imported {args.git_repo_prefix}/{args.git_repo_name}@{repo_commit}")

# Delete code checkout and temp config files
shutil.rmtree(pkg_checkout_dir)
shutil.rmtree(git_checkout_dir)
#oscconf.close()
