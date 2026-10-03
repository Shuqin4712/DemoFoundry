# P1 · 抽取清单

> 状态：**草稿 v2，待认可**（2026-10-03）。v2 在通读 zeedemo 全仓库后补了 §8–§9，修正了 `word_time`
> 范围：zeedemo 的 `shared/gen/zgen.py`、`shared/gen/zui.py`、`shared/tools/*.py`，逐函数标注；其余来源按文件列在最后。
> 读法：这份清单只回答「搬不搬、怎么搬」，具体搬的动作在 P2 做。

## 0. 全部工具一览

`D:\zeedemo` 下除上游 HyperFrames skill 以外的全部脚本，共 35 个文件（2026-10-03 全盘搜索，含未提交和被 gitignore 的目录；`zeedemo-main` 是空目录，第七集备份目录不算）。按用途排，后面各节逐个标注。

| 用途 | 文件 | 能做什么 | 本清单 |
| --- | --- | --- | --- |
| 读录屏 | `shared/tools/recording.py` | `index`：找出界面每个状态在第几秒（时间中值滤掉光标、屏蔽一直在播的区域）→ 总览图 + 状态表 + JSON；`crop`：按像素框或按第 N 个变化裁证据图 | §5 |
| 量截图 | `product-ui-rebuild/scripts/ref_profile.py` + `png.py` | 截图 → JSON：卡片包围盒（亚像素）、圆角、边框、面色、标题栏墨迹与笔画宽、结构骨架、暗色内容块、主色簇 | §7a |
| 建组件库骨架 | `product-ui-rebuild/scripts/new_library.py` | 铺 tokens / index / README / 两个验收页 / 工具 | §7a |
| 验收页里的测量 | `product-ui-rebuild/assets/proof-template.html`（JS） | `INK` 墨迹高、`STEM` 笔画宽、`INKW` 字号 + 字间距最小二乘、`WRAP` 逐行断点；`solve()` 反解 CSS 常数；`recheck()` 重算对表 | §7a |
| 验收页生成 | `shared/proof/video-node.gen.py` | 调 `zui.py` 生成验收页，组件和录屏裁图并排 | §9 |
| Figma 复刻自检 | `reference/ui/*/figma-recreation/structure.test.mjs`（3 个） | 检查复刻页保留了 Figma 节点 id、画板尺寸、文案、素材 | §9 |
| 探针 / 量合成 | `make-fingerprint.py`（包装）+ `product-ui-rebuild/scripts/make_fingerprint.py` | 把子合成变成可单独驱动的页，严格 seek 后读几何 | §6、§7a |
| 静态服务 | `shared/tools/serve.py`、`product-ui-rebuild/scripts/serve.py` | 不缓存的静态服务（两份相同） | §6 |
| 配音 | `shared/tools/voice.py` | 生成 / 导入录音 → 转写对齐 → 逐词核对 → 量停顿 → 补破折号 → 在真实静音处切段 → 排布 → 预览 + 响度；`promote` 定稿 | §3 |
| 演示素材 | `shared/tools/media.py` | 规格警告、改前改后逐帧比对、切点、改动区域、静帧 / 播放片段 / 胶片条 / 放大镜、对照总览 | §4 |
| 音乐 | `videos/…image-node/_build/bgm-extend.py`；`…ugc-ad/assets/bgm/compose.py` | 按乐句接长曲子；代码合成音乐（试验，被否） | §9 |
| 量参考片 | `shared/techniques/measure-reference.py` | 平均镜头长、静止占比、运镜（平移 / 缩放 / 旋转）、切点判定、动作事件 | §6 |
| 技法卡片 | `shared/techniques/_beat.js`（+ 三张 catalog HTML） | 卡片渲染器：同一时钟循环、单帧步进、调速 | §7 |
| 生成器 | `shared/gen/zgen.py`、`shared/gen/zui.py`、各集 `_build/gen.py`（6 个） | 时间轴、镜头、光标、片头片尾、主时间轴；界面标记；每集画面 | §1、§2、§8 |
| 连线几何（JS） | `shared/assets/canvas-ui/wire.js` | `wireBetween` / `wire`：水平进出的贝塞尔连线 | §7a |
| 开集 | `shared/tools/new-episode.py` | 从骨架模板建一集、建链接、可复制上一集生成器 | §6 |
| 进度 | `zeemo-tutorial/scripts/status.py`（`.claude` 和 `.agents` 各一份，相同） | 按文件判断一集做到哪个阶段 | §9 |
| 封面 | `shared/tools/cover.py` | `cover.json` → 模板 → 无头 Chrome 截图 | §6 |
| 工作台 | `workbench/server.py`、`test_server.py`、`dist/app.js` | 本地看板、资料索引、进度与日志保存 | §7（P5） |

