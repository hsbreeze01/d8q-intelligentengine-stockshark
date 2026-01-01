const API_BASE_URL = 'http://localhost:5001/api';

let stockChart = null;

document.addEventListener('DOMContentLoaded', function() {
    initTabs();
    initStockSearch();
    initScenarioSearch();
});

function initTabs() {
    const tabButtons = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');

    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const targetTab = button.dataset.tab;

            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabContents.forEach(content => content.classList.remove('active'));

            button.classList.add('active');
            document.getElementById(targetTab).classList.add('active');
        });
    });
}

function initStockSearch() {
    const searchBtn = document.getElementById('search-stock-btn');
    const input = document.getElementById('stock-code-input');

    searchBtn.addEventListener('click', handleStockSearch);
    input.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            handleStockSearch();
        }
    });
}

function initScenarioSearch() {
    const searchBtn = document.getElementById('search-scenario-btn');
    const input = document.getElementById('scenario-input');

    searchBtn.addEventListener('click', handleScenarioSearch);
    input.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            handleScenarioSearch();
        }
    });
}

async function handleStockSearch() {
    const stockCode = document.getElementById('stock-code-input').value.trim();
    
    if (!stockCode) {
        showError('stock-trend', '请输入股票代码');
        return;
    }

    const searchBtn = document.getElementById('search-stock-btn');
    const originalText = searchBtn.textContent;
    searchBtn.textContent = '查询中...';
    searchBtn.disabled = true;
    
    try {
        const response = await fetch(`${API_BASE_URL}/analysis/stock/quote?symbol=${stockCode}`);
        const result = await response.json();

        if (result.success && result.data) {
            displayStockInfo(result.data);
            await loadStockHistory(stockCode);
            await loadStockSectors(stockCode);
        } else {
            showError('stock-trend', result.error || '获取股票信息失败');
        }
    } catch (error) {
        showError('stock-trend', '网络请求失败，请稍后重试');
        console.error('Error fetching stock data:', error);
    } finally {
        searchBtn.textContent = originalText;
        searchBtn.disabled = false;
    }
}

async function loadStockHistory(stockCode) {
    try {
        const endDate = new Date();
        const startDate = new Date();
        startDate.setDate(startDate.getDate() - 90);
        
        const startDateStr = startDate.toISOString().split('T')[0];
        const endDateStr = endDate.toISOString().split('T')[0];
        
        const response = await fetch(`${API_BASE_URL}/analysis/stock/history?symbol=${stockCode}&start_date=${startDateStr}&end_date=${endDateStr}`);
        const result = await response.json();

        if (result.success && result.data && result.data.length > 0) {
            displayStockChart(result.data);
        } else {
            document.getElementById('stock-chart-container').style.display = 'none';
        }
    } catch (error) {
        console.error('Error fetching stock history:', error);
        document.getElementById('stock-chart-container').style.display = 'none';
    }
}

async function loadStockSectors(stockCode) {
    try {
        const response = await fetch(`${API_BASE_URL}/analysis/stock/sectors?symbol=${stockCode}`);
        const result = await response.json();

        if (result.success && result.data) {
            displayStockSectors(result.data);
        }
    } catch (error) {
        console.error('Error fetching stock sectors:', error);
    }
}

function displayStockInfo(data) {
    const infoContainer = document.getElementById('stock-info');
    
    const name = data.name || data.symbol || '未知';
    const symbol = data.symbol || 'N/A';
    const close = data.close || data.price || '0.00';
    const changePct = data.change_pct !== undefined ? data.change_pct : 0;
    const volume = data.volume || 0;
    const amount = data.amount || 0;
    const open = data.open || '0.00';
    const high = data.high || '0.00';
    const low = data.low || '0.00';
    const preClose = data.pre_close || '0.00';
    
    const changeClass = changePct >= 0 ? 'positive' : 'negative';
    const changeIcon = changePct >= 0 ? '↑' : '↓';
    
    infoContainer.innerHTML = `
        <div class="stock-header">
            <h2>${name}</h2>
            <span class="stock-code">${symbol}</span>
        </div>
        <div class="stock-details">
            <div class="detail-item">
                <span class="label">最新价</span>
                <span class="value">${close}</span>
            </div>
            <div class="detail-item">
                <span class="label">涨跌幅</span>
                <span class="value ${changeClass}">${changeIcon} ${changePct}%</span>
            </div>
            <div class="detail-item">
                <span class="label">成交量</span>
                <span class="value">${formatVolume(volume)}</span>
            </div>
            <div class="detail-item">
                <span class="label">成交额</span>
                <span class="value">${formatAmount(amount)}</span>
            </div>
            <div class="detail-item">
                <span class="label">开盘价</span>
                <span class="value">${open}</span>
            </div>
            <div class="detail-item">
                <span class="label">最高价</span>
                <span class="value">${high}</span>
            </div>
            <div class="detail-item">
                <span class="label">最低价</span>
                <span class="value">${low}</span>
            </div>
            <div class="detail-item">
                <span class="label">昨收</span>
                <span class="value">${preClose}</span>
            </div>
        </div>
    `;
    
    infoContainer.style.display = 'block';
}

