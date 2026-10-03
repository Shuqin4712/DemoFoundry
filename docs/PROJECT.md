# DemoFoundry · 项目概况与进度

> 这份文件是项目的**现行真源**：定位、范围、计划、进度、已定决策都以这里为准。
> 讨论过程和历史版本在设想文档 [生成式视频流水线 · 开源设想](https://claude.ai/code/artifact/2217212a-3639-4cf0-a3a9-ea7172a8bcf9)，那边只作参考。
> 发现这里写错了：直接改，或在「决策记录」里加一行说明为什么改。

**当前阶段：P1 清单与约定** · 最后更新：2026-10-03

---

## 1. 一句话

**把录屏、截图、Figma 或产品源码交给 agent，重建成你产品的界面组件库（模具），然后用讲稿批量生成带旁白的产品教程和演示片系列。**

录屏得到的是冻结的像素，重建得到的是可编程的界面。界面和视觉语言沉淀在仓库里，每做一集，下一集更快。

**做小做精。** v1 只做一种片型：带旁白的教程 / 演示片系列。给用户产品做的快节奏宣传片（音乐卡点、可能无旁白）不在 v1。

## 2. 给谁用

会用 Claude Code 或 Codex、有自己产品、需要快速批量出片的独立开发者和小团队。

用户最好不碰代码：只接触讲稿、预览和反馈，生成器由 agent 写。但不写死——生成器是可读可改的普通代码，想改的人可以直接改；常用的调整（主题、声音、音乐、画幅）放在配置文件里。

**一切英文为主**：README、skill 说明、对外文档、代码注释、示例集旁白都用英文；README 附中文版。本文件和 `AGENTS.md` 这类内部规划文件用中文，发布前决定是否翻译或移出仓库。

不面向不使用 agent 的人（那是远期的声明式描述 / MCP 方向）。

## 3. 和相邻方案的差别

| 方案 | 做什么 | 不做什么 |
| --- | --- | --- |
| Screen Studio + 配音 | 把录屏做得好看 | 像素是死的：产品改版要重录，录不到的状态摆不出来 |
| video-shotcraft（Remotion） | 通用镜头词汇：157 张镜头卡、主题、剪映导出 | 不记住你的产品；真实页面一律用截图贴图；本体无旁白 |
| HyperFrames `product-launch-video` | 给 URL 出一支宣传片 | 一次性，没有跨集复用 |
| **DemoFoundry** | 针对一个产品的、带旁白的、可持续出的系列片 | 不拼镜头卡数量；高级动效随版本慢慢加 |

重建界面带来的能力：产品改版不重录（改组件、重新生成）· 能摆出录不到的状态 · 光标、连线、打字、高亮按界面几何计算并挂在旁白的词上 · 任意画幅和分辨率 · 跨集一致。

## 4. 形态

**装 skill，由 skill 在用户的产品仓库里建工作室。**

1. **安装**：一句话装 skill（把链接交给 agent，或 `npx skills add`）。
2. **开工**：在产品仓库里说「给这个产品做一集教程」，skill 先初始化一个视频目录，并检查 Node、Python、ffmpeg。
3. **引擎**：生成器公共库和工具脚本随 skill 分发，升级 skill 即升级引擎；已出的集保留生成产物，不重新生成就不受影响。

| 层 | 内容 | 住在哪 |
| --- | --- | --- |
| 模具（产品工具箱） | 界面组件、质检页、色板字体、片头片尾、配音和音乐设置 | 用户仓库的视频目录 |
| 各集 | 讲稿、配音、生成器、合成、发布包 | 用户仓库的视频目录 |
| 引擎 | 生成器公共库、配音 / 录屏 / 素材工具、技法卡片 | skill 目录 |
| skill | 建模具、做一集 | skill 目录 |
| 工作台（可选） | 系列看板、模具浏览、预览入口 | skill 目录，读用户仓库的数据 |

**目录结构**（2026-10-03 定）

DemoFoundry 仓库：

```
skills/
  demofoundry/            引擎 + 初始化 + 入口
    SKILL.md
    engine/               生成器公共库；HyperFrames 输出收在一个模块里
    tools/                配音、转写、素材、封面、录屏
    techniques/           技法卡片
    templates/studio/     初始化用的模板
    scripts/              init、doctor（环境检查）
  demofoundry-mold/       建模具：SKILL.md + references/，用 ../demofoundry/ 引用引擎
  demofoundry-episode/    做一集：同上
workbench/                工作台（P5，可选安装）
tests/                    回归用的测试小集
docs/
```

安装：`npx skills add Shuqin4712/DemoFoundry --skill '*'`，装在项目级（随产品仓库提交，每个仓库锁自己的引擎版本）。

用户产品仓库里初始化出的目录：

```
demofoundry/
  demofoundry.json        主题、声音、音乐、画幅；引擎版本和 HyperFrames 版本
  mold/                   模具
    evidence/             录屏、截图、Figma 导出、源码摘录
    components/           归一化后的组件
    qc/                   质检页 + 参考图
    theme/                色板、字体
    intro-outro/          片头片尾
  assets/bgm/             背景音乐 + LICENSES.md（来源和授权）
  episodes/01-<slug>/
    SCRIPT.md             讲稿
    voice/                配音和逐词时间
    gen.py                本集生成器
    composition/          生成出的 HyperFrames 工程（不手改）
    publish/              MP4 · SRT · 封面 · 文案 · GIF
```

**工作台可插拔**：它只读仓库里的文件，出片不依赖它，不装也能完整出片。v1 不做面板级插件机制。工作台是示例集的拍摄对象、DemoFoundry 的门面，所以要**重新设计**；保留哪些功能（现有的上手指南、温馨提示、工作记录、搜索等）在 P5 和重新设计一起定。

**和 zeedemo 的关系**：zeedemo 照常生产、不受影响，DemoFoundry 只从它复制代码；v1 之前两边不做双向同步，v1 稳定后再考虑把 zeedemo 迁到 DemoFoundry 引擎。

词汇体系（辨识度的一部分）：模具 = 产品工具箱 · 浇铸 = 出一集 · 质检 = 验收页。

## 5. 关键设计

- **界面重建是核心。** 证据来源四种：产品源码（CSS、设计 token）、Figma、录屏、截图。不管从哪来，都**归一化**成同一种模具组件（CSS 加作用域、缩放约定、去掉 JS、状态用 class、标出锚点），再过**质检**（和参考图做画面差分、逐项数值对表）。
- **还原精度要高。** 质检沿用 zeedemo 的标准：逐项数值对表，容差 ±0.3px，加画面差分。自主模式也跑质检，不过就停下来报告，不调参压过去。
- **按集增量重建。** 第一集只重建本集用到的组件，模具随集数变厚。
- **动画按提示点对齐。** 画面挂在一条「提示点时间线」（一串带名字的时间点）上，不直接挂在词上。v1 的提示点只来自旁白的词，所以 v1 每集必须有旁白；重新配音后重新生成即自动对齐。以后加字幕或音乐节拍作为提示点来源，就能做无旁白的片子，不用重写。
- **流水线五个阶段。** 定调和讲稿 → 模具（按需补组件）→ 配音 → 画面和音乐 → 审阅和发布。
- **改生成器，不改成品。** 画面由每集的生成器产出，不手改生成出的 HTML。
- **两种模式。** 共创：第一集、建模具时，每阶段停下来确认。自主：模具成熟后，给讲稿直接出到预览，只在预览处停。
- **Figma 输入。** DemoFoundry 不自己写 Figma 导入：有链接 + 只读 token 时用上游 `hyperframes figma component / asset / tokens`；有现成复刻 HTML（如 zeedemo 的 `figma-recreation/`）时直接归一化。对用户只说一句：有 Figma 就给 frame 链接并配一次 token，没有就给截图或源码。
- **预览。** 用 HyperFrames Studio，不重做播放器，不做时间线编辑器（会和「生成器是源码」冲突）。
- **发布包。** 每集固定交付：成片 MP4（1080p，可选 4K）· 字幕 SRT · 封面 PNG · 标题和简介 · 一段 GIF / 短片段。

## 6. 与 HyperFrames 的关系

DemoFoundry 架在 HyperFrames 上：HyperFrames 把 HTML 渲染成视频，DemoFoundry 负责「怎么为一个产品持续生产这些 HTML」。

- 命令行不用单独装（`npx` 锁版本自动下载）；HyperFrames 的 skill 由锁文件一条命令恢复；系统要有 Node 22+、Python、ffmpeg。
- **强绑定**：生成的 HTML 合成格式；预览、检查、渲染。**中等**：配音和转写调用、人声避让属性、上游动效 skill。**不绑定**：模具、质检、技法卡片、录屏和素材工具、工作台、按词对齐的方法。
- 策略：接受依赖、锁版本、加回归测试；把输出 HyperFrames 格式的代码收进一个模块，给以后换引擎留口子。不自己写渲染器，不改用 Remotion。

## 7. v1 范围

**包含**

- 模具约定和通用的界面标记层；归一化脚本和质检页
- 一集的流水线：讲稿 → 配音 → 按词对齐生成画面 → 预览 → 发布包（十二个阶段压到五个左右）
- 两个 skill（建模具、做一集），共创和自主两种模式，初始化命令
- 现有 ①–⑪ 技法卡片和一批场景级函数（「点按钮 → 面板展开 → 输入 → 结果揭晓」这类）
- 配音来源可插拔：导入（默认）、一个本地免费引擎、ElevenLabs；转写按平台选引擎
- BGM：导入用户上传 + 借用上游 `media-use`（曲库、生成），记录来源和授权；人声避让与系列音量比例
- 工作台开源版（看板、模具浏览、预览入口）
- 示例：以**项目自己的工作台**为产品做两集，兼作上手教程
- 用项目自己做的宣传片（16:9，9:16 加分）
- 回归测试：测试小集重新生成，和已提交产物比对

**不包含（进待办池）**

给用户产品做的快节奏宣传片 · 无旁白模式（字幕或节拍作提示点） · 封面模板 · 改前改后逐帧取证 · 竖版正式支持 · 剪映导出 · 时间线编辑器 · 自己做音乐生成和曲库对接 · 更多配音平台 · 声明式 JSON · TypeScript 重写 · MCP

## 8. 计划表

按依赖排序，不定日期。完成标准过了再往下走。状态：⬜ 未开始 · 🔄 进行中 · ✅ 完成 · ⏸ 暂缓

| 阶段 | 做什么 | 完成标准 | 量 | 状态 |
| --- | --- | --- | --- | --- |
| P0 立项 | 建仓库；验证 skills CLI 多 skill 安装和锁文件恢复；定 skill 目录与初始化后的视频目录结构 | 一个占位 skill 能从仓库一句话装上 | 小 | ✅ |
| P1 清单与约定 | 逐函数标注 `zgen.py`、`zui.py`、工具脚本（通用 / 去品牌 / 专有）；模具约定草案；发布包规格 | 三份文档认可 | 小 | 🔄 |
| P2 引擎抽取 | 通用代码搬入；片头片尾去品牌、可换主题；HyperFrames 输出收进一个模块；脚本改用 `uv`；与 Zeemo 无关的测试小集作回归基准 | 测试小集能生成、`check` 通过、回归测试跑通 | 中 | ⬜ |
| P3 配音与音乐 | 配音来源接口；转写引擎按平台；BGM 两条路线 + 授权记录；产出 SRT | 测试小集不花钱、在 Windows 上从讲稿跑到成片 | 中 | ⬜ |
| P4 两个 skill | 建模具（`product-ui-rebuild` 泛化 + 归一化 + 质检）；做一集（`zeemo-tutorial` 泛化，两种模式）；初始化命令 | 空仓库装 skill → 初始化 → 出预览，全程无需手工干预 | 大 | ⬜ |
| P5 工作台开源版 | 重新设计并定功能范围；从仓库文件自动读数据；看板、模具浏览、预览入口；`serve.py` 并入；做成可选安装 | 界面冻结，可作拍摄对象 | 中 | ⬜ |
| P6 示例两集 | 「从零开一个系列」「重建并质检一个组件」；记录重建耗时、质检通过率、第二集省多少 | 两支成片 + 一组数字 | 大 | ⬜ |
| P7 包装 | 宣传片；README（英文为主、附中文）；技法 gallery 挂 GitHub Pages；卡片索引 `library.json` | 陌生人只看 README 就能装上并跑出第一集 | 中 | ⬜ |
| P8 发布 v1 | tag、公开仓库、找老师、各渠道推 | — | 小 | ⬜ |

**并行支线**

| 支线 | 时机 | 状态 |
| --- | --- | --- |
| 上游 PR（先提打字效果） | P2 之后 | ⬜ |
| 私下用其他产品界面试验（结果反哺约定，不进宣传） | P4 之后 | ⬜ |
| Figma 实验：同一节点跑上游导入，和现成复刻、Figma PNG 三方差分 | 有可用 Figma 文件时 | ⏸ |
| 找老师：带两分钟预览问定位、MCP 优先级、推广渠道 | 示例第一集出预览 + README 有草稿 | ⬜ |

**v1 之后的待办池**：更多场景函数和动效卡片 · 改前改后取证 · 封面模板 · 竖版 · 剪映导出 · 更多配音平台 · 社区模具 · zeedemo 改用 DemoFoundry 引擎 · 声明式描述与 MCP

## 9. To-do（近期）

- [x] 在 GitHub 建仓库：`Shuqin4712/DemoFoundry`，私有，Apache-2.0（2026-10-03）
- [ ] 查 DemoFoundry 的商标和域名
- [x] 验证 skills CLI：一个仓库多个 skill 的安装；`skills-lock.json` 的恢复命令（2026-10-03，结论见 §11）
- [x] 定 skill 目录结构和初始化后的视频目录结构（2026-10-03，见 §4）
- [ ] 抽取清单：逐函数标注 `zgen.py`、`zui.py`、`shared/tools/*.py`（草稿 [p1-inventory.md](p1-inventory.md)，待认可）
- [ ] 模具约定草案：组件、缩放、锚点、质检页（草稿 [p1-mold-convention.md](p1-mold-convention.md)，待认可）
- [ ] 发布包规格：MP4、SRT、封面、文案、短片段的命名和尺寸（草稿 [p1-publish-spec.md](p1-publish-spec.md)，待认可）
- [ ] 选型：本地免费配音引擎；ElevenLabs 等平台是否返回逐字时间戳
- [ ] 选型：转写引擎按平台（Windows faster-whisper、Mac Parakeet）
- [ ] 确认 `media-use` 的 BGM 路径在没有 HeyGen 账号时能做到什么程度
- [ ] 确认工作台能否代为启动某一集的 Studio 预览
- [ ] 写测试小集的讲稿（与 Zeemo 无关，30 秒左右）
- [ ] P4：初始化时在 `demofoundry/` 里写 `.gitattributes`（`* text=auto eol=lf` + 媒体文件 binary）

## 10. 决策记录

| 日期 | 决定 | 理由 |
| --- | --- | --- |
| 2026-10-02 | 定位改为「重建产品界面 → 批量出系列片」，`gen.py` 降为实现手段 | 原定位只有 HyperFrames 工程师听得懂 |
| 2026-10-02 | 不做「截图当底板」路线，录屏截图只作重建证据 | 那条路的终点是 Screen Studio，且它做得更好 |
| 2026-10-02 | 用户：会用 agent、有产品、要批量出片的独立开发者和小团队 | — |
| 2026-10-02 | 预览用 HyperFrames Studio，不做时间线编辑器 | 和「生成器是源码」冲突；播放器无差异化 |
| 2026-10-02 | 接受 HyperFrames 依赖，锁版本，绑定收进一个模块 | Apache-2.0、本地渲染无账号；自研渲染器或换 Remotion 代价过大 |
| 2026-10-02 | v1 解开配音绑定：导入为默认，加本地免费引擎，HeyGen 可选 | HeyGen 要账号和额度，是开源用户唯一会卡住的地方 |
| 2026-10-02 | 公司许可不是前置条件 | 项目由本人所有 |
| 2026-10-03 | Zeemo 成片不作为案例 | — |
| 2026-10-03 | v1 同时提供共创和自主两种模式 | 只有逐阶段确认对批量出片太重 |
| 2026-10-03 | 形态改为「装 skill，在产品仓库里建工作室」 | 安装体验；还能直接读产品源码做重建 |
| 2026-10-03 | 配音来源可插拔（导入 / 本地免费 / 平台 API，用户自己的 key） | 平台多、用户各有偏好；接口留给社区贡献 |
| 2026-10-03 | BGM 走多种路线并移进 v1 | 上游 `media-use` 已覆盖大部分；没有音乐的宣传片会很弱 |
| 2026-10-03 | 示例产品用项目自己的工作台 | 无授权和对方改版风险；示例兼作上手教程 |
| 2026-10-03 | 「任何产品都能用」靠私下用其他产品试验来证明，不进宣传 | — |
| 2026-10-03 | 名字暂定 DemoFoundry | GitHub 仅 1 个同名仓库，npm / PyPI 未占用；模具 / 浇铸的比喻贴合 |
| 2026-10-03 | v1 用 Python | 现有约 2500 行已验证；音频图像生态在 Python；输出是 HTML，语言不影响产物 |
| 2026-10-03 | 自有 skill 和上游 PR 并行 | — |
| 2026-10-03 | Figma 实验暂缓 | 没有那个 Figma 文件的权限 |
| 2026-10-03 | 仓库先私有，v1 发布时公开 | — |
| 2026-10-03 | v1 只做带旁白的教程 / 演示片系列，用户产品的宣传片不在 v1 | 做小做精 |
| 2026-10-03 | v1 每集必须有旁白；画面挂在「提示点时间线」上，给无旁白模式留口子 | 教程 / 演示片需要旁白；不是所有用户都要配音，以后扩展不必重写 |
| 2026-10-03 | 一切英文为主，README 附中文 | 目标是更多人 star 和使用 |
| 2026-10-03 | 还原精度保持高标准（±0.3px + 画面差分），自主模式也跑质检 | 界面还原是核心卖点 |
| 2026-10-03 | 用户最好不碰代码，但生成器不写死、可读可改 | — |
| 2026-10-03 | 流水线定为五个阶段 | 十二个阶段对批量出片太重 |
| 2026-10-03 | zeedemo 不受影响，v1 前不做双向同步 | — |
| 2026-10-03 | 工作台可插拔（可选安装），重新设计，功能范围 P5 再定 | 出片不该依赖它；它是示例集的门面 |
| 2026-10-03 | skill 不按系统分支，平台差异由脚本内部消化；转写默认 faster-whisper | 一般 skill 不区分系统；Parakeet 只能在 Apple 芯片上跑 |
| 2026-10-03 | 上游 HyperFrames skill 用 `heygen-com/hyperframes#<tag>` 锁版本，tag 和 HyperFrames 命令行版本一致；skills CLI 本身也锁版本（`npx skills@1.7.0`） | 不写 ref 的锁文件恢复时会装成上游最新版（实测） |
| 2026-10-03 | 三个 skill：`demofoundry`（引擎、初始化、入口）、`demofoundry-mold`、`demofoundry-episode`；后两个用 `../demofoundry/` 引用引擎。v1 仍是「建模具、做一集」两个工作流 | skills CLI 只复制 skill 自己的文件夹，两个 skill 共用的引擎必须住在某个 skill 里（实测）；HyperFrames 也用兄弟路径互相引用 |
| 2026-10-03 | DemoFoundry skill 默认装在项目级 | 随产品仓库提交，每个仓库锁自己的引擎版本；也是 CLI 默认 |
| 2026-10-03 | 产品仓库里的视频目录叫 `demofoundry/` | — |
| 2026-10-03 | 安装命令不加 `--copy`，README 不提开发者模式 | CLI 在 Windows 上建 junction（不需要开发者模式或管理员），失败时自动改为复制（读源码 + 实测） |
| 2026-10-03 | 文本文件统一 LF：DemoFoundry 根目录加 `.gitattributes`（`* text=auto eol=lf`，媒体文件标 binary）；初始化时在用户的 `demofoundry/` 里写一份只管该目录的 `.gitattributes`；引擎写文本文件显式用 LF | 回归测试和「生成器有没有改出差异」要逐字节比对，Windows 的 `autocrlf` 会把签出的文件转成 CRLF；只管 `demofoundry/` 目录，不动用户仓库根目录和全局配置 |
| 2026-10-03 | 连线几何（`wire_between` / `bez_len` 的算法）在引擎里重写一份，端点外移量作参数；`zui.py` 仍不搬 | 纯几何、和 Zeemo 样式无关，节点编辑器类产品都用得上 |
| 2026-10-03 | 切点检测（`media.py`）和 `measure-reference.py` 不进 v1 | v1 流程用不上；减少依赖（OpenCV） |
| 2026-10-03 | 模具前缀在初始化时从产品名生成，写进 `mold.json`，之后不改 | 类名和缩放变量都带前缀，中途改代价大 |
| 2026-10-03 | 产品字体：能再分发的放 `mold/theme/fonts/`，不能的进 `.gitignore`，README 写取得方式 | 商用字体常不许再分发 |
| 2026-10-03 | 成片默认 60fps，响度 −16 LUFS ±1、真峰值 ≤ −1 dBTP | zeedemo 已发布成片实测如此，听感和流畅度已验证 |
| 2026-10-03 | 发布包里的 MP4 / GIF 默认不提交进 git | 体积大，可从源码重新渲染 |
| 2026-10-03 | v1 封面只做一个默认版式；多版式封面模板仍在待办池 | 发布包要封面，但不扩大 v1 范围 |
| 2026-10-03 | 模具的组件标记用 Python 函数（`mold/ui.py`，沿用 zeedemo `zui.py`），锚点常数和组件写在一起；验收页由同一套函数生成（沿用 `video-node.gen.py`），另加锚点验收 | 锚点和组件内部尺寸都要计算；zeedemo 六集实际在用；标记只存一份 |
| 2026-10-03 | 初始化时用 `skills add <源>#<tag> --skill … --agent claude-code codex -y` 装上游 skill，不依赖 `experimental_install` | 恢复命令只装到 `.agents/skills/`，Claude Code 读不到（实测） |

## 11. 待验证与风险

| 项 | 影响 | 怎么消解 |
| --- | --- | --- |
| ~~skills CLI 能否一句话装多个 skill、恢复上游 skill~~ | 安装体验 | 已验证（2026-10-03），见下方「skills CLI 实测」 |
| 换一个产品，重建要多久、质检能否稳定通过 | 核心价值是否成立 | P6 数字 + 私下试验 |
| HyperFrames 还在 0.8.x，升级可能破坏输出 | 维护成本 | 锁版本 + 回归测试 |
| 上游 Figma 导入的质量 | v1 的 Figma 路径是否可靠 | Figma 实验（暂缓） |
| Node + Python 双环境门槛 | 新用户流失 | `uv` + 初始化时环境检查 |
| 只在 Windows 上验证（手头没有 Mac） | 跨平台问题 | 平台差异收在脚本内部（见下）；发布前找 Mac 用户试，或 CI |

**skills CLI 实测**（`skills@1.7.0`，Windows，2026-10-03）

| 问题 | 结论 |
| --- | --- |
| 一个仓库多个 skill | 可以。CLI 找出仓库里所有 `SKILL.md`；`--skill a b` 或 `--skill '*'` 一句装多个；`--list` 只列不装 |
| 装进去的是什么 | **只复制 skill 自己那个文件夹**。仓库顶层的共享目录（如 `engine/`）不会装进去；skill 文件夹里的子目录会 |
| 装到哪 | 只选 Claude Code 时直接复制到 `.claude/skills/<name>`；选多个 agent 时，正本放在 `.agents/skills/<name>`，`.claude/skills/<name>` 是指向正本的目录符号链接（本机能建；没开开发者模式的 Windows 用 `--copy`） |
| 私有仓库 | 用本机 git 凭据克隆，和公开仓库同一条命令。`npx skills add Shuqin4712/DemoFoundry --skill '*' --agent claude-code codex -y` 装上三个占位 skill，`../demofoundry/engine/` 在 `.claude/skills/` 下也能找到 |
| 锁文件锁不锁版本 | **不写 ref 就不锁**。zeedemo 的 `skills-lock.json` 没有 ref，恢复时 26 个 skill 全装成上游最新版，哈希全变，锁文件也被改写。安装源写成 `heygen-com/hyperframes#v0.8.110` 时，锁文件会记下 `"ref"`，删掉重装后文件哈希一致 |
| 恢复命令 | `npx skills experimental_install`。**只装到 `.agents/skills/`**（Codex、Cursor 等 universal agent），会忽略 `--agent`，不给 Claude Code 建 `.claude/skills/` |
| 上游 skill 之间怎么共享文件 | HyperFrames 的 skill 直接用相对路径引用兄弟 skill（如 `../hyperframes-core/references/...`），前提是一起装 |

**已知的 Windows / Mac 差异**（原则：skill 不按系统分支，脚本内部消化）

| 差异 | 现状 | 处理 |
| --- | --- | --- |
| 命令名：`python` / `python3`，`npx.cmd` / `npx` | zeedemo `voice.py` 在 Windows 上调不到 `npx` | 脚本里统一查找可执行文件，或用 `uv` 统一入口 |
| 转写引擎 | zeedemo 写死 Parakeet，只能在 Apple 芯片上跑 | 默认 faster-whisper（两边都能用），Parakeet 作 Mac 可选加速 |
| 符号链接 | zeedemo 靠符号链接共享组件库，Windows 需开发者模式 | 新形态引擎住在 skill 目录，不用符号链接；skills CLI 在 Windows 上用 junction，失败自动复制 |
| 硬编码路径 | `cover.py` 写死无头浏览器路径格式 | 跨平台查找 |
| 临时空间 | Windows 的 C 盘常常不够 4K 渲染 | 临时目录可配置 |
| 控制台编码 | 中文 Windows 默认不是 UTF-8 | 脚本输出显式用 UTF-8 |
| 换行符 | Windows 的 `autocrlf=true` 签出时转 CRLF | `.gitattributes` 统一 LF；脚本写文件显式用 LF |

## 12. 参考

- 设想文档（讨论过程）：<https://claude.ai/code/artifact/2217212a-3639-4cf0-a3a9-ea7172a8bcf9>
- 来源仓库 zeedemo（Zeemo 教程系列生产仓库，`D:\zeedemo\zeedemo`）：`shared/gen/`、`shared/tools/`、`shared/techniques/`、`workbench/`、`.claude/skills/product-ui-rebuild/`、`.claude/skills/zeemo-tutorial/`
- HyperFrames：<https://github.com/heygen-com/hyperframes>（Apache-2.0）
- video-shotcraft：<https://github.com/Vincentwei1021/video-shotcraft>（README 结构、安装方式、多模式、卡片索引可借鉴）