zeedemo 调用、但不是自己写的（上游 HyperFrames skill / CLI）：`media-use/audio/scripts/heygen-tts.mjs`（HeyGen 配音）、`hyperframes-audio/scripts/carve.mjs`（人声避让）、`motion-doctrine/scripts/seam-stamp.mjs` / `seam-gate.mjs`（接缝登记与检查）、`npx hyperframes check / preview / render / snapshot / transcribe / tts`。这些不搬，通过锁版本的上游调用。

## 标注

| 标注 | 意思 | P2 怎么处理 |
| --- | --- | --- |
| **通用** | 和 Zeemo 无关，换个产品原样能用 | 搬进引擎；顺手修 Windows / 编码问题、改英文注释 |
| **去品牌** | 机制通用，但写死了 Zeemo 的名字、logo、配色、字体、网址或数值 | 搬机制，品牌部分改成从 `demofoundry.json` / 模具主题读 |
| **改造** | 通用，但要按已定决策改接口（配音来源可插拔、提示点时间线、跨平台） | 搬进引擎，按「改法」一栏改 |
| **专有** | Zeemo 产品界面或 Zeemo 系列专属 | 不搬。需要的话只提炼成约定 |
| **暂缓** | 通用，但对应的功能不在 v1 | 不搬，记进待办池 |

## 跨文件的共性问题（P2 统一修）

| 问题 | 出现在 | 改法 |
| --- | --- | --- |
| `open()` 不带 `encoding`，写文件不指定换行 | `zgen.write / write_json / load_json`，`cover.py`、`carve` 等 | 统一走引擎的 `io` 模块：UTF-8 + LF（决策记录 2026-10-03） |
| 画幅写死 1920×1080（`960` / `540` / `2080` / `1180` 散落在各处） | `Camera.scr / init_state / emit_moves`、`Cursor.init_state / enter / exit`、`index_html`、`end_card` | 画幅从配置读；屏幕中心、画外入场点按画幅算 |
| 调 `npx` 在 Windows 上找不到（要 `npx.cmd`） | `voice.transcribe` | 引擎统一的可执行文件查找（PROJECT §11 差异表） |
| 路径按 zeedemo 仓库结构硬算（`ROOT = 上三级`、`.agents/skills/...`、`shared/assets/...`） | `voice.py`、`cover.py`、`new-episode.py`、两个薄包装 | 引擎住在 skill 目录：skill 内资源按 `__file__` 找；用户数据按 `demofoundry/` 根找 |
| 同一组小工具重复了三份（`die / run / probe / save_png`） | `media.py`、`recording.py`、`product-ui-rebuild/scripts/png.py` | 合成一个 `media` 工具模块 |
| HyperFrames 版本锁在 0.8.34（集模板的 `package.json`），上游已到 0.8.114 | 集模板 | P2 选定一个版本，和上游 skill 的 tag 一起锁（决策记录 2026-10-03） |

## 1. `shared/gen/zgen.py`（452 行）

