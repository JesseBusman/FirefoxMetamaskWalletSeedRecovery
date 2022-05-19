#!/bin/python3
import sqlite3
import snappy
import io
import sys
import glob
import pathlib




"""A SpiderMonkey StructuredClone object reader for Python."""
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Credits:
#   – Source was havily inspired by
#     https://dxr.mozilla.org/mozilla-central/rev/3bc0d683a41cb63c83cb115d1b6a85d50013d59e/js/src/vm/StructuredClone.cpp
#     and many helpful comments were copied as-is.
#   – Python source code by Alexander Schlarb, 2020.

import collections
import datetime
import enum
import io
import re
import struct
import typing


class ParseError(ValueError):
	pass


class InvalidHeaderError(ParseError):
	pass


class JSInt32(int):
	"""Type to represent the standard 32-bit signed integer"""
	def __init__(self, *a):
		if not (-0x80000000 <= self <= 0x7FFFFFFF):
			raise TypeError("JavaScript integers are signed 32-bit values")


class JSBigInt(int):
	"""Type to represent the arbitrary precision JavaScript “BigInt” type"""
	pass


class JSBigIntObj(JSBigInt):
	"""Type to represent the JavaScript BigInt object type (vs the primitive type)"""
	pass


class JSBooleanObj(int):
	"""Type to represent JavaScript boolean “objects” (vs the primitive type)
	
	Note: This derives from `int`, since one cannot directly derive from `bool`."""
	__slots__ = ()
	
	def __new__(self, inner: object = False):
		return int.__new__(bool(inner))
	
	def __and__(self, other: bool) -> bool:
		return bool(self) & other
	
	def __or__(self, other: bool) -> bool:
		return bool(self) | other
	
	def __xor__(self, other: bool) -> bool:
		return bool(self) ^ other
	
	def __rand__(self, other: bool) -> bool:
		return other & bool(self)
	
	def __ror__(self, other: bool) -> bool:
		return other | bool(self)
	
	def __rxor__(self, other: bool) -> bool:
		return other ^ bool(self)
	
	def __str__(self, other: bool) -> str:
		return str(bool(self))



class _HashableContainer:
	inner: object
	
	def __init__(self, inner: object):
		self.inner = inner
	
	def __hash__(self):
		return id(self.inner)
	
	def __repr__(self):
		return repr(self.inner)
	
	def __str__(self):
		return str(self.inner)


class JSMapObj(collections.UserDict):
	"""JavaScript compatible Map object that allows arbitrary values for the key."""
	@staticmethod
	def key_to_hashable(key: object) -> collections.abc.Hashable:
		try:
			hash(key)
		except TypeError:
			return _HashableContainer(key)
		else:
			return key
	
	def __contains__(self, key: object) -> bool:
		return super().__contains__(self.key_to_hashable(key))
	
	def __delitem__(self, key: object) -> None:
		return super().__delitem__(self.key_to_hashable(key))
	
	def __getitem__(self, key: object) -> object:
		return super().__getitem__(self.key_to_hashable(key))
	
	def __iter__(self) -> typing.Iterator[object]:
		for key in super().__iter__():
			if isinstance(key, _HashableContainer):
				key = key.inner
			yield key
	
	def __setitem__(self, key: object, value: object):
		super().__setitem__(self.key_to_hashable(key), value)


class JSNumberObj(float):
	"""Type to represent JavaScript number/float “objects” (vs the primitive type)"""
	pass


class JSRegExpObj:
	expr:  str
	flags: 'RegExpFlag'
	
	def __init__(self, expr: str, flags: 'RegExpFlag'):
		self.expr  = expr
		self.flags = flags
	
	@classmethod
	def from_re(cls, regex: re.Pattern) -> 'JSRegExpObj':
		flags = RegExpFlag.GLOBAL
		if regex.flags | re.DOTALL:
			pass  # Not supported in current (2020-01) version of SpiderMonkey
		if regex.flags | re.IGNORECASE:
			flags |= RegExpFlag.IGNORE_CASE
		if regex.flags | re.MULTILINE:
			flags |= RegExpFlag.MULTILINE
		return cls(regex.pattern, flags)
	
	def to_re(self) -> re.Pattern:
		flags = 0
		if self.flags | RegExpFlag.IGNORE_CASE:
			flags |= re.IGNORECASE
		if self.flags | RegExpFlag.GLOBAL:
			pass  # Matching type depends on matching function used in Python
		if self.flags | RegExpFlag.MULTILINE:
			flags |= re.MULTILINE
		if self.flags | RegExpFlag.UNICODE:
			pass  #XXX
		return re.compile(self.expr, flags)


class JSSavedFrame:
	def __init__(self):
		raise NotImplementedError()


class JSSetObj:
	def __init__(self):
		raise NotImplementedError()


class JSStringObj(str):
	"""Type to represent JavaScript string “objects” (vs the primitive type)"""
	pass



class DataType(enum.IntEnum):
	# Special values
	FLOAT_MAX = 0xFFF00000
	HEADER    = 0xFFF10000
	
	# Basic JavaScript types
	NULL      = 0xFFFF0000
	UNDEFINED = 0xFFFF0001
	BOOLEAN   = 0xFFFF0002
	INT32     = 0xFFFF0003
	STRING    = 0xFFFF0004
	
	# Extended JavaScript types
	DATE_OBJECT           = 0xFFFF0005
	REGEXP_OBJECT         = 0xFFFF0006
	ARRAY_OBJECT          = 0xFFFF0007
	OBJECT_OBJECT         = 0xFFFF0008
	ARRAY_BUFFER_OBJECT   = 0xFFFF0009
	BOOLEAN_OBJECT        = 0xFFFF000A
	STRING_OBJECT         = 0xFFFF000B
	NUMBER_OBJECT         = 0xFFFF000C
	BACK_REFERENCE_OBJECT = 0xFFFF000D
	#DO_NOT_USE_1
	#DO_NOT_USE_2
	TYPED_ARRAY_OBJECT    = 0xFFFF0010
	MAP_OBJECT            = 0xFFFF0011
	SET_OBJECT            = 0xFFFF0012
	END_OF_KEYS           = 0xFFFF0013
	#DO_NOT_USE_3
	DATA_VIEW_OBJECT      = 0xFFFF0015
	SAVED_FRAME_OBJECT    = 0xFFFF0016  # ?
	
	# Principals ?
	JSPRINCIPALS      = 0xFFFF0017
	NULL_JSPRINCIPALS = 0xFFFF0018
	RECONSTRUCTED_SAVED_FRAME_PRINCIPALS_IS_SYSTEM     = 0xFFFF0019
	RECONSTRUCTED_SAVED_FRAME_PRINCIPALS_IS_NOT_SYSTEM = 0xFFFF001A
	
	# ?
	SHARED_ARRAY_BUFFER_OBJECT = 0xFFFF001B
	SHARED_WASM_MEMORY_OBJECT  = 0xFFFF001C
	
	# Arbitrarily sized integers
	BIGINT        = 0xFFFF001D
	BIGINT_OBJECT = 0xFFFF001E
	
	# Older typed arrays
	TYPED_ARRAY_V1_MIN           = 0xFFFF0100
	TYPED_ARRAY_V1_INT8          = TYPED_ARRAY_V1_MIN + 0
	TYPED_ARRAY_V1_UINT8         = TYPED_ARRAY_V1_MIN + 1
	TYPED_ARRAY_V1_INT16         = TYPED_ARRAY_V1_MIN + 2
	TYPED_ARRAY_V1_UINT16        = TYPED_ARRAY_V1_MIN + 3
	TYPED_ARRAY_V1_INT32         = TYPED_ARRAY_V1_MIN + 4
	TYPED_ARRAY_V1_UINT32        = TYPED_ARRAY_V1_MIN + 5
	TYPED_ARRAY_V1_FLOAT32       = TYPED_ARRAY_V1_MIN + 6
	TYPED_ARRAY_V1_FLOAT64       = TYPED_ARRAY_V1_MIN + 7
	TYPED_ARRAY_V1_UINT8_CLAMPED = TYPED_ARRAY_V1_MIN + 8
	TYPED_ARRAY_V1_MAX           = TYPED_ARRAY_V1_UINT8_CLAMPED
	
	# Transfer-only tags (not used for persistent data)
	TRANSFER_MAP_HEADER              = 0xFFFF0200
	TRANSFER_MAP_PENDING_ENTRY       = 0xFFFF0201
	TRANSFER_MAP_ARRAY_BUFFER        = 0xFFFF0202
	TRANSFER_MAP_STORED_ARRAY_BUFFER = 0xFFFF0203


