import torch.onnx

# 定义输入示例（批量大小为1，784个特征）
dummy_input = torch.randn(1, 94, 24)

# 指定输出ONNX模型的文件名
onnx_model_path = "model.onnx"

# 导出模型
torch.onnx.export(
    model,                      # 要转换的PyTorch模型
    dummy_input,                # 模型的输入示例
    onnx_model_path,            # ONNX模型的存储路径
    export_params=True,         # 是否导出训练好的参数
    opset_version=11,           # ONNX的操作集版本
    do_constant_folding=True,   # 是否优化常量折叠
    input_names = ['input'],    # 输入节点的名称
    output_names = ['output'],  # 输出节点的名称
    dynamic_axes={'input' : {1 : 'batch_size'},    # 动态轴设置
                  'output' : {1 : 'batch_size'}}
)

print(f"模型已成功转换并保存为 {onnx_model_path}")
