# neuron_firmware_upgrade

# 使用方法
## 所需要的环境

- python 2.7
- 需要安装 pyserial 的库，最好是用 pip 安装 `python install pyserial`
- 需要安装 progressbar2 的库，最好是用 pip 安装 `pip install progressbar2`

## 使用步骤

- 在shell 中输入 `python neuron_firmware_upgrade.py -p [串口名称] -i [固件镜像的Path]` -d[需要升级的模块id]

- 示例: `python neuron_firmware_upgrade.py -p COM3 -i H:/myan/python/013_64_02_appButton_20170925.bin -d 2`