class RegExpFlag(enum.IntFlag):
	IGNORE_CASE = 0b00001
	GLOBAL      = 0b00010
	MULTILINE   = 0b00100
	UNICODE     = 0b01000


class Scope(enum.IntEnum):
	SAME_PROCESS                   = 1
	DIFFERENT_PROCESS              = 2
	DIFFERENT_PROCESS_FOR_INDEX_DB = 3
	UNASSIGNED                     = 4
	UNKNOWN_DESTINATION            = 5


class _Input:
	stream: io.BufferedReader
	
	def __init__(self, stream: io.BufferedReader):
		self.stream = stream
	
	def peek(self) -> int:
		try:
			return struct.unpack_from("<q", self.stream.peek(8))[0]
		except struct.error:
			raise EOFError() from None
	
	def peek_pair(self) -> (int, int):
		v = self.peek()
		return ((v >> 32) & 0xFFFFFFFF, (v >> 0) & 0xFFFFFFFF)
	
	def drop_padding(self, read_length):
		length = 8 - ((read_length - 1) % 8) - 1
		result = self.stream.read(length)
		if len(result) < length:
			raise EOFError()
	
	def read(self, fmt="q"):
		try:
			return struct.unpack("<" + fmt, self.stream.read(8))[0]
		except struct.error:
			raise EOFError() from None
	
	def read_bytes(self, length: int) -> bytes:
		result = self.stream.read(length)
		if len(result) < length:
			raise EOFError()
		self.drop_padding(length)
		return result
	
	def read_pair(self) -> (int, int):
		v = self.read()
		return ((v >> 32) & 0xFFFFFFFF, (v >> 0) & 0xFFFFFFFF)
	
	def read_double(self) -> float:
		return self.read("d")


