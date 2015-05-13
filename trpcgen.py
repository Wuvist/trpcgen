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
parser.add_argument('-l', '--lang', metavar='lang', type=str, choices=["java"],
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
	"java": ".java"
}

def handle_struct(module, loader):
	for obj in module.structs:
		tpl_path = os.path.join('tpl', args.lang, "struct.%s_tpl" % args.lang)

		tpl = open(tpl_path, 'r').read().decode("utf8")
		t = Template(tpl, searchList=[{"loader": loader, "obj": obj}])
		code = str(t)
		out_path = os.path.join(args.output_folder_path, "gen_" + obj.name.value + lang_ext[args.lang])
		write_file(out_path, code)

def handle_service(module, loader):
	for service in module.services:
		print service.name
		for f in service.functions:
			print f

	# if len(module.consts) > 0:
	# 	tpl = open('tmpl/go_const.tmpl', 'r').read()
	# 	t = Template(tpl, searchList=[{"namespace": namespace, "objs": module.consts}])
	# 	if not path.exists(out_path + namespace):
	# 		mkdir(out_path + namespace)
	# 	with open(out_path + "%s/gen_%s_const.go" % (namespace, namespace), "w") as fp:
	# 		fp.write(str(t))

	# if len(module.enums) > 0:
	# 	tpl = open('tmpl/go_enum.tmpl', 'r').read()
	# 	t = Template(tpl, searchList=[{
	# 		"namespace": namespace,
	# 		"objs": module.enums,
	# 		"name": filename,
	# 	}])
	# 	if not path.exists(out_path + namespace):
	# 		mkdir(out_path + namespace)
	# 	with open(out_path + "%s/gen_%s_enum.go" % (namespace, namespace), "w") as fp:
	# 		fp.write(str(t))

def main(thrift_idl):
	loader = base.load_thrift(thrift_idl)
	# tpl = open('tmpl/go_package.tmpl', 'r').read()
	# t = Template(tpl, searchList=[{"namespace": namespace}])
	# code = unicode(t)
	# if not path.exists(out_path + namespace):
	# 	mkdir(out_path + namespace)
	# with open(out_path + namespace + '/gen_init.go', "w") as fp:
	# 	fp.write(code)

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
