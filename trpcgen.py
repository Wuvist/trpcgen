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
parser.add_argument('thrift_file_path', metavar='thrift_file_path', type=str,
                   help='input thrift file path')
parser.add_argument('output_folder_path', metavar='output_folder_path', type=str,
                   help='out folder path')

args = parser.parse_args()

def main(thrift_idl):
	loader = base.load_thrift(thrift_idl)
	global namespace
	namespace = loader.namespace
	# tpl = open('tmpl/go_package.tmpl', 'r').read()
	# t = Template(tpl, searchList=[{"namespace": namespace}])
	# code = unicode(t)
	# if not path.exists(out_path + namespace):
	# 	mkdir(out_path + namespace)
	# with open(out_path + namespace + '/gen_init.go', "w") as fp:
	# 	fp.write(code)

	for module in loader.modules.values():
		print module

	for module in loader.modules.values():
		print module

main(args.thrift_file_path)
