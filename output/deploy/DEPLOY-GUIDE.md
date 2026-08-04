# 高砖积木 GEO 部署指引（开发者操作手册）

> 目标读者：前端/后端开发者
> 预计总工时：4-6 小时
> 生效时间：Schema 部署后 1-2 周被搜索引擎和 AI 引擎抓取

---

## 文件清单

```
deploy/
├── 01-organization-schema.html    ← 全站 <head> 注入
├── 02-faq-schema.html             ← FAQ 页面 <head> 注入
├── 03-og-meta-tags.html           ← 各页面 <head> 替换 meta 标签
├── 04-breadcrumb-schema.html      ← 各页面 <head> 注入对应路径
├── 05-article-schema-templates.html ← 文章/商品页面 <head> 模板
├── content/
│   ├── pillar-moc-guide.md        ← Pillar Page 核心文章
│   ├── sub-01-moc-intro.md        ← 子文章：MOC入门指南
│   ├── sub-02-parts-guide.md      ← 子文章：零件选购指南
│   └── sub-07-designer-path.md    ← 子文章：设计师认证路径
└── DEPLOY-GUIDE.md                ← 本文件
```

---

## 部署步骤

### Step 1: 全站注入 Organization Schema（15 分钟）

**操作：**
1. 打开 `01-organization-schema.html`
2. 将 `<script type="application/ld+json">...</script>` 代码块复制
3. 粘贴到全站共享的 `<head>` 模板中（所有页面都会加载的位置）
4. 如果使用 Google Tag Manager，可以创建自定义 HTML 标签注入

**验证：**
- 访问 [validator.schema.org](https://validator.schema.org/)
- 输入部署后的页面 URL
- 确认无错误，Organization 类型被正确识别

**注意：**
- `logo` 字段的图片 URL 需替换为实际 logo 路径
- 全站只需部署一次，所有页面共享

---

### Step 2: FAQ 页面注入 FAQ Schema（20 分钟）

**操作：**
1. 打开 `02-faq-schema.html`
2. 将 `<script type="application/ld+json">...</script>` 代码块复制
3. 粘贴到帮助中心页面（`/help?id=39`）的 `<head>` 中
4. **关键：** 页面上必须有对应的可见 FAQ 内容（HTML 文本），Schema 中的文字需与页面可见文字一致

**最佳方案：** 创建独立的 `/faq` 页面，将 12 个问答以可见 HTML 展示，同时注入 FAQ Schema。

**验证：**
- 使用 [validator.schema.org](https://validator.schema.org/) 验证
- 使用 Google Search Console 检查 FAQ 富文本是否生效

---

### Step 3: 替换 Meta 标签 + 添加 OG 标签（30 分钟）

**操作：**
1. 打开 `03-og-meta-tags.html`
2. 按页面找到对应区块（首页 / 帮助中心 / 积木圈 / 商城）
3. 替换现有 `<title>` 和 `<meta name="description">` 标签
4. 添加 `<meta property="og:...">` 和 `<meta name="twitter:...">` 标签

**需要准备的素材：**
- `og-image.png` — 1200x630 像素的品牌分享图
- `og-image-about.png` — 关于页面分享图
- `og-image-community.png` — 积木圈分享图
- `og-image-shop.png` — 商城分享图

---

### Step 4: 各页面注入 BreadcrumbList Schema（20 分钟）

**操作：**
1. 打开 `04-breadcrumb-schema.html`
2. 根据页面类型选择对应的代码块
3. 替换 `{{变量}}` 为实际值
4. 注入到对应页面的 `<head>` 中

**页面映射：**
| 页面 | 使用哪个代码块 |
|------|--------------|
| 商城 | 首页 > 商城 |
| 积木圈 | 首页 > 积木圈 |
| 帮助中心 | 首页 > 帮助中心 |
| 关于我们 | 首页 > 帮助中心 > 关于我们 |
| 作品详情 | 首页 > 积木圈 > {作品名} |
| 商品详情 | 首页 > 商城 > {商品名} |

---

### Step 5: 文章和商品页面添加 Article / Product Schema（30 分钟）

**操作：**
1. 打开 `05-article-schema-templates.html`
2. 根据页面类型选择模板：
   - 博客/教程文章 → `BlogPosting`
   - 工具使用教程 → `TechArticle`
   - 积木圈作品 → `CreativeWork`
   - 商品详情 → `Product`
   - 带作者标记的文章 → `E-E-A-T @graph`
3. 替换所有 `{{变量}}` 为实际值
4. 注入到对应页面的 `<head>` 中

**重点：**
- 每篇帮助中心文章都应有 `BlogPosting` 或 `TechArticle` Schema
- 每个商品都应有 `Product` Schema（含价格、库存状态）
- 积木圈作品应使用 `CreativeWork` Schema（含设计师信息）

---

### Step 6: 部署 Pillar Page 内容（1-2 小时）

**操作：**
1. 在 CMS 或静态页面系统中创建以下页面：

| 路径 | 内容文件 |
|------|---------|
| `/moc-guide` | `content/pillar-moc-guide.md` |
| `/moc-guide/intro` | `content/sub-01-moc-intro.md` |
| `/moc-guide/parts-guide` | `content/sub-02-parts-guide.md` |
| `/moc-guide/designer-path` | `content/sub-07-designer-path.md` |

2. 每篇文章添加对应的 Schema：
   - Pillar Page → `BlogPosting` Schema
   - 子文章 → `BlogPosting` Schema + `BreadcrumbList`

3. 确认内部链接正确（文章底部导航）

---

## 部署后验证清单

完成所有部署后，逐一检查：

| 检查项 | 工具 | 预期结果 |
|--------|------|---------|
| Organization Schema | [validator.schema.org](https://validator.schema.org/) | 0 错误 |
| FAQ Schema | [validator.schema.org](https://validator.schema.org/) | 0 错误，识别 12 个问答 |
| BreadcrumbList | [validator.schema.org](https://validator.schema.org/) | 层级正确 |
| OG 标签 | [developers.facebook.com/tools/debug/](https://developers.facebook.com/tools/debug/) | 分享预览正确 |
| 全站 Schema | Google Search Console → 增强功能 | 全部通过 |
| 页面速度 | [PageSpeed Insights](https://pagespeed.web.dev/) | Schema 不影响加载速度 |

---

## 持续维护

| 任务 | 频率 | 说明 |
|------|------|------|
| 新文章发布时添加 Schema | 每次发布 | 使用模板文件中的 BlogPosting 模板 |
| AI 可见度手动测试 | 每月 | 在 ChatGPT/Perplexity/Gemini 搜索关键词 |
| 新增 FAQ 问答 | 每月 | 根据用户反馈补充新的问答对 |
| 内容可读性检测 | 每篇发布前 | 检查营销词密度、句长、是否有问句 |
| Schema 验证 | 每季度 | 全站 Schema 健康检查 |

---

## 注意事项

1. **Schema 内容必须与页面可见内容一致** — Google 会对比两者，不一致可能导致惩罚
2. **不要重复部署** — 每个页面每种 Schema 类型只放一个
3. **图片 URL 必须可访问** — Schema 中引用的图片必须返回 200
4. **日期格式** — 统一使用 `YYYY-MM-DD` 格式
5. **价格格式** — Product Schema 中 price 字段只填数字，不含货币符号
