# 股票分析系统任务文档

## 1. Overview
本任务文档基于股票分析系统的需求和设计文档，将系统实现分解为具体的任务列表，每个任务包含详细的实现要求和提示。

## 2. Tasks List

### Task 1: 项目初始化和基础架构搭建
- **Description**: 初始化项目结构，搭建基础架构，包括后端框架配置、数据库连接、依赖安装等。
- **Files**: 
  - `requirements.txt`
  - `app.py`
  - `config.py`
  - `database.py`
- **Requirements**: 所有功能的基础架构支持
- **_Prompt**: 实现项目初始化和基础架构搭建任务。首先创建项目的基本目录结构，然后配置Flask后端框架，设置MySQL和MongoDB数据库连接，安装必要的依赖包（如akshare、pandas、numpy、flask等）。确保项目能够正常启动，数据库连接正常。

### Task 2: 数据层实现 - akshare数据源接入
- **Description**: 实现akshare数据源的接入，包括股票基本信息、行情数据、财务数据的获取功能。
- **Files**: 
  - `data/akshare_data.py`
  - `data/data_processor.py`
- **Requirements**: 数据需求、单股票分析功能、主题筛选功能
- **_Prompt**: 实现akshare数据源接入任务。首先创建数据获取模块，封装akshare的API调用，实现股票基本信息、行情数据、财务数据的获取功能。然后创建数据处理模块，实现数据清洗、转换和整合功能。确保数据能够正确获取和处理，为业务逻辑层提供支持。

### Task 3: 单股票分析引擎实现
- **Description**: 实现单股票分析引擎，包括股票信息获取、规则分析执行、投资价值评估和风险分析功能。
- **Files**: 
  - `services/stock_analysis_engine.py`
  - `services/rules_manager.py`
- **Requirements**: 单股票分析功能
- **_Prompt**: 实现单股票分析引擎任务。首先创建股票分析引擎模块，实现股票信息获取、规则分析执行、投资价值评估和风险分析功能。然后创建规则管理模块，实现规则定义、存储和执行功能。确保分析引擎能够根据用户设定的规则执行分析，生成准确的投资价值和风险评估结果。

### Task 4: API层实现 - Stock API
- **Description**: 实现Stock API，包括股票基本信息查询、股票分析、规则设置等接口。
- **Files**: 
  - `api/stock_api.py`
  - `api/api_routes.py`
- **Requirements**: 单股票分析功能
- **_Prompt**: 实现Stock API任务。首先创建股票API模块，实现股票基本信息查询、股票分析、规则设置等接口。然后配置API路由，将接口暴露给前端。确保API接口符合设计文档中的规范，能够正确处理请求和返回响应。

### Task 5: 主题筛选引擎实现
- **Description**: 实现主题筛选引擎，包括主题/行业分类、筛选条件处理、排序算法和结果生成功能。
- **Files**: 
  - `services/theme_filter_engine.py`
  - `services/category_manager.py`
- **Requirements**: 主题/行业股票筛选功能
- **_Prompt**: 实现主题筛选引擎任务。首先创建主题筛选引擎模块，实现主题/行业分类、筛选条件处理、排序算法和结果生成功能。然后创建分类管理模块，实现主题和行业的管理功能。确保筛选引擎能够根据用户设定的条件执行筛选和排序，生成准确的股票列表。

### Task 6: API层实现 - Theme API
- **Description**: 实现Theme API，包括主题/行业查询、股票筛选、排序等接口。
- **Files**: 
  - `api/theme_api.py`
  - `api/api_routes.py`（更新）
- **Requirements**: 主题/行业股票筛选功能
- **_Prompt**: 实现Theme API任务。首先创建主题API模块，实现主题/行业查询、股票筛选、排序等接口。然后更新API路由，将新接口添加到路由配置中。确保API接口符合设计文档中的规范，能够正确处理请求和返回响应。

### Task 7: NLP分析模块实现
- **Description**: 实现NLP分析模块，包括文本分词、实体识别、关系抽取和情感分析功能。
- **Files**: 
  - `services/nlp_analysis.py`
  - `services/entity_recognizer.py`
