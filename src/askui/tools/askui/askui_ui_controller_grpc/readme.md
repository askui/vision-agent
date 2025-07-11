## 1) Generate code
```bash
python -m grpc_tools.protoc \
-I src/askui/tools/askui/askui_ui_controller_grpc/proto \
--python_out=src/askui/tools/askui/askui_ui_controller_grpc/generated \
--pyi_out=src/askui/tools/askui/askui_ui_controller_grpc/generated \
--grpc_python_out=src/askui/tools/askui/askui_ui_controller_grpc/generated \
src/askui/tools/askui/askui_ui_controller_grpc/proto/*
```

 
## 2) Fix import
Because of [this issue](https://github.com/protocolbuffers/protobuf/issues/1491) following change is required in `Controller_V1_pb2_grpc.py` after generating the code.

```diff
- import Controller_V1_pb2 as Controller__V1__pb2
+ from . import Controller_V1_pb2 as Controller__V1__pb2
```

