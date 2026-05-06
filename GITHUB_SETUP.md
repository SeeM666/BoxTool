# BoxTool v5.0 - GitHub 仓库初始化指南

## 📋 上传到 GitHub 的步骤

### 方法一：使用 Git 命令行

```bash
# 1. 进入项目目录
cd C:\Users\TR\Desktop\apk

# 2. 初始化 Git 仓库
git init

# 3. 添加所有文件
git add .

# 4. 提交
git commit -m "Initial commit: BoxTool v5.0"

# 5. 在 GitHub 创建新仓库（不要勾选初始化选项）

# 6. 关联远程仓库（替换 YOUR_USERNAME 为你的 GitHub 用户名）
git remote add origin https://github.com/YOUR_USERNAME/boxtool.git

# 7. 推送
git branch -M main
git push -u origin main
```

### 方法二：使用 GitHub Desktop

1. 下载并安装 [GitHub Desktop](https://desktop.github.com/)
2. 打开 GitHub Desktop
3. File → Add Local Repository → 选择 `C:\Users\TR\Desktop\apk` 文件夹
4. 点击 "Create a repository"
5. 填写仓库名称（如 `boxtool`）
6. 点击 "Publish repository"

---

## 🔄 触发 APK 自动构建

上传到 GitHub 后，有以下几种方式触发 APK 构建：

### 方式 1：创建 Tag（推荐）

```bash
# 创建版本 tag
git tag v5.0.0
git push origin v5.0.0
```

这会自动触发 GitHub Actions 构建 APK，并在 Release 中发布。

### 方式 2：手动触发

1. 进入 GitHub 仓库页面
2. 点击 "Actions" 标签
3. 选择 "Build Android APK" 工作流
4. 点击 "Run workflow" 按钮
5. 选择分支，点击 "Run workflow"

---

## 📝 后续更新

```bash
# 修改代码后
git add .
git commit -m "修复界面布局问题"
git push

# 发布新版本
git tag v5.0.1
git push origin v5.0.1
```

---

## ⚙️ 配置说明

### buildozer.spec 关键配置

| 配置项 | 说明 | 当前值 |
|--------|------|--------|
| package.name | 应用包名 | boxtool |
| package.domain | 包域名 | org.boxtool |
| version | 版本号 | 5.0.0 |
| android.api | Android API 级别 | 33 |
| android.minapi | 最低支持 API | 24 |
| android.archs | 支持的架构 | arm64-v8a, armeabi-v7a |

### GitHub Actions 配置

工作流文件位于：`.github/workflows/build-apk.yml`

触发条件：
- Push 到 `main` 或 `master` 分支
- 创建 `v*` 格式的 tag
- 手动触发（workflow_dispatch）

---

## 🔍 故障排查

### 构建失败

1. 检查 GitHub Actions 日志
2. 确认 `buildozer.spec` 配置正确
3. 确保所有依赖在 `requirements.txt` 中

### APK 无法安装

1. 检查 Android 设备是否允许"未知来源"安装
2. 确认 APK 架构与设备匹配（arm64-v8a / armeabi-v7a）
3. 检查 Android 版本是否 >= API 24 (Android 7.0)

---

## 📞 需要帮助？

提交 Issue 到 GitHub 仓库，或查看 [README.md](README.md) 获取更多信息。
