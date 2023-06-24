# Splatoon 3 地图查询插件

> QQ 机器人 SplatBot 已搭载该插件，可以[点击这里](https://flawless-dew-f3c.notion.site/SplatBot-e91a70e4f32a4fffb640ce8c3ba9c664)查看使用指南

## 已实现功能

### 对战地图查询

1. 简单地图查询：
    - `/图`：查询当前时段图
    - `/下图`：查询下个时段图
    - `/图图`：查询当前时段和下个时段图
    - `/下图图`：查询下个时段和下下个时段图

2.	选择时段查询： 举例：可以通过`023图`来查询当前时段(0)、下下个时段(2)、下下下个时段的地图(3)。Tips：该条指令和后面的两条指令，都不需要加斜杠

3.	选择时段进行模式筛选查询：举例：可以通过`023区域开放`来查询这三个时段中真格模式（开放）中区域模式的地图；也可以通过`023挑战`来查询这三个时段中真格模式（挑战）的地图。（关键词：(区域，推塔，蛤蜊，抢鱼)，(涂地，挑战，开放，X段)）

4.	模式筛选查询：如果要查询 24 小时时段内的地图并进行模式筛选，可以通过类似`全部区域挑战`的方式来对 24 小时时段内的地图进行筛选。同样地，`全部挑战`也有效。

- 例如：`全部蛤蜊挑战`, `12推塔X段`, `全部开放` 等都是正确的用法。

（祭典期间1～4的功能会关闭，因为祭典期间没有分配模式地图，大家只管上线开打就好啦！）

### 打工地图查询

1. 查看当期工与下期工的时间、详情：`/工`
2. 查看从当期开始后连续 5 期工的信息：`/全部工`

### 娱乐功能

1.随机武器功！`/随机武器`

---

## 安装指南

### 手动安装

```shell
git clone https://github.com/Skyminers/Bot-Splatoon3.git
```

在 nonebot2 框架中，将本仓库代码内的`nonebot_plugin_splatoon3`文件夹置于插件目录(`src/plugins`)即可正常加载

