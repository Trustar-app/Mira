---
# 详细文档见https://modelscope.cn/docs/%E5%88%9B%E7%A9%BA%E9%97%B4%E5%8D%A1%E7%89%87

tags: #自定义标签
-
datasets: #关联数据集
  evaluation:
  #- iic/ICDAR13_HCTR_Dataset
  test:
  #- iic/MTWI
  train:
  #- iic/SIBR
models: #关联模型
- Qwen/Qwen2.5-Omni-7B

## 启动文件(若SDK为Gradio/Streamlit，默认为app.py, 若为Static HTML, 默认为index.html)
# deployspec:
#   entry_file: app.py
license: Apache License 2.0
---

## 部署

### 本地部署
1. 下载 uv 包管理器

   ```bash
   pip install uv
   ```

2. 安装依赖

   ```bash
   sh make-env.sh
   source .venv/bin/activate  
   ```

3. 在 `.env `文件中写入自己的 `API_KEY`

   API KEY 获取网站：`https://bailian.console.aliyun.com/?tab=model#/api-key`


4. 运行和调试 qwen-omni 的 agent
   ```bash
   python run_omni.py
   ```
     
5. 运行前后端
    ```bash
   python launch.py
   ```
   前端界面并没有更新。。。

   