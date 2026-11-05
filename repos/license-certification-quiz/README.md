# 开源软件许可证合规检测报告

## 项目信息
- **检测项目**：Apache Commons Lang 3.14.0
- **项目官网**：https://commons.apache.org/proper/commons-lang/
- **检测工具**：ScanCode Toolkit 32.0.6
- **检测日期**：2026-10-29
- **操作系统**：Windows 11 + Python 3.12.7

## 项目简介

Apache Commons Lang 是 Apache 软件基金会维护的一个 Java 工具类库，提供了对 `java.lang` 包的扩展工具方法，包括字符串处理、数组操作、异常处理、并发工具、反射工具、日期时间工具等。该项目是 Apache Commons 系列中使用最广泛的库之一，几乎所有 Java 项目都直接或间接依赖它。

## 扫描命令

```bash
scancode -l -c -p -i --json-pp report.json --html report.html .
```

参数说明：
- `-l`：扫描许可证（license）
- `-c`：扫描版权信息（copyright）
- `-p`：扫描包信息（package）
- `-i`：扫描文件信息（info，含文件类型、大小、哈希等）
- `--json-pp`：输出格式化 JSON 报告
- `--html`：输出 HTML 网页报告
- `.`：扫描当前目录

## 扫描结果概览

| 指标 | 数值 |
|------|------|
| 扫描文件总数 | 1,468 |
| 检测到许可证的文件 | 15 |
| 检测到版权的文件 | 14 |
| 检测到的包（Package） | 1（Maven） |
| 无许可证文件 | 2 |
| 主要许可证 | Apache-2.0（100%） |

## 报告内容

1. **项目介绍**：Apache Commons Lang 的功能与背景
2. **工具安装过程**：Python 环境准备 → pip 安装 ScanCode → 遇到的问题与解决
3. **检测报告**：ScanCode 输出的 HTML 与 JSON 结果
4. **详细分析**：许可证分布、版权归属、合规性评价、工具评价

## 文件说明

| 文件 | 说明 |
|------|------|
| `report.html` | 可视化扫描报告，浏览器双击打开 |
| `report.json` | JSON 格式的原始扫描数据，含文件级许可证、版权、哈希、包信息 |
| `scan-command.txt` | 执行的扫描命令及参数说明 |

## 合规结论

Apache Commons Lang 3.14.0 的开源许可证合规状况**良好**：
- 所有源代码文件（.java）均包含标准的 Apache-2.0 许可证头，匹配率 100%
- 根目录包含完整的 LICENSE.txt 和 NOTICE.txt
- pom.xml 声明的许可证与扫描结果一致
- 仅 2 个非源代码配置文件缺少许可证头（属正常现象，不影响合规性）
- 未发现任何许可证冲突

## 免责声明

本报告由 ScanCode Toolkit 自动生成，仅供学习参考，不构成法律意见。如需正式合规结论，请咨询专业律师。
