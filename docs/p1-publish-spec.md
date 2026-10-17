# P1 · 发布包规格

> 状态：**已认可**（2026-10-03）
> 依据：PROJECT §5「发布包」（成片 MP4 1080p 可选 4K · 字幕 SRT · 封面 PNG · 标题和简介 · 一段 GIF / 短片段）；zeedemo 发布阶段（SERIES-WORKFLOW 阶段 10）；zeedemo 成片实测（见 §2）。
> 平台限制（标题长度、封面大小、章节规则）按 YouTube 写；发布前再核对一次平台当前要求。

## 1. 位置与命名

每集的发布包放在 `demofoundry/episodes/<NN>-<slug>/publish/`。文件名都以 `<NN>-<slug>` 开头，拷出目录后仍然知道是哪一集。

```
publish/
  01-getting-started.mp4          成片 1080p
  01-getting-started-4k.mp4       成片 4K（可选）
  01-getting-started.srt          字幕
  01-getting-started-cover.png    封面
  01-getting-started-clip.mp4     短片段
  01-getting-started-clip.gif     同一段的 GIF
  copy.md                         标题、简介、章节、标签
  manifest.json                   这一包的清单和来源记录
  publish.json                    发布包参数：封面、短片段起止（生成的输入）
```

**提交进 git 的**：`copy.md`、`manifest.json`、`publish.json`、`.srt`、封面 PNG。
**默认不提交的**（写进 `demofoundry/.gitignore`）：`.mp4`、`.gif`。体积大，而且能从源码重新渲染；想提交的用户自己改 `.gitignore` 或用 Git LFS。

## 2. 成片 MP4

默认值取自 zeedemo 已发布成片的实测（`ffprobe` + `ebur128`，2026-10-03）：

| 项 | 默认 | zeedemo 实测 |
| --- | --- | --- |
| 分辨率 | 1920×1080；4K 可选 3840×2160 | 1080p60 和 4K60 两种都出过 |
| 帧率 | 60fps | 60fps |
| 视频编码 | H.264，yuv420p | H.264，yuv420p |
| 音频 | AAC，48kHz，立体声，约 192kbps | AAC，48kHz，立体声，约 200kbps |
| 响度 | 整片 **−16 LUFS ±1**，真峰值 ≤ −1 dBTP | −16.6 / −16.3 LUFS，峰值 −1.0 / −1.4 dBFS |
| 封装 | `faststart`（moov 前置，网页边下边播） | — |

- 画幅和分辨率从 `demofoundry.json` 读；v1 只正式支持 16:9。
- 渲染用 HyperFrames（2026-10-17 修订：运行时取最新版，发布清单记录实际版本）；只在用户确认整片预览后才渲。
- 渲染完自动量响度和峰值，写进 `manifest.json`；超出范围报警，不自动改。

## 3. 字幕 SRT

- **文字来自讲稿，不来自转写。** 时间来自配音的逐词时间。
- 编码 UTF-8（无 BOM），换行 LF（决策记录 2026-10-03）。
- 每条最多 2 行，每行最多 42 个字符；每条显示 1–7 秒。
- 断句优先在句末，其次在配音片段边界和逗号处；不把专有名词、数字和单位拆到两行。
- 片头片尾卡上没有旁白的部分不出字幕。

## 4. 封面 PNG

- 1920×1080，PNG。超过平台大小上限（YouTube 目前是 2MB）时另出一份同尺寸 JPG。
- **v1 只有一个默认版式**：左边标题（两到三行，最后一行用强调色写功能名），右边是本集里的一帧真实界面（取自某个提示点时刻），配色和字体用模具主题。
- 参数写在 `publish.json` 的 `cover` 里：标题各行、取哪个提示点的画面、强调色是否覆盖主题。
- 用无头 Chrome 截图（复用 zeedemo `cover.py` 的机制，模板换成 DemoFoundry 自己的）。
- **多版式封面模板在待办池**，v1 不做（PROJECT §7）。zeedemo 的封面是 1672×941、一个默认版式加四个变体（`empty-node`、`portrait`、`refs-fan`、`trio`），都是 Zeemo 品牌；v1 只取它「每集只写一个 JSON、模板渲染」的机制。

## 5. 文案 `copy.md`

每一项放在单独的代码块里，方便原样复制到上传页面。

| 项 | 规则 |
| --- | --- |
| Title | 一句讲清收益的话，可选系列后缀 `| <系列名>`（后缀在 `demofoundry.json` 里配）。**最多 100 字符**，建议 ≤ 70，避免在搜索结果里被截断 |
| Description | 结构沿用 zeedemo：① 1–2 句痛点或目标 + 用这个功能能做到什么；② `What you'll learn:` + 3–5 条，每条一个动作；③ 一句 CTA，和片尾卡用词一致；④ 链接（从配置读）；⑤ 话题标签。**写功能能做什么，不照抄旁白** |
| Chapters | 从讲稿的段落标题生成：`0:00 <标题>` 一行一条。YouTube 规则：第一条必须是 `0:00`，至少 3 条，每条至少 10 秒；不满足时不输出这一节 |
| Tags | 系列固定标签（配置里）+ 本集标签 |

## 6. 短片段和 GIF

给社交媒体、README、更新日志用的一小段。

| 项 | 短片段 `-clip.mp4` | GIF `-clip.gif` |
| --- | --- | --- |
| 内容 | 本集最有代表性的一个操作，起止用两个提示点指定，写在 `publish.json` 的 `clip` 里 | 同左 |
| 长度 | 5–15 秒 | 3–8 秒（GIF 体积随长度涨得快） |
| 尺寸 | 1920×1080，参数同成片 | 宽 960，等比 |
| 声音 | 保留（含旁白和 BGM） | 无 |
| 帧率 | 同成片 | 15fps |
| 大小 | — | ≤ 10MB（GitHub README 能直接显示的上限），超出时自动降宽或缩短并提示 |

GIF 用 ffmpeg 两遍调色板（`palettegen` + `paletteuse`），不用默认 256 色抖动，界面文字才不糊。

## 7. 清单 `manifest.json`

```json
{
  "episode": "01-getting-started",
  "generated_at": "2026-10-03T12:00:00Z",
  "engine": { "demofoundry": "0.1.0", "hyperframes": "0.8.114" },
  "files": {
    "01-getting-started.mp4": { "w": 1920, "h": 1080, "fps": 60, "duration": 80.85, "lufs": -16.4, "true_peak": -1.1 },
    "01-getting-started.srt": { "cues": 42 }
  },
  "voice": { "source": "import", "detail": "..." },
  "music": { "file": "assets/bgm/track.wav", "source": "...", "license": "...", "license_url": "..." }
}
```

- 记下引擎和 HyperFrames 版本：以后升级引擎时，判断旧集要不要重新生成就看这里。
- 音乐的来源和授权从 `assets/bgm/LICENSES.md` 抄进来（PROJECT §7：记录来源和授权）。
- 工作台的看板读这个文件显示每集的交付状态。

## 已定（2026-10-03）

1. 默认 60fps。
2. 响度 −16 LUFS ±1，真峰值 ≤ −1 dBTP。
3. MP4 / GIF 默认不提交进 git。