| 函数 / 类 | 做什么 | 标注 | 改法 / 备注 |
| --- | --- | --- | --- |
| `write` / `write_json` / `load_json` | 读写文件 | 通用 | UTF-8 + LF |
| `load_words` | 读 `words.json` | 通用 | |
| `word_time` | 词 → 时间（取第一次出现） | **改造** | 每集都包一层 `W(片段, 词)`，按旁白片段限定范围，跨片段重名不会取错；`TIMELINE.md` 的「关键词 → 画面事件」表就是提示点时间线。改造成具名提示点，把这张表变成数据：`cue('sec2', 'Character')`，同片段内重复的词用序号区分 |
| `wav_duration` | wav 时长 | 通用 | |
| `Timeline` | 收集 GSAP 行，支持整体平移 `offset` | 通用 | 放进「HyperFrames 输出模块」（PROJECT §6） |
| `Camera` | 镜头表 + 移动序列；光标操作时镜头在动直接报错 | 通用 | 画幅参数化；`ease` 默认值留着 |
| `CURSOR_CSS` / `CURSOR_SVG` | 96px 白色箭头光标 | 去品牌 | 尺寸、颜色进主题（默认值可以就用现在这套） |
| `Cursor`（`enter / to / screen / press / release / click / exit`） | 光标入场律、点击 1:2 节奏 | 通用 | 画幅参数化 |
| `Cursor.drag_wire` | 从节点出口拖出连线 | 通用 | 只对节点编辑器类产品有用，留着当场景函数 |
| `ellipse_pts` / `path_d` / `path_len` / `draw` | 手绘椭圆笔迹、描线 | 通用 | |
| `wipe` | 扫光揭晓（改前 → 改后） | 通用 | |
| `typing_html` / `typing_init` / `typing` | 逐字打字 | 通用 | 上游 PR 的第一个候选（PROJECT §8 支线） |
| `fly` | 缩略图飞入（⑦ 三段） | 通用 | |
| `INTRO_CSS` / `intro_html` / `intro_timeline` | 系列片头：胶囊标签随关键词浮现、退场、主元素入场 | 去品牌 | 配色、字体、发光色进主题；文案和关键词从讲稿来；`last_word='Canvas'` 默认值去掉 |
| `intro_stars` | 星点爆开、落到画布点阵格点 | 去品牌 | 落点绑定了 Zeemo 画布点阵（48px 格）。改成可选的「片头背景」之一，没有点阵的产品落到中心或不用 |
| `end_card` | 片尾卡：logo + CTA + 网址胶囊 + Powered by | 去品牌 | logo、网址、配色、字体全进主题；**字体路径指向 `assets/canvas-ui/edit/fonts/`（不搬的目录）**，要换 |
| `bgm_length_check` | BGM 长度和片长对不上就报警 | 通用 | 路径参数化 |
| `carve` | 存 / 回填人声避让属性 | 通用 | 属于 HyperFrames 绑定，放进输出模块；依赖上游 `hyperframes-audio` 的 `carve.mjs` |
| `index_html` | 主时间轴：场景挂载、配音组、BGM、系列角标 | 去品牌 | 角标文字 / logo、背景色、字体、混音比例（0.75 / 0.32）进配置；画幅参数化 |

**小结**：除了片头片尾和主时间轴三处去品牌，全部可搬。zeedemo 已经是「每集 gen.py 只写本集数据、公共部分进库」的结构，DemoFoundry 引擎沿用它。

## 2. `shared/gen/zui.py`（559 行）

按 AGENTS.md 不搬这个文件。它整个是 Zeemo 界面的 HTML 标记，下面只标出**值得提炼成约定或重写进引擎的几处**，其余一律专有。

