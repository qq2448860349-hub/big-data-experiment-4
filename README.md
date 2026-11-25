# 实验四 并行化频繁项集挖掘

使用 Apriori 算法，从购物篮中找出出现频率不低于 15% 的商品组合。提供单进程 Python 和 Spark RDD 两个版本，比较全部频繁项集、整数出现次数和输出文件字节。

## 数据与运行环境

数据为自行生成的教学购物篮，固定种子 20261118，共 30000 笔交易、12 种商品，保存在 data/transactions.txt。每行是一笔交易，商品之间用空格分隔，同行重复商品只计一次，空行忽略。data/manifest.json 记录来源、种子及 SHA256。数据含早餐、水果、咖啡等预设购买组合及随机添加商品，不能描述为真实超市采集数据。

Ubuntu 22.04，用户名 vboxuser，Java 8，Hadoop 3.2.2，Spark 3.5.8，Python 3.10。Hadoop 目录 /home/vboxuser/hadoop，Spark 目录 /home/vboxuser/spark-3.5.8-bin-hadoop3。沿用实验三已安装的环境。

包解压到 /home/vboxuser，得到 /home/vboxuser/experiment4。HDFS 工作路径只使用 /user/vboxuser/experiment4，每次运行自动建立新子目录。

## 操作顺序

先启动原有 Hadoop 服务，在终端运行下列命令。普通启动使用 start-dfs.sh 和 start-yarn.sh。

```bash
cd /home/vboxuser/experiment4
bash scripts/check_environment.sh
```

正常结束显示 Environment check passed。若提示 Missing NameNode 等，先启动 HDFS 和 YARN 再检查。遇到错误保留完整命令、报错首尾及 jps 输出。

然后运行独立小样例核对。

```bash
bash scripts/self_test.sh
```

正常结束显示 OK。这一步使用穷举参考和分区计数核对算法，实际 Spark 作业由下一步执行。

```bash
bash scripts/run_all.sh
```

该脚本先执行单机算法，再把同一数据上传至 HDFS，通过 YARN 运行 Spark 算法。配置一个 Executor、两个计算核，输入至少四个分区。成功时显示 MATCH 及 EXPERIMENT4 PASS。records 下本次运行目录包含 serial.tsv、spark.tsv、两份统计 JSON 和 run.log；失败时同一目录保留日志。每次运行建立新目录，可直接重试。

在虚拟机 Firefox 打开 http://localhost:8088，找到 experiment4-apriori。确认应用类型 SPARK、状态 FINISHED、最终状态 SUCCEEDED，并保存页面截图。应用真实编号也写入 spark.json 和 run.log。

## 算法与精度

最小出现次数用十进制支持度乘有效交易数并向上取整，正式数据的阈值为 4500。Apriori 从单商品开始，保留满足阈值的组合，再通过连接和子集剪枝产生下一层候选，直到没有下一层候选。完整挖掘全部频繁项集，没有人为限制项集长度。

单机版在一个 Python 进程里扫描交易并计数。Spark 版缓存交易 RDD，广播本轮候选，各分区先汇总候选的出现次数，再用 reduceByKey 合并整数计数，驱动端负责剪枝。交易明细不 collect 到驱动端。

输出按项集长度及商品名排序，列为 items、count、transactions、support。count 为包含该组合的交易数，support=count/transactions，展示为十位小数。两种实现均使用整数计数，核对程序检查全部项集、计数、分母和格式化输出，同时比较文件字节及 SHA256。

统计 JSON 记录各层候选数量、频繁项集数量和耗时。Spark elapsed_seconds 包含会话启动、读入、计算和写出，serial elapsed_seconds 包含读取、计算和写出。小数据和单机伪分布式环境可能出现 Spark 更慢，报告按真实耗时解释，不预填加速比。

## 目录

- serial_apriori.py 为单机实现，spark_apriori.py 为并行实现。
- mining.py 提供统一解析、候选生成、分区计数及输出格式。
- generate_data.py 生成数据，已有数据的校验信息见 data/manifest.json。重新生成时选一个新的 --directory，以免覆盖本次输入。
- verify_results.py 比较两种实际运行结果。
- scripts 提供环境检查、自测及正式运行入口。
- tests 含独立穷举核对，覆盖多层剪枝、重复商品、阈值边界及空分区。
- docs/报告记录.md 列出报告需要记录的信息。

## 报告与代码提交

用实际截图记录环境检查、单机完成输出、Spark YARN 成功页面、两种结果及 MATCH 信息。报告按原题不超过8页，宋体小四、1.25倍行距并导出 PDF。原题写明12月9日前提交，以教师最新通知为准。源码整理上传至公开 GitHub 仓库，并将真实链接写入报告，上传时保留代码、data、scripts、tests、docs 和 README。

## 实际运行结果

2026年11月25日在上述 Ubuntu 虚拟机完成正式运行，30000笔交易共得到45个频繁项集，单机与Spark结果逐项及逐字节一致，终端显示 EXPERIMENT4 PASS。单机耗时约0.9384秒，Spark程序耗时约129.5894秒。

Spark应用编号为 application_1795570037929_0001，YARN详情页显示类型 SPARK、名称 experiment4-apriori、状态 FINISHED、最终状态 SUCCEEDED。YARN页面显示耗时1分39秒。该页面统计应用在YARN中的时间，程序计时还包含Spark会话启动等过程。

真实输出示例为 milk 的出现次数19518、支持度0.6506000000；apple,banana 的出现次数6275、支持度0.2091666667。输入为教学合成数据。Spark在本次小规模、单机伪分布式实验中耗时更长，报告按实际结果分析。

Spark RDD、广播及提交接口参考官方指南 https://spark.apache.org/docs/3.5.8/rdd-programming-guide.html 。
