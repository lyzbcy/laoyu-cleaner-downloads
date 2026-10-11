# 捞鱼 C 盘清理 0.1.3（测试版）

[下载 Windows / macOS Intel / Apple Silicon](https://github.com/lyzbcy/laoyu-cleaner-downloads/releases/tag/v0.1.3)

Windows 解压后双击 LaoyuCleaner.exe；Mac 按芯片选择 ZIP，解压运行 app。Mac 包当前 ad-hoc 签名，尚未 Developer ID 公证；普通电脑首次打开未验收，优先由小范围用户试用。

默认只读诊断、默认不选清理项。用户逐项确认后仅移到系统回收站/废纸篓，不自动清空。个人文档、下载、桌面与系统核心不自动清理；不自动迁移。缓存可能联网重建，移动量不是已释放空间。

提供 Agent 迁移 Prompt：先只读评估，列明来源与目标空间，确认、备份、复制校验和回滚；软件不执行迁移。

Windows 实际打包界面/剪贴板和隔离回收恢复通过；Mac 两架构在真实托管 macOS 15.7.9 上通过界面 DOM、剪贴板、隔离废纸篓恢复、个人文件保留和真实 Node 进程保护验收。不等于每款应用、每台用户电脑或 Gatekeeper 首次打开验收。部分截图存在帧时序问题，文件名不是页面内容证明。

只发布桌面软件和说明，不发布旧全盘删除 BAT。暂无后台清理、自动迁移、提权或完整自动安装升级。