| 函数 / 常数 | 标注 | 提炼什么 |
| --- | --- | --- |
| `icon` | 专有（写法通用） | 引擎自己写一个同样的小助手，不搬原文件 |
| `wire_between` / `bez_len` / `Wires` | 专有（几何通用） | 「两个矩形之间的水平进出贝塞尔线 + 长度 + 描线」对所有节点编辑器类产品通用。**建议在引擎里重写一份几何函数**（端点外移量作参数），不带 Zeemo 的样式类名 —— 需要你确认，见文末待定 |
| `TB_H`、`NODEBAR_W`、`NB_VAR`、`VMENU_ITEM`、`BAR_GEN`、`GMENU_ITEM_IMAGE`、`PORT_R` 等几何常数，`nb_pos` | 专有 | **这就是「锚点」**：按钮中心、菜单行中心相对组件左上角的位置。现在散落成 Python 常数，模具约定里改成组件元数据的一部分，见 [模具约定](p1-mold-convention.md) §5 |
| 各组件函数统一的 id 规则（`<nid>-label / -card / -badge`、`<pid>-gen`） | 专有 | 提炼成约定：组件实例的子元素 id = `<实例 id>-<部位>`，动画按这个 id 找元素 |
| `data-layout-ignore` 的用法（菜单盖住卡片是产品真实行为） | 专有 | 提炼成约定：组件元数据里标「允许遮挡」，生成时自动加 |
| `listing_page` / `film_frame` | 专有 | 讲解性示意（电商详情页、电影画幅），不是 Zeemo 界面，但 CSS 在不搬的 `canvas-ui/explainer/`。v1 不做，以后可以做成场景函数 |
| 其余（`image_node`、`nodebar_*`、`gen_panel`、`model_pop`、`param_pop`、`history_panel`、`video_*` 等，全文件共 44 个函数和类） | 专有 | — |

## 3. `shared/tools/voice.py`（561 行）

配音流水线：生成 → 逐词核对 → 量停顿 → 补破折号停顿 → 按静音切段 → 排布 → 预览。**主体是 v1 配音的核心，几乎全部可搬。**

| 函数 | 标注 | 改法 / 备注 |
| --- | --- | --- |
| `read_wav` / `write_wav` / `read_words` / `write_words` | 通用 | |
| `load_spec` | 改造 | `engine` 字段只认 `heygen` / `canvas-tts`，改成配音来源接口：`import`（默认）/ 本地免费引擎 / `elevenlabs`（决策记录 2026-10-03） |
| `norm` / `tokens` / `word_index` / `verify` | 通用 | 分词按英文写的（v1 英文为主，够用） |
| `silence_runs` / `gap_run` / `pause_report` | 通用 | |
| `fill` / `pad_dashes` | 通用 | |
| `split` | 通用 | |
| `make_layout` / `preview` | 通用 | 依赖 ffmpeg |
| `cmd_tts` | 专有 | 调 HeyGen（经 `media-use` 的 `heygen-tts.mjs`），还带本机代理变量。改成「平台 API 来源」的一个实现，HeyGen 可选 |
| `trim_edges` | 通用 | |
| `transcribe` | 改造 | 现在先试 Parakeet、失败再退 faster-whisper。按决策改成默认 faster-whisper，Parakeet 作 Mac 可选加速；修 `npx.cmd` |
| `whisper_python` / `transcribe_whisper` | 改造 | 写死 `~/.venvs/whisper`；改成 `uv` 管理的环境 |
| `align` | 去品牌 | `squash` 里写死了 `zemo → zeemo`。改成配置里的「专有名词别名表」 |
| `find_recordings` / `split_joint` / `cmd_import` | 通用 | **导入是 v1 默认来源**，这几个就是它的实现。文件命名（`sec0.mp3`、连录 `sec0-1.mp3`）来自 Zeemo Audio Node，改成按 `voice.json` 段落名，保留连录自动切开 |
| `restrict` / `cmd_measure` / `cmd_build` / `cmd_layout` / `cmd_promote` / `main` | 通用 | |

## 4. `shared/tools/media.py`（399 行）

演示素材预处理。为 Zeemo「改前改后」类视频编辑功能写的，大半是取证，不在 v1。

| 函数 | 标注 | 改法 / 备注 |
| --- | --- | --- |
| `run` / `probe` / `frame_count` / `gray_frames` / `rgb_frame` / `save_png` / `extract_frames` | 通用 | 和 `recording.py` 合并成一个工具模块 |
| `load` / `pair_by` | 暂缓 | 跟着取证走 |
| `cmd_probe` | 暂缓 | 规格表通用，但警告写死了 Zeemo 节点宽 `NODE_W = 465` |
| `cmd_diff` / `curve` | 暂缓 | 改前改后逐帧比对 = 待办池「改前改后取证」 |
| `detect_cuts` / `cmd_cuts` | 通用 | 帧精确切点。v1 用不上，P2 可以不搬 |
| `color_mask` / `smooth` / `largest_component` / `cmd_region` / `overlay` | 暂缓 | 改动区域定位，属于取证 |
| `cmd_assets`：静帧、播放片段 | 通用 | 「把产品产出的图 / 视频放进界面」用得上，搬 |
| `cmd_assets`：胶片条、放大镜 | 专有 | Zeemo 编辑面板专用 |
| `contact_sheet` | 暂缓 | 取证 |

