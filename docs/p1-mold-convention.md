# P1 · 模具约定（草案 v2）

> 状态：**草稿，待认可**（2026-10-03）
> v2 按 zeedemo 的实际做法和用户 2026-10-03 定的证据优先级重写（v1 只依据 `product-ui-rebuild` skill，把第一集的纯截图量测当成了唯一标准）。依据：
> `shared/assets/canvas-ui/` 及各子库 README、`shared/proof/` 八个验收页、`shared/gen/zui.py`、`shared/proof/video-node.gen.py`、`reference/ui/` 的证据组织、第七集 `_build/gen.py`。
> 这份定的是**模具里的东西长什么样、放在哪、怎么证明它对**；怎么一步步建模具是 `demofoundry-mold` skill 的事（P4）。发布前译成英文。

## 0. 证据优先级

**有 Figma 用 Figma；没有的话靠截图 + 录屏。**（用户 2026-10-03，依据 zeedemo 的实际效果）

| 优先级 | 证据 | 管什么 | zeedemo 里的例子 |
| --- | --- | --- | --- |
| 1 | **Figma**：节点导出，或按节点做的复刻 HTML | 尺寸、间距、圆角、颜色、字体、图标原件 | `reference/ui/edit/figma-recreation/`（第二集）；Figma 节点 22182:1624 的 Image 组件复刻 |
| 2 | **录屏** | 行为、状态、出现顺序、界面原文；Figma 里没有的状态 | 第二到七集都有，`recording.py` 建索引 |
| 3 | **截图**（100% 缩放、PNG） | 没有 Figma 时的尺寸和颜色；录屏偏色时取色 | 第一集核心库、`reference/ui/node-*/` |
| 兜底 | 只有截图、逐项量测再微调 | — | 第一集核心库。**还原度较低**：数值是从像素反推、一点点调出来的，不如直接拿 Figma 的值 |

zeedemo 从第二集起就是三样并行：Figma 复刻给数值，录屏给行为，截图补缺。产品源码（CSS、设计 token）和 Figma 同级，有就用。

### Figma 复刻 HTML 长什么样

一个 Figma 节点一个目录，例如节点 22182:1624：

```
zeemo-ui-22182-1624/
  index.html            独立组件，画板尺寸写成 CSS 变量（--design-width: 449.5px）；
                        每个元素带 data-node-id（对应 Figma 节点）、data-testid
  assets/               Figma 导出的原件：SVG 图标、图片、字体
  structure.test.mjs    检查节点 id、画板尺寸、文案、素材、交互入口都还在
  README.md             Figma 链接、节点 id
  archive/              旧版本
```

**它是怎么做出来的（推断，2026-10-03）**：用户是向老师要的复刻，不知道做法。从文件痕迹看，很可能是 **Figma MCP 取设计数据 + 编程 agent 改写**：

- SVG 带 `preserveAspectRatio="none" overflow="visible" style="display: block;"`，图层名原样成了 id（`<g id="edit4"><path id="Union">`）——这是 Figma MCP 提供素材的写法，Figma 手动导出没有；
- 每个子元素有真实的 Figma 子节点 id，只能从节点数据读到；Figma MCP 生成的代码正是逐元素标 `data-node-id`；
- 第二集那份复刻的素材叫 `imgAiVideo.svg`、`imgComponent14.svg`，是 Figma MCP 生成代码里素材变量的命名；
- 之后被 agent 改写成手写 CSS（不是 MCP 默认的 React + Tailwind），补了交互、中文无障碍标签和结构测试。

它的数值就是 Figma 的数值（工具条 433 宽、内边距 4、圆角 10），不需要再量。归一化时：CSS 加作用域、去掉 JS（点击反馈、`fit()` 缩放）、交互状态改成 class、标记写进 `ui.py`，数值一个不改；`data-node-id` 留在注释里当出处。

## 1. 模具是什么

模具 = 一个产品的界面组件库 + 证明它和产品一致的证据与验收页。它住在用户仓库的 `demofoundry/mold/`，每做一集按需补组件。

