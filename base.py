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
	"i64": "long",
	"string": "String"
}

objc_types = {
	"i32": "int ",
	"string": "(nonatomic, copy) NSString *"
}

objc_types_for_param = {
	"i32": "int",
	"string": "NSString *"
}

java_ref_types = {
	"bool": "Boolean",
	"i32": "Integer",
	"i64": "Long",
	"string": "String"
}

def to_java_type(type_str):
	if java_types.has_key(type_str):
		return java_types[type_str]

	if type_str.startswith("list<"):
		return "java.util.ArrayList<" + to_java_type(type_str[5:-1]) + ">"
	return type_str

def to_objc_type(type_str):
	if objc_types.has_key(type_str):
		return objc_types[type_str]

	if type_str.startswith("list<"):
		return "NSArray *"
	return type_str + " *"

def to_objc_type_for_param(type_str):
	if objc_types_for_param.has_key(type_str):
		return objc_types_for_param[type_str]

	if type_str.startswith("list<"):
		return "NSArray *"
	return type_str + " *"

def to_java_ref_type(type_str):
	if java_ref_types.has_key(type_str):
		return java_ref_types[type_str]

	if type_str.startswith("list<"):
		return "java.util.ArrayList<" + to_java_ref_type(type_str[5:-1]) + ">"
	return type_str

def extend_field(field):
	type_str = str(field.type)

	def type_java():
		return to_java_type(type_str)
	def type_objc():
		return to_objc_type(type_str)
	def type_java_ref():
		return to_java_ref_type(type_str)

	field.is_list_type = False
	if type_str.startswith("list<"):
		field.is_list_type = True
		field.inner_type_java = to_java_type(type_str[5:-1])

	field.type_java = type_java
	field.type_objc = type_objc

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

	def get_objc_params():
		params = []
		if len(func.arguments) > 0:
			p = func.arguments[0]
			param_type = to_objc_type_for_param(str(p.type))
			params.append("(%s)%s" % (param_type, p.name))

		for p in func.arguments[1:]:
			param_type = to_objc_type_for_param(str(p.type))
			params.append("%s:(%s)%s" % (p.name, param_type, p.name))

		return_type = to_objc_type_for_param(str(func.type))
		if return_type != "void":
			params.append("success:(void (^)(%s))success" % (return_type + "result"))
		return "\n".join(params)
	func.get_objc_params = get_objc_params

	def get_objc_params_for_call():
		params = []
		if len(func.arguments) > 0:
			p = func.arguments[0]
			params.append(":%s" % (p.name))

		for p in func.arguments[1:]:
			params.append("%s:%s" % (p.name, p.name))

		params.append("success:success")
		return " ".join(params)
	func.get_objc_params_for_call = get_objc_params_for_call

	def is_arg_objc_obj(p):
		param_type = to_objc_type_for_param(str(p.type))

		return param_type.endswith("*")
	func.is_arg_objc_obj = is_arg_objc_obj

	def get_java_return_type():
		return to_java_ref_type(str(func.type))

	def get_java_return_inner_type():
		type_str = str(func.type)
		if type_str.startswith("list<"):
			return to_java_ref_type(type_str[5:-1])
		return type_str
	func.get_java_return_type = get_java_return_type
	func.get_java_return_inner_type = get_java_return_inner_type


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
