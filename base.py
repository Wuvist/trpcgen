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

java_types = {
	"bool": "boolean",
	"i32": "int",
	"string": "String"
}

java_ref_types = {
	"bool": "Boolean",
	"i32": "Integer",
	"string": "String"
}

def to_java_type(type_str):
	if java_types.has_key(type_str):
		return java_types[type_str]

	if type_str.startswith("list<"):
		return "java.util.ArrayList<" + to_java_type(type_str[5:-1]) + ">"
	return type_str

def to_java_ref_type(type_str):
	if java_ref_types.has_key(type_str):
		return java_ref_types[type_str]

	if type_str.startswith("list<"):
		return "java.util.ArrayList<" + to_java_ref_type(type_str[5:-1]) + ">"
	return type_str

def extend_field(field):
	def type_java():
		type_str = str(field.type)
		return to_java_type(type_str)
	def type_java_ref():
		type_str = str(field.type)
		return to_java_ref_type(type_str)

	field.type_java = type_java

def extend_struct(obj):
	def get_name():
		return obj.name.value
	obj.get_name = get_name 

	for field in obj.fields:
		extend_field(field)

def extend_func(func):
	# final String originCode, final int offset, final int limit, final Listener<ArrayList<TCollection>> listener

	def get_java_params():
		params = []
		for p in func.arguments:
			params.append("final %s %s" % (to_java_type(str(p.type)), p.name))

		return_type = to_java_ref_type(str(func.type))
		if return_type != "void":
			params.append("final Listener<%s> listener" % (return_type))
		return ", ".join(params)
	func.get_java_params = get_java_params

	def get_java_return_type():
		return to_java_ref_type(str(func.type))
	func.get_java_return_type = get_java_return_type


def extend_service(obj):
	def get_name():
		return obj.name.value
	obj.get_name = get_name

	for func in obj.functions:
		extend_func(func)

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
			extend_service(node)
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
