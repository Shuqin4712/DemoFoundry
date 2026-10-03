# P2 · 引擎抽取记录

> 2026-10-03。依据 [抽取清单](p1-inventory.md)。引擎在 `skills/demofoundry/engine/`（Python 包 `demofoundry`），测试在 `tests/`。

## 1. HyperFrames 版本实测

把 zeedemo 第七集复制到临时目录（符号链接展开，不动 zeedemo），两个版本各跑一遍：

| 项 | 0.8.34 | 0.8.114 |
| --- | --- | --- |
| `check` | 0 错误；lint 20 警告、布局 80 提示、对比度 6 警告 | 完全相同 |
| 整片渲染（草稿、30fps） | C 盘剩 19GB 时失败（帧缓存要 20GB）；临时目录改到 D 盘后 266s | 269s，没有空间问题 |
| 时长 / 响度 | 80.87s · −16.7 LUFS · LRA 7.5 · 峰值 −1.0 | 完全相同 |
| 画面 | — | 平均 PSNR 43 dB；17 个孤立帧低于 35 dB，都在节点里播放 24fps 视频的时段（取到相邻源帧），肉眼看不出 |

结论：锁 0.8.114（决策记录）。

## 2. 搬了什么、怎么验证

| 引擎模块 | 来源 | 验证 |
| --- | --- | --- |
| `hf.Timeline` | `zgen.Timeline` | 和 zgen 逐字节一致 |
| `stage.Camera` / `Cursor` | `zgen.Camera` / `Cursor` | 一致（含 `drag_wire`、移动中报错）；画幅参数化，1920×1080 时数值不变 |
| `fx`（笔迹、描线、扫光、打字、飞入） | `zgen` | 一致 |
| `geom`（连线几何） | `zui.wire_between` / `bez_len` / `Wires` 按同一算法重写 | 四种方向的连线、长度、描线一致（端点外移 5.75 作参数） |
| `cues` | `zgen.word_time` + 各集 `W()` | 一致；新增同片段内第 n 次出现 |
| `intro`（片头） | `zgen.INTRO_CSS` / `intro_*` | 星点和时间轴除两行注释外一致；配色字体改由主题提供 |
| `intro.end_card`、`hf.index_html` | `zgen.end_card` / `index_html` | 去品牌：logo、网址、Powered by、角标、混音比例都进主题 / 配置 |
| `scene`（场景函数） | 第四到七集 `gen.py` 里重复的辅助函数 | 合并成一份；单元测试 |
| `voice` | `shared/tools/voice.py` | 第七集定稿那一版（c02）原始段落重跑 `build`：12 个片段 wav 逐字节一致、排布表一致、逐词时间数据一致（只有换行符从 CRLF 变 LF） |
| `recording` | `shared/tools/recording.py` | 第七集录屏：15 次变化、15 个状态一致，总览图逐字节一致 |
| `refprofile` | `product-ui-rebuild` 的 `ref_profile.py` + `png.py` | `reference/ui/node-*` 22 张截图测量结果全部一致；倍率和阈值改成参数 |
| `av` | `media.py` / `recording.py` 的公共小工具 + 静帧 / 播放片段 | 合并三份重复代码 |
| `bgm trim`、`fingerprint`、`serve`、`which`、`io` | 对应工具 | 单元测试 / 使用中验证 |

对拍脚本含 Zeemo 取值，放在会话临时目录，没进仓库。

## 3. 改掉的问题

- 画幅写死 1920×1080 → 从配置读。
- 文件读写统一 UTF-8 + LF。
- `npx` 在 Windows 调不到 → `which` 统一查找。
- 转写默认 faster-whisper，Parakeet 改为可选；`zemo → zeemo` 硬编码改成配置里的别名表。
- ffmpeg 9 删掉了 `-vsync`（本机就是 9.0.2）→ 改用 `-fps_mode passthrough`。
- 片尾卡没有 logo 时仍在动画里操作 `#ec-logo`，`check` 报「GSAP target not found」→ 没有就不写。
- 讲解描框写死白色，浅色界面上看不见 → 颜色作参数。
- GSAP 改用 HyperFrames 自己模板里的固定版本 CDN（`gsap@3.14.2`），仓库不分发 GSAP 文件。
- 不用符号链接：生成时把模具的 css / icons / fonts 同步到集目录 `assets/mold/`（不提交）。

## 4. 测试小集

`tests/fixtures/jot/`：虚构笔记应用「Jot」，夹具模具（不是从证据重建的）+ 一集 5 段约 24 秒：片头（星点 + 胶囊）→ 点 New note → 推近、逐字打标题、Saved、讲解描框 → 拉回、点 Share、弹出提示 → 片尾卡。配音暂用均匀排布的逐词时间和静音 wav（`tests/make_fixture_voice.py`），P3 换成真的本地免费配音。

```bash
python -m unittest discover -s tests            # 23 项；回归 = 重新生成并和提交的产物逐字节比较
DF_HF_CHECK=1 python -m unittest discover -s tests   # 另跑 hyperframes check
```

2026-10-03：23 项全过，`check` 0 错误 0 警告；草稿渲染逐帧看过。

## 5. 没在 P2 做的

| 项 | 挪到 | 原因 |
| --- | --- | --- |
| 脚本改用 `uv` | 待定 | 本机没装 `uv`，安装要你同意；引擎已按标准 `pyproject.toml` 写好，装上即可用 |
| BGM 接长（`bgm-extend.py`） | P3 | 参数是按那一首曲子调的，要先泛化 |
| 封面（`cover.py` 机制） | P3 / P4 | 需要一个 DemoFoundry 自己的默认封面模板 |
| 建模具骨架、验收页模板、`solve()` / `recheck()`、进度检查 `status.py` | P4 | 属于两个 skill 的流程 |
| 配音来源接口、本地免费引擎、ElevenLabs | P3 | 计划表 |