**合成里不内联重画任何产品界面**；缺什么就加进模具并补验收标本（zeedemo PLAYBOOK §2、§6.9）。

## 2. 目录

```
demofoundry/mold/
  mold.json                 清单：前缀、各组件的路线和验收状态（§8）
  README.md                 完成度表 + 已知未解分歧（给人看）
  theme/
    tokens.css              颜色、字体变量；每个值注明采样来源
    fonts/                  可再分发的产品字体（决策记录 2026-10-03）
  css/
    <子库>.css              按功能分子库，后引用的只写差异（同 zeedemo canvas-ui 子库的引用顺序）
    icons/<子库>/           图标（SVG 优先；只能从录屏抠的位图注明「别推近」）
  ui.py                     标记函数 + 几何常数（锚点），相当于用户产品自己的 zui.py（§4、§5）
  evidence/
    <功能>/
      README.md             证据表 + 界面原文（逐字）+ 录屏状态索引（§3）
      recording/<名>.mp4    录屏；_index/ 由 recording 工具生成（不提交）
      recording/crops/      关键帧裁图，文件名 <组件>__<状态>-<秒>s.png
      screenshots/          截图，<状态>__<说明>.png
      figma/                Figma 导出或复刻 HTML
      source/               产品源码摘出的 CSS / token，注明仓库和提交
  proof/
    <子库>.gen.py           调 ui.py 生成验收页（同 zeedemo video-node.gen.py）
    <子库>.html             生成出的验收页，不手改
    gallery.html            所有组件按真实用法裸摆，看默认状态
```

## 3. 证据

**按功能组织**（`evidence/<功能>/`），不是按组件：一条录屏里通常有好几个组件的好几个状态。每个功能目录一份 README，三张表：

| 表 | 内容 |
| --- | --- |
| 证据 | 每份证据是什么、规格（分辨率、帧率、画布缩放）、管什么 |
| 界面原文（逐字） | 按钮、菜单、占位、tooltip 的原文，大小写和标点照抄 |
| 录屏状态索引 | 时间 → 状态 → 要点；`recording` 工具出骨架，agent 看总览图填 |

规则（zeedemo 阶段 3、组件库 README 里反复验证过的）：

- **证据冲突时：行为和文案以录屏为准，色值和尺寸以 Figma / 源码为准。** h264 录屏会偏色，不从录屏取色。
- 截图用 PNG、产品 100% 缩放、不后期；retina 原样保存。
- 录屏不在 100% 时，写明换算比（如「录屏像素 ÷ 1.345 = 1x」），**至少用两处互相印证**（zeedemo 第六集：工具条 584 → 433、生成面板 940 → 701）。
- 分清**屏幕空间**和**画布空间**：面板、菜单、弹层大小不随画布缩放；节点卡片随缩放。缩放中的录屏只能量屏幕空间的东西。
- 证据里没有的界面**不凭口述画**，先请用户补录。录屏缺的状态（如完成态）在分镜里标出来并写明按什么画。

## 4. 组件

**组件只描述「长什么样」**：不带位置、不带出现时机、不带动画起始态。从场景里提取样式时剥掉 `left / top / width / height` 和 `opacity: 0`；`gallery.html` 专门抓这类泄漏（zeedemo 抓到过三处）。

### CSS

- 类名带模具前缀，选择器加作用域（复刻 HTML 里 `.panel`、`.icon` 这类通用类名一律包一层作用域类）。
- 单位：**1x 逻辑像素**（= Figma 1x）。整块缩放用包裹层 `transform: scale()`，Figma 复刻的数值原样保留，不改写成 `calc`；只有纯截图重建的组件才需要 `--<p>-u` 缩放契约。
- 边框用 `outline` + 负 `outline-offset`，画在盒内；flex 子项 `flex: 0 0 auto`；字间距用 `em`。
- 按类型不同的值用类型类限定，不当全局默认（zeedemo：四种节点的图标尺寸各不相同，曾把 text 的值当默认，其余小了 40%–55%）。
- 每个常数旁注释「实测值 + 来源」；从录屏量的标「近似」；刻意偏离产品的标「刻意偏离，非实测」和原因。
- **不搬产品的 JS。** 点击、rAF、`performance.now()` 违反渲染确定性；状态用 class 表达（`is-open`、`is-hover`、`is-busy`），由时间轴切换。

