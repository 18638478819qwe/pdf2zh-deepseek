# 极客版学术文献双语翻译神器 (PDFMathTranslate DeepSeek 增强版)

> 基于知名开源项目 [Byaidu/PDFMathTranslate (pdf2zh)](https://github.com/Byaidu/PDFMathTranslate) 的深度定制二次开发版本。
> 完美支持双栏排版、复杂数学公式、学术图表的无损还原，并深度适配大语言模型！

---

## 🌟 二创特性亮点

1. **🚀 深度适配 DeepSeek 大模型（默认首选）**：
   - 相比传统机器翻译，大模型翻译行文更加流畅地道，专业术语契合学术规范。
   - 界面默认预设 DeepSeek 最佳配置，开箱即用。
2. **🧠 智能人名推断与热词自动记忆**：
   - 针对中国学者发英文 Paper 时常见的拼音姓名（如 *Han Yuying*, *Qin Huimin*），支持自定义中文名字映射。
   - 大模型在翻译全篇时，将聪明地将拼音还原为正统汉字人名。
   - **自动持久化记忆**：热词配置一次输入，本地自动记忆，重启不丢失。
3. **🛡️ 纯净解耦与安全开箱**：
   - 剥离本地臃肿虚拟环境与私密文献，代码轻量纯净。
   - API Key 采用环境变量或界面即时输入，杜绝泄露风险。

---

## 🚀 快速开始

### 1. 克隆仓库
```bash
git clone https://github.com/sanger3471-dotcom/pdf2zh-deepseek.git
cd pdf2zh-deepseek
```

### 2. 安装依赖
建议使用 Python 3.10+ 环境：
```bash
pip install -r requirements.txt
```

### 3. 配置密钥与运行

#### 方式 A：Windows 一键启动（推荐）
双击目录下的 `start.bat` 即可启动服务。启动后，浏览器会自动打开 Web 操作界面：
- 在界面的 `OpenAI / DeepSeek API Key` 中输入你的 DeepSeek 密钥即可。

#### 方式 B：配置环境变量后启动
```bash
# Windows PowerShell
$env:DEEPSEEK_API_KEY="sk-你的DeepSeek密钥"
python app.py

# Linux / macOS
export DEEPSEEK_API_KEY="sk-你的DeepSeek密钥"
python app.py
```

---

## 💡 使用指南

### 1. 模式一：DeepSeek 智能大模型模式（推荐）
1. 上传待翻译的学术 PDF。
2. 在“自定义热词替换”中填入对应课题组成员或作者汉字姓名（如 `韩玉莹`、`秦慧民`，一行一个）。
3. 点击 **Translate**，等待模型解析与排版还原。
4. 翻译完成后，支持直接预览并下载**纯中文版**或**中英双语对照版** PDF！

### 2. 模式二：Google 免费模式
无需任何 API Key，在 Service 中切换为 `Google`，适合快速通读全文。在热词框中可使用 `英文=中文` 进行强制精准替换（例如 `Yuying Han=韩玉莹`）。

---

## 🙏 致谢与声明

本项目基于开源项目 [Byaidu/PDFMathTranslate](https://github.com/Byaidu/PDFMathTranslate) 进行二创增强与工作流定制。感谢原作者与开源社区的杰出贡献。