## 5. `shared/tools/recording.py`（237 行）

产品录屏 → 界面状态时间表 + 总览图 → 按框裁证据图。**全部通用**，是「录屏作为重建证据」这条路的入口，归建模具 skill 用。

| 函数 | 标注 | 备注 |
| --- | --- | --- |
| `run` / `probe` / `save_png` | 通用 | 合并进工具模块 |
| `analyse` / `group` | 通用 | 分析宽度 519 是按 zeedemo 的 2076 宽录屏取的，改成按录屏宽度算 |
| `label` / `overview` | 通用 | |
| `cmd_index` / `cmd_crop` / `main` | 通用 | 输出 `states.md` 是中文表头，改英文 |

## 6. 其余工具脚本

| 文件 | 标注 | 备注 |
| --- | --- | --- |
| `cover.py`（113 行） | 去品牌 | 机制通用：读 `cover.json` → 填 HTML 模板 → 无头 Chrome 截图。模板在 `shared/assets/cover/`，是 Zeemo 品牌，不搬。`chrome()` 查找 HyperFrames 下载的无头 Chrome，通用。v1 封面怎么做见 [发布包规格](p1-publish-spec.md) §4 |
| `new-episode.py`（97 行） | 改造 | 拆成 `init`（建 `demofoundry/`）和「开一集」两步；不再建符号链接（引擎住在 skill 目录）；`--gen-from` 复制上一集生成器的做法保留 |
| `make-fingerprint.py`、`ref-profile.py` | 通用 | 只是薄包装，实现在 `product-ui-rebuild/scripts/`，搬实现、不搬包装 |
| `serve.py` | 通用 | 不缓存的静态服务。P5 并入工作台；`product-ui-rebuild/scripts/` 里还有一份副本，合成一份 |
| `shared/techniques/measure-reference.py`（249 行） | 通用 | 量参考片的节奏、运镜。依赖 OpenCV（重），做成可选依赖 |

## 7. 不在逐函数范围、P2 / P4 要一起搬的

| 来源 | 标注 | 去哪 |
| --- | --- | --- |
| `.claude/skills/product-ui-rebuild/`（SKILL.md、`scripts/` 5 个、`references/` 3 份、`assets/` 两个验收页模板） | 通用 | `demofoundry-mold`。已经很通用；`worked-example.md` 写的是 Zeemo 案例，换成示例集的案例 |
| `.claude/skills/zeemo-tutorial/` | 去品牌 | `demofoundry-episode` 的起点（P4） |
| `shared/techniques/`（技法卡片 ①–⑪、`_beat.js / _beat.css`） | 通用 | `demofoundry/techniques/`；`catalog-camera.html` 和 `catalog-compose.html` 引用了 Zeemo 界面，演示对象要换 |
| `shared/templates/episode/`（BRIEF / SCRIPT / STORYBOARD / TIMELINE / AGENTS.md 等） | 去品牌 | `demofoundry/templates/`；标题后缀 `| Zeemo Canvas Tutorial`、链接、话题标签都在里面 |
| `shared/docs/SERIES-WORKFLOW.md` | 去品牌 | 十二个阶段压成五个后，拆进两个 skill 的 SKILL.md 和 references |
| `workbench/`（`server.py`、`test_server.py`、`dist/`） | — | P5 重新设计时再标注 |
| 上游脚本：`carve.mjs`（`hyperframes-audio`）、`seam-stamp.mjs` / `seam-gate.mjs`（`motion-doctrine`） | 不搬 | 通过锁版本的上游 skill 调用。注意 `motion-doctrine` 在上游仓库的 `.agents/skills/` 下（不是 `skills/`），算上游内部 skill，接口稳定性要在 P2 确认 |

