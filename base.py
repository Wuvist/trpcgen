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
objc_namespace = ""
javascript_namespace = ""

java_types = {
	"bool": "boolean",
	"i32": "int",
	"i64": "long",
	"string": "String"
}

csharp_types = {
	"bool": "bool",
	"i32": "int",
	"i64": "long",
	"string": "string"
}

objc_types = {
	"i32": "NSInteger ",
	"i64": "long long ",
	"string": "(nonatomic, copy) NSString *",
	"double":"double ",
	"bool":"BOOL ",
}

objc_types_for_param = {
	"i32": "NSInteger",
	"bool": "BOOL",
	"string": "NSString *"
}

java_ref_types = {
	"bool": "Boolean",
	"i32": "Integer",
	"i64": "Long",
	"string": "String"
}

javascript_types = {
	"int":"number",
	"i32":"number",
	"i64":"number",
	"double":"number",
	"bool":"boolean",
	"string":"string",
}

def is_list(field_type):
	if field_type is str:
		return field_type.startswith("list<")

	return str(field_type).startswith("list<")

def need_import_type(field_type):
	if is_list(field_type):
		return need_import_type(get_inner_type(field_type))
	type_str = str(field_type)
	if type_str in ["void", "i32", "i64", "int", "bool", "string", "double"]:
		return False
	return True

def get_inner_type(field_type):
	type_str = str(field_type)
	if type_str.startswith("list<"):
		return type_str[5:-1]
	return None

def to_java_type(type_str):
	if java_types.has_key(type_str):
		return java_types[type_str]

	if type_str.startswith("list<"):
		return "java.util.ArrayList<" + to_java_ref_type(type_str[5:-1]) + ">"
	return type_str

def to_csharp_type(type_str):
	if csharp_types.has_key(type_str):
		return csharp_types[type_str]

	if type_str.startswith("list<"):
		return "List<" + to_csharp_type(type_str[5:-1]) + ">"
	return type_str

def to_objc_type(type_str):
	if objc_types.has_key(type_str):
		return objc_types[type_str]

	if type_str.startswith("list<"):
		return "NSArray *"
	return objc_namespace + type_str[1:] + " *"

def to_javascript_type(type_str):
	if javascript_types.has_key(type_str):
		return javascript_types[type_str]

	if type_str.startswith("list<"):
		return "Array<%s>"%(to_javascript_type(type_str[5:-1]))

	if type_str.find(".") > -1:
		type_str = type_str.split(".")[-1:][0]

	return javascript_namespace+type_str

def to_javascript_callback_success_type(type_str):
	if type_str == "void":
		return "emptyCallback"

	return "%sCallback"%(to_javascript_type(type_str).replace("<","").replace(">",""))


def to_objc_type_for_param(type_str):
	if objc_types_for_param.has_key(type_str):
		return objc_types_for_param[type_str]

	if type_str.startswith("list<"):
		return "NSArray *"
	return objc_namespace + type_str[1:] + " *"

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
	def type_java_ref():
		return to_java_ref_type(type_str)

	field.is_list_type = False
	if type_str.startswith("list<"):
		field.is_list_type = True
		field.inner_type_java = to_java_type(type_str[5:-1])

	field.type_java = type_java

	def type_csharp():
		return to_csharp_type(type_str)
	field.type_csharp = type_csharp

	def type_objc():
		return to_objc_type(type_str)
	field.type_objc = type_objc

def extend_struct(obj):
	def get_name():
		return obj.name.value
	obj.get_name = get_name 

	extra_struct = set()
	get_objc_struct_import = set()
	for field in obj.fields:
		extend_field(field)

		if field.is_list_type:
			inner_type = get_inner_type(field.type)
			if need_import_type(inner_type):
				extra_struct.add(inner_type)
				get_objc_struct_import.add('#import "' + inner_type + '.h"')
		else:
			if need_import_type(field.type):
				extra_struct.add(str(field.type))
				get_objc_struct_import.add('#import "' + str(field.type) + '.h"')
	
	def to_javascript_callbacks():
		classes = []
		baseType = obj.get_name()
		
		types = [
			"list<%s>"%baseType,
			"list<list<%s>>"%baseType,
			baseType,
		]

		for oneType in types:
			classes.append("declare class %s{success:(data:%s)=>void;error?:(data:any)=>void}"%(to_javascript_callback_success_type(oneType),to_javascript_type(oneType)))
			
		return "\n".join(classes)


	obj.get_objc_struct_import = "\n".join(get_objc_struct_import)
	obj.extra_struct = extra_struct
	obj.get_inner_type = get_inner_type
	obj.to_javascript_type = to_javascript_type
	obj.to_javascript_callbacks = to_javascript_callbacks
	

