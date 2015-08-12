#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from ptsd.loader import Loader
from Cheetah.Template import Template
from os import path, mkdir
import os
import argparse

import base

parser = argparse.ArgumentParser(description='Code generation tool for trpc')
parser.add_argument('action', metavar='action', type=str,
                   help='generation action: struct|service|both', choices=["struct", "service", "both"])
parser.add_argument('thrift_file_path', metavar='thrift_file_path', type=str,
                   help='input thrift file path')
parser.add_argument('-l', '--lang', metavar='lang', type=str, choices=["java", "objc", "csharp"],
                   help='language to be generated: java')
parser.add_argument('output_folder_path', metavar='output_folder_path', type=str,
                   help='out folder path')

args = parser.parse_args()

def write_file(fname, content):
	dir = path.dirname(fname)
	if not path.exists(dir):
		os.makedirs(dir)

	with open(fname, "w") as f:
		f.write(content)

lang_ext = {
	"java": [".java"],
	"csharp": [".cs"],
	"objc": [".m", ".h"]
}

base_path = os.path.dirname(os.path.realpath(__file__))

def handle_struct(module, loader):
	fileExts = lang_ext[args.lang]
	def genFile(ext):
		tpl_path = os.path.join(base_path, 'tpl', args.lang, "struct.%s_tpl" % ext[1:])

		tpl = open(tpl_path, 'r').read().decode("utf8")
		t = Template(tpl, searchList=[{"loader": loader, "obj": obj}])
		code = str(t)
		out_path = os.path.join(args.output_folder_path, obj.name.value + ext)
		write_file(out_path, code)

	for obj in module.structs:
		for ext in fileExts:
			genFile(ext)

def handle_service(module, loader):
	fileExts = lang_ext[args.lang]

	def genFile(ext):
		tpl_path = os.path.join(base_path, 'tpl', args.lang, "service.%s_tpl" % ext[1:])

		tpl = open(tpl_path, 'r').read().decode("utf8")
		t = Template(tpl, searchList=[{"loader": loader, "obj": obj}])
		code = str(t)

		if args.lang == "csharp":
			filename = "I" + obj.name.value + "Controller" + ext
		else:
			filename = obj.name.value + "Service" + ext
		out_path = os.path.join(args.output_folder_path, filename)
		write_file(out_path, code)

	for obj in module.services:
		for ext in fileExts:
			genFile(ext)


def main(thrift_idl):
	loader = base.load_thrift(thrift_idl)
	if loader.namespaces.has_key("objc"):
		base.objc_namespace = str(loader.namespaces["objc"])

	if args.lang == None:
		args.lang = "java"

	for module in loader.modules.values():
		if args.action == "struct":
			handle_struct(module, loader)
		elif args.action == "serivce":
			handle_service(module, loader)
		else:
			handle_struct(module, loader)
			handle_service(module, loader)

main(args.thrift_file_path)
