# 没有uv环境需要使用 pip install uv 安装uv环境
uv venv .venv
source .venv/bin/activate
uv pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple