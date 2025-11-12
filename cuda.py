import torch

# 1. 检查 CUDA 是否可用
print(f"CUDA 可用：{torch.cuda.is_available()}")  # 输出 True 则成功

# 2. 查看 PyTorch 绑定的 CUDA 版本（应显示 12.4）
print(f"PyTorch 绑定的 CUDA 版本：{torch.version.cuda}")

# 3. 查看 GPU 信息（验证是否识别显卡）
if torch.cuda.is_available():
    print(f"GPU 型号：{torch.cuda.get_device_name(0)}")
    print(f"GPU 数量：{torch.cuda.device_count()}")