## 7a. `product-ui-rebuild` 的脚本与验收页 JS，`wire.js`

整个 skill 已经很通用，归 `demofoundry-mold`。

| 文件 / 函数 | 标注 | 改法 / 备注 |
| --- | --- | --- |
| `png.py`：`load`（无依赖 PNG 解码）、`lum`（Rec.709 亮度）、`edge`（亚像素边缘内插） | 通用 | `load` 只支持 8 位 RGB / RGBA；可以换成 Pillow（第七集 `gen.py` 已经在用 Pillow），`edge` 保留 |
| `ref_profile.py`：`profile`（卡片 / 特写两种分支、媒体铺满判定、边框、圆角、面色交叉校验、标题栏墨迹与笔画宽、结构骨架、暗色内容块、主色簇） | 通用 | 写死了 retina 2x（`R2` 折半）和亮度阈值 16.5（按 Zeemo 深色界面定的）。改成按截图倍率和地面亮度自动取；浅色界面的产品要另测 |
| `ref_profile.py` 的 `--all` 批量 | 通用 | 默认 glob `reference/ui/*/*.png` 改成模具证据目录 |
| `new_library.py` | 改造 | 建模具骨架的起点。改成按模具约定 v2 的目录（`ui.py`、`proof/<子库>.gen.py`、`evidence/<功能>/`）铺 |
| `make_fingerprint.py` | 通用 | 带「拒绝覆盖非点号文件」的护栏（曾覆盖过生产合成），保留 |
| `serve.py` | 通用 | 和 `shared/tools/serve.py` 合成一份 |
| `assets/proof-template.html`：`INK` / `STEM` / `INKW` / `WRAP` / `solve()` / `recheck()`、按时间戳逐个 `<link>` 防缓存 | 通用 | 截图量测验收的核心，原样搬，文案改英文 |
| `assets/gallery-template.html` | 通用 | 裸摆总览页 |
| `references/measurement.md`、`figma.md` | 通用 | 测量口径与陷阱、Figma 输入。英文化 |
| `references/worked-example.md` | 专有 | Zeemo 的 81 项对表案例，换成示例集的案例 |
| `shared/assets/canvas-ui/wire.js`：`wireBetween` / `wire` | 通用（几何） | 和 `zui.wire_between` 同一算法的 JS 版，端点外移是旧值 9（`zui` 是实测 5.75）。引擎重写连线几何时以 `zui` 版为准，JS 版给验收页用 |

## 8. 每集 `gen.py` 里反复出现的辅助函数（v1 漏掉的）

每集生成器里都有一批自己写的小函数，其中不少在 3–4 集里各写过一遍（第七集的备份目录不算）。它们就是 PROJECT §7 要的「场景级函数」的现成来源，P2 收进引擎。

| 函数 | 出现在 | 做什么 | 标注 |
| --- | --- | --- | --- |
| `reveal` | 第四到七集（4 集） | 扫光出图 + 收起「生成中」 | 通用 |
| `spin` | 第五、六、七集 | 「生成中」转圈，转速按时长算 | 通用 |
| `pop_in` / `appear` / `appear_node` | 第四到七集 | 弹层 / 节点带缩放淡入 | 通用 |
| `cls` | 第五、六、七集 | 用 `tl.set` 切 className（状态切换的标准做法） | 通用 |
| `wire` / `draw_wire` / `wire_on` | 第四到七集 | 登记连线、描线长出、直接显示 | 通用（依赖连线几何，见决策记录） |
| `hl_box` / `hl_on`，`hl_dash` / `hl_dash_box` | 第五、六、七集 | 讲解用的虚线描框，顺时针画出 | 通用 |
| `line_hl` | 第七集 | 文本整行高亮 | 通用 |
| `swap` | 第七集 | 同一时刻换两层：分开 hide / show 哪怕差 0.01s，60fps 下会空一帧导致频闪（2026-09-30 成片实测） | 通用，**必须进引擎** |
| `dim` | 第七集 | 压暗不在讲的部分 | 通用 |
| `pulses` | 第七集 | 连线上的能量流光点 | 通用 |
| `halo` / `glow_reveal` | 第七集 | 节点背光，颜色从图片主色自动取（依赖 PIL） | 通用 |
| `video_block` / `video_or_ph` | 第七集 | 节点里的视频：首帧 / 末帧叠层、每段只播一遍不循环 | 通用 |
| `placeholder` / `img_or_ph` / `has` / `mpath` | 第七集 | 素材还没到时画占位，放进目录后重跑即替换 | 通用 |
| `preset_flow` | 第七集 | 「点节点 → 工具条 → 下拉 → 选预设 → Generate → 新节点生成 → 出图」整套 | 场景函数的样板；里面的锚点是 Zeemo 的，机制通用 |
| 展示卡飞进节点（FLIP）、`node_screen` / `scr_rect` | 第七集 | 屏幕空间的卡片飞到某个镜头下的节点位置 | 通用；`node_screen` 和 `Camera.scr` 重复，合并 |
| `media` / `sample` / `palette` / `node` | 第二到六集 | 各集自己的素材路径、取色、节点写法 | 被 `zui.py` 和第七集的写法取代，不搬 |

