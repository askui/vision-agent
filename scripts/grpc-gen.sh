#!/bin/bash

# Define paths
PROTO_DIR="src/askui/tools/askui/askui_ui_controller_grpc/proto"
OUTPUT_DIR="src/askui/tools/askui/askui_ui_controller_grpc/generated"
PROTO_FILE="Controller_V1.proto"
GRPC_FILE="Controller_V1_pb2_grpc.py"

# Generate Python gRPC code from proto file
python -m grpc_tools.protoc \
  -I "$PROTO_DIR" \
  --python_out="$OUTPUT_DIR" \
  --pyi_out="$OUTPUT_DIR" \
  --grpc_python_out="$OUTPUT_DIR" \
  "$PROTO_DIR/$PROTO_FILE"

# Fix import in generated gRPC file to use relative import
# https://github.com/protocolbuffers/protobuf/issues/1491
sed -i.bak \
  's/^import Controller_V1_pb2 as Controller__V1__pb2$/from . import Controller_V1_pb2 as Controller__V1__pb2/' \
  "$OUTPUT_DIR/$GRPC_FILE"

# Remove backup file
rm "$OUTPUT_DIR/$GRPC_FILE.bak"