### 标记：`ui.py`

沿用 zeedemo `zui.py` 的写法：**每个组件一个 Python 函数，传参数、返回 HTML。**

- 子元素 id 规则 `<实例 id>-<部位>`（`<nid>-card`、`<pid>-gen`），动画按 id 找元素。
- 需要计算的放在函数里：列表高度随行数变、滑块位置随数值变、几种状态叠成几层用 `tl.set` 切（避免宽度跳）。
- 盖住别的元素是产品真实行为时，函数自己加 `data-layout-ignore`（菜单、面板、弹层），免得 HyperFrames `check` 误报。
- 函数的 docstring 写清：对应哪份证据的哪一秒、有哪些子元素 id、哪些状态。

## 5. 锚点

锚点 = 组件上有名字的点：按钮中心、菜单第 i 行中心、连线出入口。光标、连线、讲解描框都挂在锚点上。

- 写在 `ui.py` 里，紧挨着对应的组件函数，相对组件左上角、1x 逻辑像素（zeedemo 的 `NB_VAR`、`VMENU_ITEM(i)`、`BAR_GEN`、`PORT_R`、`nb_pos()` 就是这种）。
- 每个常数的注释写推导过程（「内边距 4 + Edit 70 + 间距 4 + 下拉键 60」），不只写结果。
- **新增：锚点进验收。** 验收页用 `ui.py` 生成标本时，同时在真实 DOM 里量锚点对应元素的中心，和常数比。组件改了样式、锚点没跟着改，验收会报。zeedemo 目前没有这一项。

## 6. 验收

按证据来源验不同的东西，同一个组件常常几样都要做：

| 证据 | 验什么 | 怎么验 |
| --- | --- | --- |
| Figma 复刻 / 节点导出 | 数值没被改动、结构没丢 | 结构测试（节点 id、画板尺寸、文案、素材，同 `structure.test.mjs`）；归一化后的组件和复刻页同尺寸叠加，差分应为 0 |
| 录屏 | 行为、状态、文案、布局 | 验收页逐行把组件和录屏同一时刻的裁图（按换算比缩到同一尺度）并排；换算比两处印证 |
| 截图（100% 缩放） | 尺寸和颜色 | 逐项实测对表，容差 ±0.3 逻辑像素；`solve()` 反解；并排 / 叠加 / 差分 |

共同的：

- 验收页由 `ui.py` 生成，标记只存一份；锚点一起验（§5）。
- `gallery.html` 裸摆组件，看默认状态。
- **把验收页给人看，专门问语义**：哪些是不同元素、何时出现、贴不贴边。
- **不过就停。** 没过的写没过；测法互相矛盾的保留成失败项、写进「已知未解分歧」，不调参压过去。自主模式下验收没过，停下来报告。

## 7. 状态记录

`mold.json`（工作台和自主模式读它）：

```json
{
  "prefix": "acme",
  "libs": {
    "editor": { "evidence": ["figma", "recording"], "qc": "pass", "at": "2026-10-03" },
    "panels": { "evidence": ["recording", "screenshot"], "qc": "fail", "failed": 1, "at": "2026-10-03", "note": "见 README 已知分歧 #1" }
  }
}
```

`qc`：`pass` / `fail` / `unchecked`。README 是同一份信息给人看的版本，完成度表只给真正过了的打 ✅，未实测写「未实测」。

## 8. 按集增量

- 讲稿阶段列出本集用到的组件和状态。
- 做一集前对照 `mold.json`：缺组件、缺状态或 `qc` 不是 `pass`，先补模具（共创模式下先问人）。
- 组件库有、但这一集用不上的东西，留在库里，由这一集自己决定不用。

## 已定（2026-10-03）

1. 「±0.3px」那条决策按 §6 改写（见决策记录）。
2. Figma 输入多一条候选「Figma MCP + agent 改写」，和上游 `hyperframes figma` 一起放进 Figma 实验比较。
