# HLTB API

一个基于 HowLongToBeat 的游戏时长查询 API 服务。

## 接入方式

### 接口地址

```
GET /api/search
```

### 请求参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| key | string | 是 | API 密钥 |
| game | string | 是 | 游戏名称（2-200字符） |

### 请求示例

```bash
curl "https://your-api-domain.com/api/search?key=YOUR_API_KEY&game=Elden%20Ring"
```

## 输出格式

### 成功响应 (200)

```json
{
  "matched_name": "Elden Ring",
  "similarity": 0.98,
  "main_story": 54.5,
  "main_extra": 101.5,
  "completionist": 135.0,
  "all_styles": 97.0
}
```

**字段说明：**

- `matched_name`: 匹配到的游戏名称
- `similarity`: 相似度（0-1之间，阈值为0.6）
- `main_story`: 主线时长（小时）
- `main_extra`: 主线+支线时长（小时）
- `completionist`: 完美主义时长（小时）
- `all_styles`: 全风格平均时长（小时）

> 注：时长字段可能为 `null`，表示该类型数据不可用

### 错误响应

#### 401 未授权
```json
{
  "error": "Unauthorized"
}
```

#### 400 参数错误
```json
{
  "error": "Invalid game name"
}
```

#### 404 未找到
```json
{
  "error": "Game not found"
}
```
或
```json
{
  "error": "No close match found"
}
```

#### 503 服务不可用
```json
{
  "error": "HLTB service unavailable",
  "detail": "网络不稳定，请稍后重试"
}
```

## 特性

- **智能搜索**：自动尝试多种搜索策略（原名、标准化名称、移除副标题）
- **自动重试**：最多重试 3 次，应对网络波动
- **括号过滤**：自动移除游戏名中的括号内容，提高匹配率
- **相似度匹配**：相似度阈值 0.6，确保结果准确性

## 环境变量

| 变量名 | 说明 |
|--------|------|
| API_KEY | API 访问密钥（必填） |

## 部署

本项目基于 Vercel Serverless 部署，配置文件见 `vercel.json`。
