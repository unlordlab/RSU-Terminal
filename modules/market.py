        width: 100%;
}

.header {
    background: #0c0e12;
    padding: 12px 15px;
    border-bottom: 1px solid #1a1e26;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.title {
    color: white;
    font-size: 14px;
    font-weight: bold;
}

.tooltip-container {
    position: relative;
    cursor: help;
}

.tooltip-icon {
    width: 26px;
    height: 26px;
    border-radius: 50%;
    background: #1a1e26;
    border: 2px solid #555;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #aaa;
    font-size: 16px;
    font-weight: bold;
}

.tooltip-text {
    visibility: hidden;
    width: 260px;
    background-color: #1e222d;
    color: #eee;
    text-align: left;
    padding: 10px 12px;
    border-radius: 6px;
    position: absolute;
    z-index: 999;
    top: 35px;
    right: -10px;
    opacity: 0;
    transition: opacity 0.3s;
    font-size: 12px;
    border: 1px solid #444;
    box-shadow: 0 4px 12px rgba(0,0,0,0.4);
}

.tooltip-container:hover .tooltip-text {
    visibility: visible;
    opacity: 1;
}

.content {
    background: #11141a;
    height: 340px;
    overflow-y: auto;
}
</style>
</head>
<body>
<div class="container">
    <div class="header">
        <div class="title">Notícies d'Alt Impacte</div>
        <div class="tooltip-container">
            <div class="tooltip-icon">?</div>
            <div class="tooltip-text">''' + tooltip_text + '''</div>
        </div>
    </div>
    <div class="content">
        ''' + news_content + '''
    </div>
</div>    