class Reader:
	all_objs: typing.List[typing.Union[list, dict]]
	compat:   bool
	input:    _Input
	objs:     typing.List[typing.Union[list, dict]]
	
	
	def __init__(self, stream: io.BufferedReader):
		self.input = _Input(stream)
		
		self.all_objs = []
		self.compat   = False
		self.objs     = []
	
	
	def read(self):
		self.read_header()
		self.read_transfer_map()
		
		# Start out by reading in the main object and pushing it onto the 'objs'
		# stack. The data related to this object and its descendants extends
		# from here to the SCTAG_END_OF_KEYS at the end of the stream.
		add_obj, result = self.start_read()
		if add_obj:
			self.all_objs.append(result)
		
		# Stop when the stack shows that all objects have been read.
		while len(self.objs) > 0:
			# What happens depends on the top obj on the objs stack.
			obj = self.objs[-1]
			
			tag, data = self.input.peek_pair()
			if tag == DataType.END_OF_KEYS:
				# Pop the current obj off the stack, since we are done with it
				# and its children.
				self.input.read_pair()
				self.objs.pop()
				continue
			
			# The input stream contains a sequence of "child" values, whose
			# interpretation depends on the type of obj. These values can be
			# anything.
			#
			# startRead() will allocate the (empty) object, but note that when
			# startRead() returns, 'key' is not yet initialized with any of its
			# properties. Those will be filled in by returning to the head of
			# this loop, processing the first child obj, and continuing until
			# all children have been fully created.
			#
			# Note that this means the ordering in the stream is a little funky
			# for things like Map. See the comment above startWrite() for an
			# example.
			add_obj, key = self.start_read()
			if add_obj:
				self.all_objs.append(key)
			
			# Backwards compatibility: Null formerly indicated the end of
			# object properties.
			if key is None and not isinstance(obj, (JSMapObj, JSSetObj, JSSavedFrame)):
				self.objs.pop()
				continue
			
			# Set object: the values between obj header (from startRead()) and
			# DataType.END_OF_KEYS are interpreted as values to add to the set.
			if isinstance(obj, JSSetObj):
				obj.add(key)
			
			if isinstance(obj, JSSavedFrame):
				raise NotImplementedError()  #XXX: TODO
			
			# Everything else uses a series of key, value, key, value, … objects.
			add_obj, val = self.start_read()
			if add_obj:
				self.all_objs.append(val)
			
			# For a Map, store those <key,value> pairs in the contained map
			# data structure.
			if isinstance(obj, JSMapObj):
				obj[key] = value
			else:
				if not isinstance(key, (str, int)):
					#continue
					raise ParseError("JavaScript object key must be a string or integer")
				
				if isinstance(obj, list):
					# Ignore object properties on array
					if not isinstance(key, int) or key < 0:
						continue
					
					# Extend list with extra slots if needed
					while key >= len(obj):
						obj.append(NotImplemented)
				
				obj[key] = val
		
		self.all_objs.clear()
		
		return result
	
	
	def read_header(self) -> None:
		tag, data = self.input.peek_pair()
		
		scope: int
		if tag == DataType.HEADER:
			tag, data = self.input.read_pair()
			
			if data == 0:
				data = int(Scope.SAME_PROCESS)
			
			scope = data
		else:  # Old on-disk format
			scope = int(Scope.DIFFERENT_PROCESS_FOR_INDEX_DB)
		
		if scope == Scope.DIFFERENT_PROCESS:
			self.compat = False
		elif scope == Scope.DIFFERENT_PROCESS_FOR_INDEX_DB:
			self.compat = True
		elif scope == Scope.SAME_PROCESS:
			raise InvalidHeaderError("Can only parse persistent data")
		else:
			raise InvalidHeaderError("Invalid scope")
	
	
	def read_transfer_map(self) -> None:
		tag, data = self.input.peek_pair()
		if tag == DataType.TRANSFER_MAP_HEADER:
			raise InvalidHeaderError("Transfer maps are not allowed for persistent data")
	
	
	def read_bigint(self, info: int) -> JSBigInt:
		length   = info & 0x7FFFFFFF
		negative = bool(info & 0x80000000)
		raise NotImplementedError()
	
	
	def read_string(self, info: int) -> str:
		length = info & 0x7FFFFFFF
		latin1 = bool(info & 0x80000000)
		
		if latin1:
			return self.input.read_bytes(length).decode("latin-1")
		else:
			return self.input.read_bytes(length * 2).decode("utf-16le")
	
	
	def start_read(self):
		tag, data = self.input.read_pair()
		
		if tag == DataType.NULL:
			return False, None
		
		elif tag == DataType.UNDEFINED:
			return False, NotImplemented
		
		elif tag == DataType.INT32:
			if data > 0x7FFFFFFF:
				data -= 0x80000000
			return False, JSInt32(data)
		
		elif tag == DataType.BOOLEAN:
			return False, bool(data)
		elif tag == DataType.BOOLEAN_OBJECT:
			return True, JSBooleanObj(data)
		
		elif tag == DataType.STRING:
			return False, self.read_string(data)
		elif tag == DataType.STRING_OBJECT:
			return True, JSStringObj(self.read_string(data))
		
		elif tag == DataType.NUMBER_OBJECT:
			return True, JSNumberObj(self.input.read_double())
		
		elif tag == DataType.BIGINT:
			return False, self.read_bigint()
		elif tag == DataType.BIGINT_OBJECT:
			return True, JSBigIntObj(self.read_bigint())
		
		elif tag == DataType.DATE_OBJECT:
			# These timestamps are always UTC
			return True, datetime.datetime.fromtimestamp(self.input.read_double(),
			                                             datetime.timezone.utc)
		
		elif tag == DataType.REGEXP_OBJECT:
			flags = RegExpFlag(data)
			
			tag2, data2 = self.input.read_pair()
			if tag2 != DataType.STRING:
				#return False, False
				raise ParseError("RegExp type must be followed by string")
			
			return True, JSRegExpObj(flags, self.read_string(data2))
		
		elif tag == DataType.ARRAY_OBJECT:
			obj = []
			self.objs.append(obj)
			return True, obj
		elif tag == DataType.OBJECT_OBJECT:
			obj = {}
			self.objs.append(obj)
			return True, obj
		
		elif tag == DataType.BACK_REFERENCE_OBJECT:
			try:
				return False, self.all_objs[data]
			except IndexError:
				#return False, False
				raise ParseError("Object backreference to non-existing object") from None
		
		elif tag == DataType.ARRAY_BUFFER_OBJECT:
			return True, self.read_array_buffer(data)  #XXX: TODO
		
		elif tag == DataType.SHARED_ARRAY_BUFFER_OBJECT:
			return True, self.read_shared_array_buffer(data)  #XXX: TODO
		
		elif tag == DataType.SHARED_WASM_MEMORY_OBJECT:
			return True, self.read_shared_wasm_memory(data)  #XXX: TODO
		
		elif tag == DataType.TYPED_ARRAY_OBJECT:
			array_type = self.input.read()
			return False, self.read_typed_array(array_type, data)  #XXX: TODO
		
		elif tag == DataType.DATA_VIEW_OBJECT:
			return False, self.read_data_view(data)  #XXX: TODO
		
		elif tag == DataType.MAP_OBJECT:
			obj = JSMapObj()
			self.objs.append(obj)
			return True, obj
		
		elif tag == DataType.SET_OBJECT:
			obj = JSSetObj()
			self.objs.append(obj)
			return True, obj
		
		elif tag == DataType.SAVED_FRAME_OBJECT:
			obj = self.read_saved_frame(data)  #XXX: TODO
			self.objs.append(obj)
			return True, obj
		
		elif tag < int(DataType.FLOAT_MAX):
			# Reassemble double floating point value
			return False, struct.unpack("=d", struct.pack("=q", (tag << 32) | data))[0]
		
		elif DataType.TYPED_ARRAY_V1_MIN <= tag <= DataType.TYPED_ARRAY_V1_MAX:
			return False, self.read_typed_array(tag - DataType.TYPED_ARRAY_V1_MIN, data)
		
		else:
			#return False, False
			raise ParseError("Unsupported type")







