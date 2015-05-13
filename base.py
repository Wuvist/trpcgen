#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import traceback

from ptsd import ast
from ptsd.loader import Loader
from Cheetah.Template import Template
from os import path, mkdir
import traceback

namespace = ""
thrift_file = ""


def init_module(module):
	module.consts = []
	module.typedef = []
	module.enums = []
	module.structs = []
	module.services = []

	for node in [i for i in module.values() if isinstance(i, ast.Typedef)]:
		node.go_type = type_translate(node.type)
		module.typedefs.append(node)
		typedef[str(node.name)] = node.type

	for node in module.values():
		if not isinstance(node, ast.Node):
			continue
		if isinstance(node, ast.Enum):
			module.enums.append(node)
		elif isinstance(node, ast.Const):
			module.consts.append(transform_const(node))
		elif isinstance(node, ast.Struct):
			module.structs.append(node)
		elif isinstance(node, ast.Service):
			module.services.append(node)

	## process enum labels
	for obj in module.enums:
		obj.labels = {}
		for i in obj.values:
			label_anno = [j.value for j in i.annotations if j.name.value == "label"]
			if len(label_anno) == 0:
				obj.labels[i.tag] = '"%s"' % i.name
			else:
				obj.labels[i.tag] = label_anno[0]

def load_thrift(thrift_idl):
	global thrift_file, namespace
	thrift_file = thrift_idl
	try:
		loader = Loader(thrift_idl, lambda x: x)
		if loader.namespace == "":
			print 'general namespace not found, please add `namespace * XXXX` to ' + thrift_file + " and retry"
			sys.exit(1)

		loader.namespace = str(loader.namespace)
		namespace = loader.namespace

		for module in loader.modules.values():
			init_module(module)
	except Exception, e:
		print "error", thrift_file
		traceback.print_exc()
		raise e
	return loader