- **Requirements**: 场景/新闻驱动股票分析功能
- **_Prompt**: 实现NLP分析模块任务。首先创建NLP分析模块，实现文本分词、实体识别、关系抽取和情感分析功能。然后创建实体识别模块，实现关键实体的识别和提取功能。确保NLP模块能够正确分析文本，识别关键实体和关系，为场景分析引擎提供支持。

### Task 8: 场景分析引擎实现
- **Description**: 实现场景分析引擎，包括文本分析、实体识别、供应链分析、上市状态查询和股权结构分析功能。
- **Files**: 
  - `services/scenario_analysis_engine.py`
  - `services/supply_chain_analyzer.py`
- **Requirements**: 场景/新闻驱动股票分析功能
- **_Prompt**: 实现场景分析引擎任务。首先创建场景分析引擎模块，实现文本分析、实体识别、供应链分析、上市状态查询和股权结构分析功能。然后创建供应链分析模块，实现供应链关系的构建和分析功能。确保场景分析引擎能够正确分析场景或新闻，生成相关企业信息和供应链关系。

### Task 9: API层实现 - Scenario API
- **Description**: 实现Scenario API，包括场景分析、实体查询、供应链信息查询等接口。
- **Files**: 
  - `api/scenario_api.py`
  - `api/api_routes.py`（更新）
- **Requirements**: 场景/新闻驱动股票分析功能
- **_Prompt**: 实现Scenario API任务。首先创建场景API模块，实现场景分析、实体查询、供应链信息查询等接口。然后更新API路由，将新接口添加到路由配置中。确保API接口符合设计文档中的规范，能够正确处理请求和返回响应。

### Task 10: 前端基础框架搭建
- **Description**: 搭建前端基础框架，包括React项目初始化、依赖安装、路由配置等。
- **Files**: 
  - `frontend/package.json`
  - `frontend/src/App.js`
  - `frontend/src/index.js`
  - `frontend/src/routes.js`
- **Requirements**: 所有前端功能的基础架构支持
- **_Prompt**: 实现前端基础框架搭建任务。首先使用create-react-app初始化React项目，然后安装必要的依赖包（如axios、react-router-dom、echarts等），配置路由系统，搭建基础的页面布局和组件结构。确保前端项目能够正常启动，路由配置正确。

### Task 11: 股票分析模块前端实现
- **Description**: 实现股票分析模块的前端界面，包括股票查询、分析结果展示、规则设置和数据可视化功能。
- **Files**: 
  - `frontend/src/components/StockAnalysis/StockQuery.js`
  - `frontend/src/components/StockAnalysis/AnalysisResult.js`
  - `frontend/src/components/StockAnalysis/RuleSetting.js`
  - `frontend/src/components/StockAnalysis/DataVisualization.js`
- **Requirements**: 单股票分析功能的前端展示
- **_Prompt**: 实现股票分析模块前端界面任务。首先创建股票查询组件，实现股票代码或名称的输入和查询功能。然后创建分析结果组件，展示投资价值评分和风险分析结果。接着创建规则设置组件，实现分析规则的自定义设置功能。最后创建数据可视化组件，实现股票价格走势图和财务指标图表的展示。确保前端界面美观、交互流畅，能够正确调用后端API获取和展示数据。

### Task 12: 主题筛选模块前端实现
- **Description**: 实现主题筛选模块的前端界面，包括主题/行业选择、筛选条件设置、排序设置和结果列表展示功能。
- **Files**: 
  - `frontend/src/components/ThemeFilter/ThemeSelection.js`
  - `frontend/src/components/ThemeFilter/FilterCondition.js`
  - `frontend/src/components/ThemeFilter/SortSetting.js`
  - `frontend/src/components/ThemeFilter/ResultList.js`
- **Requirements**: 主题/行业股票筛选功能的前端展示
- **_Prompt**: 实现主题筛选模块前端界面任务。首先创建主题/行业选择组件，实现主题和行业的选择功能。然后创建筛选条件设置组件，实现多条件筛选的设置功能。接着创建排序设置组件，实现排序规则的设置功能。最后创建结果列表组件，展示筛选后的股票列表和关键指标。确保前端界面美观、交互流畅，能够正确调用后端API获取和展示数据。

