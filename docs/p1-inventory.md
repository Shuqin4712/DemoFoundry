# P1 · 抽取清单

> 状态：**草稿，待认可**（2026-10-03）
> 范围：zeedemo 的 `shared/gen/zgen.py`、`shared/gen/zui.py`、`shared/tools/*.py`，逐函数标注；其余来源按文件列在最后。
> 读法：这份清单只回答「搬不搬、怎么搬」，具体搬的动作在 P2 做。

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
| `word_time` | 词 → 时间（取第一次出现） | **改造** | 这是「提示点时间线」的雏形。改成具名提示点：`cue('click-generate')`，提示点由讲稿标记生成，同一个词出现多次时不再靠「第一次」碰运气 |
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

## 待定（需要你拍板）

1. **连线几何要不要重写进引擎？** `wire_between` / `bez_len` 在 `zui.py` 里（不搬的文件），但它们是纯几何、和 Zeemo 样式无关。我建议在引擎里按同样的算法重写一份（端点外移量作参数），这样节点编辑器类产品能直接用；不重写的话，每个用户的模具要各自写一份。
2. **`media.py` 的切点检测和 `measure-reference.py` 要不要进 v1？** 两个都通用，但 v1 的流程里用不上。我倾向 P2 先不搬，减少依赖（尤其 OpenCV）。
