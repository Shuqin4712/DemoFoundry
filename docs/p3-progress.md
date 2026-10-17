# P3 · 配音与音乐推进记录

> 2026-10-17。状态：进行中，免费旁白到成片已跑通；音乐实际使用、试听与平台 API 仍待验证。P4 未开工。

## 本次结果

| 项目 | 结果 | 验证边界 |
| --- | --- | --- |
| HyperFrames 实时更新 | 所有执行脚本使用 `hyperframes@latest`；本次实际为 **0.8.168** | 不自动刷新已经复制到产品仓库的 skill 文件；P4 初始化/更新流程再刷新上游 skill |
| 免费本地配音 | Kokoro ONNX，`af_sarah`，CPU，本机 Windows | Kokoro 首次下载约 354MB 模型/音色文件，之后本地合成；运行库与模型不分发进仓库 |
| 转写 | faster-whisper CPU int8，实测 `tiny.en` | 默认仍为 `small.en`；本次只实测英文 tiny.en，Mac Parakeet 未实测 |
| 配音接口 | 默认导入；新增 Kokoro 和 ElevenLabs 两个 provider | ElevenLabs 未发网络请求，字符时间转词时间与缺 key 行为有测试 |
| 讲稿对齐 | 5 段连续合成，逐词时间对齐原讲稿，破折号停顿补至 200ms | 5 段均无对齐差异警告；这不等于主观试听通过，也不保证词级时间绝对准确 |
| SRT | 从 final 的词时间加片段全局偏移导出，UTF-8/LF，最多两行、每行 42 字符 | 尚需复杂专有名词断行、极短字幕的显示时长策略 |
| 音乐裁剪/接长 | trim；按显式乐句边界插入、等功率交叉淡化、保留原收尾 | 正弦测试信号通过长度验证；未用真实曲目试听，不声称已实现自动节拍检测 |
| 音乐授权记录 | 来源 URL、license、attribution、文件 SHA-256 | 记录使用者给出的授权事实，不代为认证许可 |
| BGM 两条入口 | 导入已有授权曲目；借用上游 media-use 的曲库/生成 | 本机未配置 HeyGen CLI；上游文档明确曲库检索需要 CLI 登录；没登录仍能走导入路线 |
| 响度处理 | 显式 `master` 命令，两遍 loudnorm，视频流复制 | 与「量完报警、不自动改」兼容：只有主动执行 master 才处理；处理后仍须复测 AAC |

## 本次实际成片

实验副本放在 `.tmp/p3/jot/`（gitignore），未覆盖静音的逐字节回归基准。

- 5 段真实 Kokoro 旁白；逐词时间来自实际转写，不是均匀分配。
- `publish/01-quick-note.mp4`：H.264，1920×1080，60fps，20.4 秒，AAC 48kHz 立体声。
- 显式响度处理后 ffmpeg ebur128 实测：**−16.0 LUFS，真峰值 −1.0 dBFS**。
- `publish/01-quick-note.srt`：5 条字幕。
- 片子是技术验证，无 BGM；已看抽帧总览，尚待用户试听并判断语速、发音和音画对位。
- 成片与模型不提交；代码、测试、锁文件和复现方式提交。

## 测试与已遇问题

- 完整 30 项测试全部通过（含最新 HyperFrames check、ffmpeg 实际乐句接长）。
- 最新版首次检查在默认浏览器配置中耗时过长，最后报浏览器未运行/超时。记录为失败，不当作通过。
- 本地缓存固定 GSAP（只放实验/测试目录）并改用软件 GPU 后通过。两项同时改变，尚不能断言具体由哪一个因素导致；集成测试增加 180 秒外层超时，不再无限等。
- 真实配音版 `check`：0 错误、0 警告、16 条布局信息（镜头推近后的有意画外元素）；53/53 文字对比度检查通过。
- 新版 PyAV 19 移除了 faster-whisper 解码路径所用的 `metadata_errors` 参数：改为系统 ffmpeg 解码到 16kHz float32 PCM，再交给转写，已实际验证。
- Kokoro 与音色文件下载后记录来源和 SHA-256；这些哈希用于标识本次文件，不是与官方预先签名的校验值比对。

## 复现

仓库根目录，Python/Node/ffmpeg 已有，首次联网下载模型：

```powershell
uv run --locked --extra local --project skills/demofoundry/engine python tests/run_p3.py --out .tmp/new-p3-run --render
```

2026-10-17 已另在 `.tmp/p3-repro/` 从头执行此脚本并成功生成第二份真实成片（20.38 秒时间轴）；`run.json` 记录实际 HyperFrames 0.8.168。

`--out` 必须为新目录。默认 tiny.en 供 smoke test，可用 `--model small.en` 切换。
脚本不访问付费 API，不取音乐；保存实际 HyperFrames 版本、检查与渲染日志。

测试：

```powershell
$env:DF_AUDIO_CHECK = '1'
$env:DF_HF_CHECK = '1'
uv run --locked --extra local --project skills/demofoundry/engine python -m unittest discover -s tests -v
```

## P3 剩余

- 用户试听：本地声音质量、语速、产品名读音及逐词对位。
- 用真实授权音乐验证裁剪、乐句接长、人声避让，以及来源/授权记录串到最终发布清单。
- 上游曲库/生成的登录条件已有文档结论，但没在有账号的环境里端到端实测。
- ElevenLabs 有 key 后的小额 API 实测（需明确授权）；Mac Parakeet 需对应机器。
- 字幕极短片段和专有名词断行策略补齐；完整发布包与初始化仍归 P4。

## 一手资料

- [Kokoro ONNX](https://github.com/thewh1teagle/kokoro-onnx)：接口、下载、运行库 MIT/模型 Apache-2.0 说明。
- [ElevenLabs with-timestamps](https://elevenlabs.io/docs/api-reference/text-to-speech/convert-with-timestamps)：音频及原文/规范化字符时间戳。
- 上游本机 `media-use` skill 的 `SKILL.md`、`references/audio.md`、`audio/references/bgm.md`：曲库需 HeyGen CLI，生成能力视具体 provider/依赖。