def extend_func(func):
	# final String originCode, final int offset, final int limit, final Listener<ArrayList<TCollection>> listener

	def get_java_params():
		params = []
		for p in func.arguments:
			params.append("final %s %s" % (to_java_type(str(p.type)), p.name))

		return_type = to_java_ref_type(str(func.type))
		if return_type == "void":
			params.append("final Listener<Boolean> listener")
		else:
			params.append("final Listener<%s> listener" % (return_type))
		return ", ".join(params)
	func.get_java_params = get_java_params

	def get_csharp_params():
		if len(func.arguments) == 0:
			return ""
		if len(func.arguments) == 1:
			p = func.arguments[0]
			return "%s %s" % (to_csharp_type(str(p.type)), p.name)

		return "%sParam para" % (func.name)
		
	func.get_csharp_params = get_csharp_params

	def wrap_name(name):
		if str(name) == "id":
			return "Id"
		return name

	def get_objc_params():
		params = []

		if len(func.arguments) > 0:
			p = func.arguments[0]
			param_type = to_objc_type_for_param(str(p.type))
			params.append("(%s)%s" % (param_type, wrap_name(p.name)))

		for p in func.arguments[1:]:
			param_type = to_objc_type_for_param(str(p.type))
			params.append("%s:(%s)%s" % (p.name, param_type, p.name))

		if str(func.type) == "void":
			if len(params) == 0:
				params.append("(void (^)())success")
			else:
				params.append("success:(void (^)())success")
		else:
			return_type = to_objc_type_for_param(str(func.type))
			if not return_type.endswith("*"):
				return_type = return_type + " "
			if len(params) == 0:
				params.append("(void (^)(%s))success" % (return_type + "result"))
			else:
				params.append("success:(void (^)(%s))success" % (return_type + "result"))

		return "\n".join(params)
	func.get_objc_params = get_objc_params

	def get_objc_params_for_call():
		params = []
		if len(func.arguments) > 0:
			p = func.arguments[0]
			params.append("%s" % (wrap_name(p.name)))

		for p in func.arguments[1:]:
			params.append("%s:%s" % (p.name, p.name))
		if len(params) == 0:
			params.append("success")
		else:
			params.append("success:success")
		return " ".join(params)
	func.get_objc_params_for_call = get_objc_params_for_call

	def is_arg_objc_obj(p):
		param_type = to_objc_type_for_param(str(p.type))

		return param_type.endswith("*")
	func.is_arg_objc_obj = is_arg_objc_obj

	def get_csharp_return_type():
		return to_csharp_type(str(func.type))
	func.get_csharp_return_type = get_csharp_return_type

	def get_java_return_type():
		return to_java_ref_type(str(func.type))

	def get_java_return_inner_type():
		type_str = str(func.type)
		if type_str.startswith("list<"):
			return to_java_ref_type(type_str[5:-1])
		return type_str
	func.get_java_return_type = get_java_return_type
	func.get_java_return_inner_type = get_java_return_inner_type

	def is_list_type(s):
		return s.startswith("list<")
		
	func.is_list_type = is_list_type
	func.get_inner_type = get_inner_type

	def get_javascript_params():

		params = [];

		for p in func.arguments:
			params.append("%s:%s"%(p.name,to_javascript_type(str(p.type))))

		params.append("callback?:%s"%(to_javascript_callback_success_type(str(func.type))));
		return ",".join(params);

	func.get_javascript_params = get_javascript_params


def extend_service(obj):
	def get_name():
		return obj.name.value
	obj.get_name = get_name

	get_objc_func_import = set()
	extra_struct = set()

	for func in obj.functions:
		extend_func(func)
		
		for p in func.arguments:
			if need_import_type(p.type):
				param_type = to_objc_type_for_param(str(p.type))
				
				type_for_import = str(p.type)
				if is_list(type_for_import):
					type_for_import = get_inner_type(type_for_import)

				get_objc_func_import.add('#import "' + type_for_import + '.h"')
				extra_struct.add(type_for_import)

		if not is_list(func.type) and need_import_type(func.type):
			get_objc_func_import.add('#import "' + str(func.type) + '.h"')
			extra_struct.add(str(func.type))

		elif is_list(func.type):
			inner_type = get_inner_type(func.type)
			if need_import_type(inner_type):
				get_objc_func_import.add('#import "' + inner_type + '.h"')
				extra_struct.add(inner_type)

	def get_csharp_param_objs():
		param_objs = []
		for func in obj.functions:
			if len(func.arguments) > 1:
				param_objs.append({
					"name": func.name.value + "Param",
					"fields": [{"type": to_csharp_type(str(p.type)), "name": p.name} for p in func.arguments]
				})

		return param_objs

	obj.get_objc_func_import = "\n".join(get_objc_func_import)
	obj.get_csharp_param_objs = get_csharp_param_objs

	obj.extra_struct = extra_struct

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
