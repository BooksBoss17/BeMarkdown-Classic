# BeMarkdown Classic

完整旧线路的独立开源工具，基于正式安装 BeMarkdown 0.3.0+sm120.2。它保留 PDF、DOCX、图片转换、三模型文字识别、公式与表格、图片筛选、资源调度及审查交接。未合入新的 V3 + OvisOCR3 视觉串行候选。

## 完整流程

1. 输入检查与来源绑定；DOCX 解析 OOXML，截图分页必要时调用 LibreOffice；图片归一化后进入 PDF 路线。
2. PDF 提取原生文字、图片和矢量证据，PP-DocLayout_plus-L 识别版面，处理区域归属与阅读顺序。
3. 文字使用 PP-OCRv6 检测/识别 + OvisOCR2 + 条件触发的 Xiaomi-OCR-0，保留分歧及待审状态。
4. 公式优先结构恢复，必要时 PP-FormulaNet_plus-L；表格使用 PP-LCNet、SLANeXt 和 RT-DETR-L 的有线/无线分支。
5. 输出 Markdown、图片资产、来源坐标、清单和审查任务；跨进程卸载 OCR 后串接 B200 + Qwen3.5-9B 图片筛选。
6. 保护公式/表格/OCR 证据图，图片用途不明时保留；提供有来源绑定的局部审查、修改验证与交接接口。

CLI、Python API 和 MCP 入口均保留。受管队列、内存/显存准入、状态查询、断点及缓存校验也是工具组成部分。Agent 视觉审查由调用本工具的宿主承担，工具提供证据与写回接口；没有审查凭证的内容不会因此自动成为已验收内容。

## 安装

本次固定安装档案面向 Windows x64、SM120 NVIDIA GPU（本机 RTX 5070 Ti），使用迁移后正式线路的 Paddle CUDA 12.9 栈。其他硬件需单独验证匹配的运行档案；本次未认证。需要互联网获取固定版本的依赖与模型；驱动由用户维护。模型、缓存和隔离环境需要较大磁盘空间，建议预留 100 GB。运行时按实际设备检查资源，不保证任意显存/内存设备都能完成复杂页面。

先阅读 [许可说明](docs/LICENSE_AUDIT.md)，再在 PowerShell 执行：

```powershell
.\setup-complete.ps1 -AcceptExternalLicenses
```

完整安装依次部署转换器、11 个转换模型、2 个图片筛选模型及隔离环境。脚本使用 uv 获取固定 Python；需预装 uv（或按脚本提示安装）。首次安装 LibreOffice/VC++ 运行库可能需要管理员确认，也可先自行安装后重跑。已有本地模型可用 `-ModelCache <MODELS目录>`，仍核对 SHA256。不会修改已有 MCP 客户端配置；完成后按 `.local/mcp-client.json` 添加工具。

高级部署可分步执行 `setup.ps1` 与 `scripts/install_semantic_retention.py`，见 [筛选部署](docs/SEMANTIC_RETENTION.md)。仅执行前者不是完整图片筛选环境。受限网络下可预置模型和环境，但不能绕过文件校验。

## 使用

在仓库根目录使用安装生成的 Python 路径执行：

```powershell
$runtime = (Get-Content .local/runtime-selection.json -Raw | ConvertFrom-Json).python
& $runtime -m bemarkdown convert input.pdf --mcp-root . --output-root output --json
& $runtime -m bemarkdown convert-batch first.docx second.pdf --mcp-root . --output-root output --json
```

MCP 使用生成的客户端配置，先执行 `bemarkdown_vision` 视觉验证，再转换、查询、查看证据及审查交接。完整接口见 [使用说明](docs/MANAGED_CONVERSION.md)。不依赖原开发区、教材库或另一份 MCP 安装。

## 分发与边界

自有转换源码沿用 AGPL-3.0-only；组合筛选工具按其 AGPL-3.0-or-later 声明，第三方各自许可。源码、对应 wheel、安装器、固定模型版本与 SHA256 清单随仓库交付。大权重从固定上游 revision 或既有 B200 Release 的分片下载，校验分片与整文件哈希；NVIDIA/Microsoft 运行库从官方渠道获取，未混入源码包。

私有教材、训练数据、派生筛选模板、账户、机器路径及开发缓存不公开。保留筛选模板接口，部署者可登记自己的模板。没有使用无授权素材填充公开模板。

本工具输出来源忠实的中间包；OCR、公式、顺序或图片分类仍可能待核。软件发布/安装通过与全文内容正确性认证分别记录。当前版本验证见 [发行验证](docs/CLASSIC_VALIDATION.md)。
