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


def init_Fields(obj):
	idField = obj.fields[0]
	obj.idField = idField

	obj.relateObj = {}
	obj.fieldMap = {}


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
	except Exception, e:
		print "error", thrift_file
		traceback.print_exc()
		raise e
	return loader