另外，第七集 `gen.py` 里的**混音**也该收进引擎配置，而不是每集手写：

| 做法 | 现在在哪 |
| --- | --- |
| 旁白偏轻时每条挂 `gain +6 → limiter −1`（画布 TTS 约 −22 LUFS） | 第六、七集 `VO_CHAIN` |
| 成品原声段 BGM 让位（−7dB，压 / 回 0.9s / 1.2s） | 第七集 `fx.n4.gain` 自动化 |
| 整片音量弧线：63%–71% 下潜 −3dB、片尾卡顶起 +2.5dB | 第六、七集，追加在 carve 链后的 `n4` 节点 |

## 9. 其余漏掉的文件

| 文件 | 标注 | 备注 |
| --- | --- | --- |
| `videos/zeemo-canvas-image-node/_build/bgm-extend.py` | 通用 | 曲子比片长短时，按乐句结构在最像的位置重复几小节、交叉淡化接长，不循环硬接。和 BGM 裁剪命令（`shared/assets/bgm/README.md` 里的 ffmpeg 淡入淡出）一起做成引擎的「BGM 按片长适配」 |
| `videos/zeemo-canvas-ugc-ad/assets/bgm/compose.py` | 不搬 | 代码合成音乐的试验，用户否掉了 |
| `.claude/skills/zeemo-tutorial/scripts/status.py` | 改造 | 按文件判断一集做到哪个阶段。归做一集 skill；检查项改成五个阶段，去掉符号链接和 Zeemo 标题后缀的检查 |
| `shared/proof/video-node.gen.py` | 通用（做法） | 验收页直接调标记函数生成，标记只存一份。模具约定采用这个做法 |
| `reference/ui/*/figma-recreation/structure.test.mjs` | 专有 | Figma 复刻页的结构测试。做法可以参考：归一化之后的组件可以有同样的结构测试 |
| `videos/zeemo-canvas-image-to-image/_harness.html` | 不搬 | 单独加载一个子合成来调试；`make-fingerprint` 覆盖了同样的需要 |
| `shared/docs/FEATURE-MAP.md`、`SERIES-PLAN.md` | 专有 | Zeemo 产品功能地图和排期。对应到 DemoFoundry 是「产品地图」和「系列计划」两个模板，P4 再定 |

## zeedemo 有未提交的改动

读源码时 zeedemo 工作区有 22 处没提交，包括第七集整个目录、`video-node` 子库和它的验收页，以及 `zui.py`、`voice.py`、`recording.py`、`cover.py`、`new-episode.py` 的修改。**这份清单按工作区的最新版本写**；P2 搬代码也从工作区搬。要不要先在 zeedemo 里提交，由你决定（DemoFoundry 这边不动 zeedemo）。

## 已定（2026-10-03）

1. 连线几何在引擎里按同样的算法重写一份（端点外移量作参数），`zui.py` 仍不搬。
2. 切点检测和 `measure-reference.py` 不进 v1。