function displayStockSectors(data) {
    const sectorsContainer = document.getElementById('stock-sectors');
    
    if (!sectorsContainer) {
        const infoContainer = document.getElementById('stock-info');
        const sectorsHtml = `
            <div id="stock-sectors" class="stock-sectors">
                <h3>所属板块</h3>
                <div class="sectors-content">
                    <div class="sector-section">
                        <h4>行业</h4>
                        <div class="sector-item">
                            <span class="sector-name">${data.industry.name || '未知'}</span>
                            <span class="sector-count">${data.industry.stock_count || 0}只股票</span>
                        </div>
                    </div>
                    <div class="sector-section">
                        <h4>概念</h4>
                        <div class="concepts-list">
                            ${data.concepts.length > 0 ? data.concepts.map(concept => `
                                <div class="concept-item">
                                    <span class="concept-name">${concept.name}</span>
                                    <span class="concept-count">${concept.stock_count}只</span>
                                </div>
                            `).join('') : '<div class="no-concepts">暂无概念信息</div>'}
                        </div>
                    </div>
                </div>
            </div>
        `;
        infoContainer.insertAdjacentHTML('afterend', sectorsHtml);
        document.getElementById('stock-sectors').style.display = 'block';
    } else {
        sectorsContainer.innerHTML = `
            <h3>所属板块</h3>
            <div class="sectors-content">
                <div class="sector-section">
                    <h4>行业</h4>
                    <div class="sector-item">
                        <span class="sector-name">${data.industry.name || '未知'}</span>
                        <span class="sector-count">${data.industry.stock_count || 0}只股票</span>
                    </div>
                </div>
                <div class="sector-section">
                    <h4>概念</h4>
                    <div class="concepts-list">
                        ${data.concepts.length > 0 ? data.concepts.map(concept => `
                            <div class="concept-item">
                                <span class="concept-name">${concept.name}</span>
                                <span class="concept-count">${concept.stock_count}只</span>
                            </div>
                        `).join('') : '<div class="no-concepts">暂无概念信息</div>'}
                    </div>
                </div>
            </div>
        `;
        sectorsContainer.style.display = 'block';
    }
}

function displayStockChart(data) {
    const chartContainer = document.getElementById('stock-chart-container');
    chartContainer.style.display = 'block';

    const ctx = document.getElementById('stock-chart').getContext('2d');
    
    if (stockChart) {
        stockChart.destroy();
    }

    const labels = data.map(item => item.date);
    const prices = data.map(item => item.close);
    const volumes = data.map(item => item.volume);

    stockChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: '收盘价',
                data: prices,
                borderColor: 'rgb(102, 126, 234)',
                backgroundColor: 'rgba(102, 126, 234, 0.1)',
                borderWidth: 2,
                fill: true,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    position: 'top'
                },
                tooltip: {
                    mode: 'index',
                    intersect: false
                }
            },
            scales: {
                x: {
                    display: true,
                    title: {
                        display: true,
                        text: '日期'
                    }
                },
                y: {
                    display: true,
                    title: {
                        display: true,
                        text: '价格'
                    }
                }
            }
        }
    });
}

