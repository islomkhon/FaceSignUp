# Local model manifest

The project does not download models at runtime.

| Model | Local path | Source | SHA-256 |
|---|---|---|---|
| MediaPipe Face Landmarker | `public/models/face_landmarker.task` | Google MediaPipe model assets | `64184E229B263107BC2B804C6625DB1341FF2BB731874B0BCC2FE6544E0BC9FF` |
| YuNet face detector | `backend/models/face_detection_yunet_2023mar.onnx` | OpenCV Zoo | `8F2383E4DD3CFBB4553EA8718107FC0423210DC964F9F4280604804ED2552FA4` |
| SFace face recognizer | `backend/models/face_recognition_sface_2021dec.onnx` | OpenCV Zoo | `0BA9FBFA01B5270C96627C4EF784DA859931E02F04419C829E83484087C34E79` |
| MediaPipe WASM runtime | `public/mediapipe/wasm/vision_wasm_internal.wasm` | `@mediapipe/tasks-vision` | `225BC06C0F51A9CF31FEA0E9E0B0243E9E01FB5EF332CC1A7FA6656DBDFDAABF` |
| MediaPipe module WASM | `public/mediapipe/wasm/vision_wasm_module_internal.wasm` | `@mediapipe/tasks-vision` | `A269E84B12AEFC93C9D6A4D62B01F41E5434A9FA941533BB8E75B1E3D1669E46` |

The MediaPipe model and WASM files are copied or downloaded during development,
then served from the local Vite or FastAPI process. `npm run localize:mediapipe`
refreshes the copied WASM files after a package update.