def print_vaults(obj):
	if isinstance(obj, dict):
		if "vault" in obj:
			print("---------------------------------------")
			print("Maybe found a Metamask vault:\n")
			print(obj["vault"])
			print("\n---------------------------------------\n\n\n")
		if "data" in obj and "salt" in obj:
			print("---------------------------------------")
			print("Found a Metamask vault:\n")
			print(json.dumps(obj))
			print("\n---------------------------------------\n\n\n")
		for key in obj:
			print_vaults(obj[key])
	if isinstance(obj, str):
		if ("'data'" in obj or '"data"' in obj) and ("'salt'" in obj or '"salt"' in obj):
			print("---------------------------------------")
			print("Probably found a Metamask vault:\n")
			print(obj)
			print("\n---------------------------------------\n\n\n")

def print_vaults_from_sqlite_file(f):
	try:
		with sqlite3.connect("file:" + f + "?mode=ro&immutable=1", uri=True) as conn:
			cur = conn.cursor()
			cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='object_data'")
			if len(cur.fetchall()) == 0:
				return
			cur.execute("SELECT * FROM object_data")
			rows = cur.fetchall()
			failures = 0
			for row in rows:
				try:
					decompressed = snappy.decompress(row[4])
				except AttributeError as ex:
					failures += 1
					if "'snappy' has no attribute" in str(ex):
						print("Failed to use python-snappy. Is it installed?")
						exit()
						os._exit(0)
					continue
				except:
					failures += 1
					#print("Snappy decompress failed for row in "+f)
					continue
				
				try:
					reader = Reader(io.BufferedReader(io.BytesIO(decompressed)))
					content = reader.read()
				except:
					failures += 1
					continue
				
				print_vaults(content)
				
			if failures >= 1:
				print("Failed to parse "+str(failures)+" rows in "+f)
	except BaseException as ex:
		print(ex)
		print("Failure while reading "+f)

if len(sys.argv) >= 2:
	print_vaults_from_sqlite_file(sys.argv[1])
else:
	print("Scanning all .sqlite files in the current folder recursively...")
	for f in pathlib.Path('.').glob('**/*.sqlite'):
		print_vaults_from_sqlite_file(str(f))