async function handleScenarioSearch() {
    const keyword = document.getElementById('scenario-input').value.trim();
    
    if (!keyword) {
        showError('scenario-results', '请输入关键字');
        return;
    }

    const searchBtn = document.getElementById('search-scenario-btn');
    const originalText = searchBtn.textContent;
    searchBtn.textContent = '搜索中...';
    searchBtn.disabled = true;
    
    const resultsContainer = document.getElementById('scenario-results');
    resultsContainer.innerHTML = '<div class="loading"><div class="spinner"></div><p>正在搜索相关企业...</p></div>';
    resultsContainer.style.display = 'block';
    
    try {
        const response = await fetch(`${API_BASE_URL}/search/stock/by-keyword?keyword=${encodeURIComponent(keyword)}`);
        const result = await response.json();

        if (result.success && result.data && result.data.length > 0) {
            displayScenarioResults(result.data);
        } else {
            showError('scenario-results', result.error || '未找到相关公司信息');
        }
    } catch (error) {
        showError('scenario-results', '网络请求失败，请稍后重试');
        console.error('Error fetching scenario data:', error);
    } finally {
        searchBtn.textContent = originalText;
        searchBtn.disabled = false;
    }
}

function displayScenarioResults(data) {
    const resultsContainer = document.getElementById('scenario-results');
    
    if (!data || data.length === 0) {
        resultsContainer.innerHTML = '<p class="no-results">未找到相关企业信息</p>';
        resultsContainer.style.display = 'block';
        return;
    }

    let html = '<div class="results-list">';
    
    data.forEach((item, index) => {
        const companyName = item.company_name || item.name || '未知公司';
        const description = item.description || item.business || '暂无描述';
        const stockCode = item.stock_code || '';
        const isListed = item.is_listed !== undefined ? item.is_listed : false;
        const hasHolding = item.has_holding !== undefined ? item.has_holding : false;
        
        const listedStatus = isListed ? 
            '<span class="badge listed">已上市</span>' : 
            '<span class="badge unlisted">未上市</span>';
        
        const stockInfo = stockCode ? 
            `<div class="stock-info">股票代码: ${stockCode}</div>` : '';
        
        const holdingInfo = hasHolding ? 
            '<div class="holding-info">有上市公司持股</div>' : '';

        html += `
            <div class="result-card">
                <div class="result-header">
                    <h3>${companyName}</h3>
                    ${listedStatus}
                </div>
                <div class="result-body">
                    <div class="result-description">${description}</div>
                    ${stockInfo}
                    ${holdingInfo}
                </div>
            </div>
        `;
    });
    
    html += '</div>';
    resultsContainer.innerHTML = html;
    resultsContainer.style.display = 'block';
}


function showError(sectionId, message) {
    const section = document.getElementById(sectionId);
    const errorHtml = `
        <div class="error-message">
            <span class="error-icon">⚠️</span>
            <span class="error-text">${message}</span>
        </div>
    `;
    
    const existingError = section.querySelector('.error-message');
    if (existingError) {
        existingError.remove();
    }
    
    section.insertAdjacentHTML('afterbegin', errorHtml);
    
    setTimeout(() => {
        const errorElement = section.querySelector('.error-message');
        if (errorElement) {
            errorElement.remove();
        }
    }, 5000);
}

function formatVolume(volume) {
    if (!volume) return '0';
    if (volume >= 100000000) {
        return (volume / 100000000).toFixed(2) + '亿';
    } else if (volume >= 10000) {
        return (volume / 10000).toFixed(2) + '万';
    }
    return volume.toString();
}

function formatAmount(amount) {
    if (!amount) return '0';
    if (amount >= 100000000) {
        return (amount / 100000000).toFixed(2) + '亿';
    } else if (amount >= 10000) {
        return (amount / 10000).toFixed(2) + '万';
    }
    return amount.toString();
}

function checkTradingDay() {
    const today = new Date();
    const dayOfWeek = today.getDay();
    
    if (dayOfWeek === 0 || dayOfWeek === 6) {
        return false;
    }
    
    return true;
}

function showNonTradingDayWarning() {
    const warningHtml = `
        <div class="warning-message">
            <span class="warning-icon">📅</span>
            <span class="warning-text">今天是非交易日，数据可能不是最新的</span>
        </div>
    `;
    
    const stockTrendSection = document.getElementById('stock-trend');
    const existingWarning = stockTrendSection.querySelector('.warning-message');
    
    if (!existingWarning && !checkTradingDay()) {
        stockTrendSection.insertAdjacentHTML('afterbegin', warningHtml);
    }
}

document.addEventListener('DOMContentLoaded', function() {
    showNonTradingDayWarning();
});