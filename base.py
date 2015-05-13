#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import traceback

from ptsd import ast
from ptsd.loader import Loader
from Cheetah.Template import Template
from os import path, mkdir
import traceback

thrift_file = ""

def extend_field(field):
	def type_java():
		type_str = str(field.type)
		if type_str == "i32":
			return "int"
		if type_str == "string":
			return "String"
		return type_str
	field.type_java = type_java

def extend_struct(obj):
	def get_name():
		return obj.name.value
	obj.get_name = get_name 

	for field in obj.fields:
		extend_field(field)

def init_module(module):
	module.consts = []
	module.enums = []
	module.structs = []
	module.services = []

	for node in module.values():
		if not isinstance(node, ast.Node):
			continue
		if isinstance(node, ast.Enum):
			module.enums.append(node)
		elif isinstance(node, ast.Const):
			module.consts.append(transform_const(node))
		elif isinstance(node, ast.Struct):
			extend_struct(node)
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
	global thrift_file
	thrift_file = thrift_idl
	loader = Loader(thrift_idl, lambda x: x)

	for module in loader.modules.values():
		init_module(module)
	return loader