### Task 13: 场景分析模块前端实现
- **Description**: 实现场景分析模块的前端界面，包括场景/新闻输入、实体识别结果展示、供应链关系图和企业信息列表展示功能。
- **Files**: 
  - `frontend/src/components/ScenarioAnalysis/ScenarioInput.js`
  - `frontend/src/components/ScenarioAnalysis/EntityRecognition.js`
  - `frontend/src/components/ScenarioAnalysis/SupplyChainGraph.js`
  - `frontend/src/components/ScenarioAnalysis/CompanyList.js`
- **Requirements**: 场景/新闻驱动股票分析功能的前端展示
- **_Prompt**: 实现场景分析模块前端界面任务。首先创建场景/新闻输入组件，实现场景描述或新闻内容的输入功能。然后创建实体识别结果组件，展示识别的关键实体。接着创建供应链关系图组件，实现供应链关系的可视化展示。最后创建企业信息列表组件，展示相关企业信息和标签。确保前端界面美观、交互流畅，能够正确调用后端API获取和展示数据。

### Task 14: 系统整合和测试
- **Description**: 整合所有模块，进行系统测试，包括功能测试、性能测试、API测试等。
- **Files**: 
  - `test/test_api.py`
  - `test/test_services.py`
- **Requirements**: 所有功能的正确性和稳定性
- **_Prompt**: 实现系统整合和测试任务。首先整合所有模块，确保各个模块之间能够正常通信和协作。然后编写测试用例，进行功能测试、性能测试和API测试。修复测试中发现的问题，优化系统性能。确保系统能够正常运行，所有功能符合需求和设计要求。

### Task 15: 文档完善和部署准备
- **Description**: 完善系统文档，包括API文档、用户手册、部署指南等，准备系统部署。
- **Files**: 
  - `README.md`
  - `API_DOC.md`
  - `DEPLOYMENT_GUIDE.md`
- **Requirements**: 系统的可维护性和可部署性
- **_Prompt**: 实现文档完善和部署准备任务。首先完善系统文档，包括项目介绍、API文档、用户手册、部署指南等。然后准备系统部署，包括Docker镜像构建、部署脚本编写等。确保文档清晰完整，部署流程简单明了，便于系统的维护和部署。

## 3. Implementation Guidelines

### 3.1 代码规范
- 遵循PEP8 Python代码规范
- 遵循React代码规范
- 使用有意义的变量和函数名
- 添加适当的注释

### 3.2 数据处理
- 使用pandas和numpy进行数据处理
- 确保数据的准确性和完整性
- 实现数据缓存机制，提高性能

### 3.3 API设计
- 遵循RESTful API设计规范
- 使用JSON格式的请求和响应
- 实现适当的错误处理和状态码
- 提供API文档

### 3.4 前端开发
- 使用React组件化开发
- 实现响应式设计
- 使用ECharts或Plotly进行数据可视化
- 确保界面美观、交互流畅

### 3.5 测试要求
- 编写单元测试和集成测试
- 确保测试覆盖率≥80%
- 进行性能测试，确保系统响应时间符合要求

### 3.6 安全要求
- 实现API认证和授权
- 进行输入验证，防止注入攻击
- 配置CORS，防止跨站请求伪造
- 加密敏感数据

## 4. 任务执行顺序
建议按照以下顺序执行任务：
1. 项目初始化和基础架构搭建
2. 数据层实现 - akshare数据源接入
3. 单股票分析引擎实现
4. API层实现 - Stock API
5. 主题筛选引擎实现
6. API层实现 - Theme API
7. NLP分析模块实现
8. 场景分析引擎实现
9. API层实现 - Scenario API
10. 前端基础框架搭建
11. 股票分析模块前端实现
12. 主题筛选模块前端实现
13. 场景分析模块前端实现
14. 系统整合和测试
15. 文档完善和部署准备

## 5. 成功标准
- 所有任务完成，代码实现符合要求
- 系统能够正常运行，所有功能正常工作
- 数据能够正确获取和处理
- API接口符合设计规范，能够正确响应
- 前端界面美观、交互流畅
- 系统性能符合要求，响应时间在规定范围内
- 文档完整清晰，便于维护和部署