# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# NO CHECKED-IN PROTOBUF GENCODE
# source: echo.proto
# Protobuf Python Version: 5.29.0
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(
    _runtime_version.Domain.PUBLIC,
    5,
    29,
    0,
    '',
    'echo.proto'
)
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\necho.proto\x12\x04\x65\x63ho\"\x1a\n\x07Request\x12\x0f\n\x07message\x18\x01 \x01(\t\"\x1b\n\x08Response\x12\x0f\n\x07message\x18\x01 \x01(\t\"\x1e\n\x05State\x12\x15\n\rrequest_count\x18\x01 \x01(\x05\"\x07\n\x05\x45mpty2f\n\x0b\x45\x63hoService\x12,\n\x0bSendRequest\x12\r.echo.Request\x1a\x0e.echo.Response\x12)\n\x0bStreamState\x12\x0b.echo.Empty\x1a\x0b.echo.State0\x01\x62\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'echo_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
  DESCRIPTOR._loaded_options = None
  _globals['_REQUEST']._serialized_start=20
  _globals['_REQUEST']._serialized_end=46
  _globals['_RESPONSE']._serialized_start=48
  _globals['_RESPONSE']._serialized_end=75
  _globals['_STATE']._serialized_start=77
  _globals['_STATE']._serialized_end=107
  _globals['_EMPTY']._serialized_start=109
  _globals['_EMPTY']._serialized_end=116
  _globals['_ECHOSERVICE']._serialized_start=118
  _globals['_ECHOSERVICE']._serialized_end=220
# @@protoc_insertion_point(module_scope)
