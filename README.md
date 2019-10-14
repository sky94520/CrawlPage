# 专利爬虫
## 1. scrapy
异步爬虫框架
## 2. Splash
轻量级的web浏览器

> Scrapy负责构造请求，之后请求交给Splash（可以是远程服务器）进行解析，
> Splash会根据对应的lua脚本来解析请求后并返回字符串给scrapy，之后则交给
> scrapy
>针对知网专利，
### splash笔记
> 1. splash如何显示等待页面的加载
> 2. splash主要通过splash:evaljs(js代码)来获取到页面信息
> 3. splash:wait()可以异步等待若干秒,即会做其他的任务，之后再继续执行。
> 4. render.html render.png render.jpeg render.har render.json 包含着大量通用
> 的功能，但是仅仅这样还是不太够的，这时候可以使用execute run。
> splash使用的是lua，详情:[splash lua](https://splash.readthedocs.io/en/stable/scripting-overview.html)

## 思路
>在初始时，启动器会检测redis是否存在一个字典
>process {"code": "A", "page": 1, "total_count": 0, "cur_count": 0}
>以此来确定从哪启动，上面的为默认值。在每次抓取一个页面成功的时候,都会更新page的值。
>抓取器在每次抓取页面时，会同时保存页面和解析页面，它也会判断当前的页面个数。
### 文件命名规范
> 1. 列表页命名 文件夹为code，文件名为页码
> 2. 详情页命名 待定
## 调度器
>1. 获取process的值，如果没有，则赋予默认值;
>2. 根据值，生成链接，
>3. 根据链接爬取页面
>4. 按照code为文件夹名和页码为文件名保存爬取到的页面
>5. 对爬取到的页面解析，获取总个数，并解析链接，并把得到的链接放入【】中，之后更新process的进度值。
>6. 判断当前解析的个数是否等于总个数，如果等于，则表示这个类别
>爬取完成，则接着向下个类别爬取；否则继续从步骤1开始。

## 断点
>断点恢复时，会判断该点有没有子孩子，（其实不应该停留在非叶节点），如果有子孩子，则找到
>第一个叶节点，之后发起请求来获取数据。当叶节点请求数据完毕后，则会找它的下一个兄弟节点，
>重复上述操作。当发现自己是最后一个节点的时候，则会找到父节点的下一个节点。以此类推。
## 问题
> 1. 当某一类别的数据超过6000个时，则只能获取6000个数据，当前的办法是按照公开日再次进行
>拆分，在cookie中添加date_gkr_from date_gkr_to两个字段。
>目前就出现两种，第一种是小于6000个值的，此时不需要拆分，直接进行即可。
>第二种是大于6000的则按照年份拆分，这样的问题主要在于文件名和断点。
>按照年份拆分时，会根据当前值和总值来判断是否应该结束。从当年依次减少1。
>process 增加一个year字段
> 2. 进行统计 统计各个文件夹的所有链接个数，去重之后的个数，按照树型结构合并的个数。
>## 启动问题
>schedule.py为一个进程，scrapy为另外一个进程。
>编写一个shell脚本。这个脚本由docker的命令行启动；这个脚本主要有两个功能
>第一个是启动scheduler.py，负责爬取列表网页；另外一个则是设置crontab的定时启动，每隔
>若干个小时尝试启动另外一个脚本，它的主要功能则是判断scrapy进程是否在运行，如果不是，则尝试
>启动
>流程：
>首先会获取当前要爬取的类别（叶节点）
>接着判断第一次运行或者判断是否达到总数目，满足条件则向下执行；
>获取当前条件下的数量,第一次如果超过6000，则按照以年为单位,
>如果在以年为单位的情况下发生超过6000的情况，则以12 /2 = 6
>如果仍然超过，则6 / 2 = 3
>注：以月份为条件的情况仅仅适用于这一年，其他的年份则需要依次判断。
>
>## 新的页面爬虫
>旧的页面爬虫使用requests，不仅效率低下，而且爬取缓慢。故切换成scrapy进行爬取
>另外，则根据类别进行爬取。
>首先需要判断的是cookie的问题


爬取翻页的功能是不变的，主要在于cookie的选择。
再有就是使用到.env，用于区别测试环境和生产环境，二者分开，以便于调试。

爬取规则放入配置文件中，要爬取的类别放入redis之中

cookie负责查询的条件，同一类，cookie是相同的，只不过在出现验证码的时候，
统一进行切换即可。
现在有两种方法：
>1. 每次只爬取一类，爬取完毕后程序退出。能完整地保证这一类的日志等，也方便管理。
>>每次只爬取一类的话，就需要外部有一个启动器，用来启动这个爬虫，这个不着急。
>先把大致的框架做好
>2. ~~while 从redis拿取所有的，不利于断点重开。~~

##当要爬取的页面的条目个数大于阈值时的处理
> 首先是要先获取一次页面才能知道在这个分类下的个数，然后再尝试按照当前的日期并且减去
>365天来获取这约一年的个数（保证按照年份，便于调试），如果仍然大于阈值，则依次
>除以2.
>逻辑上讲，days只有在第一次爬取的时候就已经确定了个数，它可以放在start_request中

## middleware
> 设置代理，会发送请求requests获取代理
> 设置cookie，会检测spider之前的cookie是否已经不可用，如果不可用，则重新发起请求获取
> 重写最大值重试次数中间件 功能只是添加了一个日志输出