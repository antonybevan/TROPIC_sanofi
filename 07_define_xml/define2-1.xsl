<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                xmlns:def="http://www.cdisc.org/ns/def/v2.1"
                exclude-result-prefixes="def">
  
  <xsl:output method="html" version="4.0" encoding="UTF-8" indent="yes"/>

  <xsl:template match="/">
    <html>
      <head>
        <title>TROPIC Study - CDISC ADaM Define-XML v2.1.0</title>
        <style>
          body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background-color: #f3f4f6;
            color: #1f2937;
            margin: 0;
            padding: 0;
            display: flex;
            height: 100vh;
            overflow: hidden;
          }
          
          /* Sidebar Styling */
          .sidebar {
            width: 280px;
            background-color: #0b1e36;
            color: #f3f4f6;
            display: flex;
            flex-direction: column;
            border-right: 1px solid #1e293b;
            flex-shrink: 0;
          }
          
          .sidebar-header {
            padding: 24px 20px;
            border-bottom: 1px solid #1e293b;
            background-color: #071424;
          }
          
          .sidebar-title {
            font-size: 18px;
            font-weight: 700;
            margin: 0;
            color: #38bdf8;
            letter-spacing: 0.5px;
          }
          
          .sidebar-subtitle {
            font-size: 11px;
            color: #94a3b8;
            margin: 4px 0 0 0;
            text-transform: uppercase;
            letter-spacing: 1px;
          }
          
          .sidebar-menu {
            flex-grow: 1;
            overflow-y: auto;
            padding: 20px 12px;
          }
          
          .menu-section-title {
            font-size: 11px;
            color: #64748b;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            margin: 16px 8px 8px 8px;
          }
          
          .menu-item {
            display: flex;
            align-items: center;
            padding: 10px 12px;
            color: #cbd5e1;
            text-decoration: none;
            border-radius: 6px;
            font-size: 14px;
            margin-bottom: 4px;
            transition: all 0.2s ease;
            cursor: pointer;
            border: 1px solid transparent;
          }
          
          .menu-item:hover {
            background-color: #1e293b;
            color: #ffffff;
          }
          
          .menu-item.active {
            background-color: #0284c7;
            color: #ffffff;
            font-weight: 600;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
            border-color: #38bdf8;
          }
          
          .dataset-badge {
            font-size: 10px;
            background-color: #1e293b;
            color: #94a3b8;
            padding: 2px 6px;
            border-radius: 4px;
            margin-left: auto;
            font-weight: 500;
          }
          
          .menu-item.active .dataset-badge {
            background-color: #0369a1;
            color: #e0f2fe;
          }
          
          /* Main Content Area */
          .main-content {
            flex-grow: 1;
            display: flex;
            flex-direction: column;
            overflow: hidden;
            background-color: #f8fafc;
          }
          
          .top-bar {
            background-color: #ffffff;
            padding: 16px 32px;
            border-bottom: 1px solid #e2e8f0;
            display: flex;
            align-items: center;
            justify-content: space-between;
            flex-shrink: 0;
            box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05);
          }
          
          .study-info {
            display: flex;
            flex-direction: column;
          }
          
          .study-title {
            font-size: 18px;
            font-weight: 700;
            color: #0f172a;
            margin: 0;
          }
          
          .metadata-pills {
            display: flex;
            gap: 8px;
            margin-top: 6px;
          }
          
          .pill {
            font-size: 11px;
            background-color: #f1f5f9;
            color: #475569;
            padding: 3px 8px;
            border-radius: 9999px;
            border: 1px solid #e2e8f0;
            font-weight: 500;
          }
          
          .pill-blue {
            background-color: #e0f2fe;
            color: #0369a1;
            border-color: #bae6fd;
          }
          
          .content-view {
            padding: 32px;
            overflow-y: auto;
            flex-grow: 1;
          }
          
          .dataset-panel {
            display: none;
            animation: fadeIn 0.25s ease-out;
          }
          
          .dataset-panel.active {
            display: block;
          }
          
          @keyframes fadeIn {
            from { opacity: 0; transform: translateY(4px); }
            to { opacity: 1; transform: translateY(0); }
          }
          
          /* Cards and Tables */
          .card {
            background: #ffffff;
            border-radius: 8px;
            border: 1px solid #e2e8f0;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.02);
            padding: 24px;
            margin-bottom: 24px;
          }
          
          .card-title {
            font-size: 16px;
            font-weight: 700;
            color: #0f172a;
            margin: 0 0 16px 0;
            padding-bottom: 12px;
            border-bottom: 1px solid #f1f5f9;
            display: flex;
            align-items: center;
          }
          
          .grid-2 {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
          }
          
          .meta-item {
            margin-bottom: 12px;
          }
          
          .meta-label {
            font-size: 12px;
            color: #64748b;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
          }
          
          .meta-value {
            font-size: 14px;
            color: #1e293b;
            margin-top: 4px;
            font-weight: 500;
          }
          
          table {
            width: 100%;
            border-collapse: separate;
            border-spacing: 0;
            margin-top: 8px;
            border: 1px solid #e2e8f0;
            border-radius: 6px;
            overflow: hidden;
          }
          
          th {
            background-color: #f8fafc;
            color: #475569;
            font-weight: 600;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            padding: 12px 16px;
            text-align: left;
            border-bottom: 1px solid #e2e8f0;
          }
          
          td {
            padding: 12px 16px;
            font-size: 13.5px;
            color: #334155;
            border-bottom: 1px solid #f1f5f9;
            vertical-align: top;
          }
          
          tr:last-child td {
            border-bottom: none;
          }
          
          tr:hover td {
            background-color: #f8fafc;
          }
          
          .var-name {
            font-family: Menlo, Monaco, Consolas, "Courier New", monospace;
            font-weight: 700;
            color: #0369a1;
          }
          
          .var-type {
            font-size: 11px;
            background-color: #f1f5f9;
            color: #475569;
            padding: 2px 6px;
            border-radius: 4px;
            font-weight: 500;
          }
          
          .method-desc {
            font-size: 12.5px;
            color: #475569;
            line-height: 1.5;
            background-color: #fafafa;
            padding: 8px 12px;
            border-left: 3px solid #cbd5e1;
            border-radius: 0 4px 4px 0;
          }
          
          .origin-badge {
            display: inline-block;
            font-size: 11px;
            padding: 2px 6px;
            border-radius: 4px;
            font-weight: 600;
          }
          
          .origin-derived { background-color: #e0f2fe; color: #0369a1; }
          .origin-collected { background-color: #d1fae5; color: #065f46; }
          .origin-assigned { background-color: #fef3c7; color: #92400e; }
          .origin-protocol { background-color: #f3e8ff; color: #6b21a8; }
          
          /* Welcome panel styling */
          .welcome-panel {
            text-align: center;
            padding: 48px;
            max-width: 600px;
            margin: 40px auto;
          }
          
          .welcome-icon {
            font-size: 48px;
            color: #0284c7;
            margin-bottom: 24px;
          }
          
          .welcome-title {
            font-size: 24px;
            font-weight: 700;
            color: #0f172a;
            margin: 0 0 12px 0;
          }
          
          .welcome-text {
            color: #64748b;
            font-size: 15px;
            line-height: 1.6;
            margin: 0;
          }
        </style>
        <script>
          <![CDATA[
          function showDataset(dsName) {
            // Hide welcome panel
            var welcome = document.getElementById('welcome-panel');
            if (welcome) welcome.style.display = 'none';

            // Deactivate all panels and menu items
            var panels = document.getElementsByClassName('dataset-panel');
            for (var i = 0; i < panels.length; i++) {
              panels[i].classList.remove('active');
            }
            var items = document.getElementsByClassName('menu-item');
            for (var i = 0; i < items.length; i++) {
              items[i].classList.remove('active');
            }

            // Activate target panel and menu item
            var targetPanel = document.getElementById('panel-' + dsName);
            if (targetPanel) targetPanel.classList.add('active');

            var targetItem = document.getElementById('menu-' + dsName);
            if (targetItem) targetItem.classList.add('active');
          }
          ]]>
        </script>
      </head>
      <body>
        
        <!-- Sidebar Navigation -->
        <div class="sidebar">
          <div class="sidebar-header">
            <h2 class="sidebar-title">TROPIC STUDY</h2>
            <div class="sidebar-subtitle">ADaM Metadata Spec</div>
          </div>
          <div class="sidebar-menu">
            <div class="menu-section-title">Datasets</div>
            <xsl:for-each select="//def:ItemGroupDef">
              <div class="menu-item" id="menu-{@Name}" onclick="showDataset('{@Name}')">
                <span><xsl:value-of select="@Name"/></span>
                <span class="dataset-badge"><xsl:value-of select="@Role"/></span>
              </div>
            </xsl:for-each>
          </div>
        </div>
        
        <!-- Main Content Area -->
        <div class="main-content">
          
          <!-- Top Bar -->
          <div class="top-bar">
            <div class="study-info">
              <h1 class="study-title">TROPIC Phase III Re-Analysis (Study EFC6193)</h1>
              <div class="metadata-pills">
                <span class="pill pill-blue">DefineVersion: 2.1.0</span>
                <span class="pill">ADaM Version: 1.3</span>
                <span class="pill">AsOf: <xsl:value-of select="//def:Define/@AsOfDateTime"/></span>
              </div>
            </div>
          </div>
          
          <!-- Main Scrolling Viewport -->
          <div class="content-view">
            
            <!-- Default Welcome Panel -->
            <div class="welcome-panel" id="welcome-panel">
              <div class="welcome-icon">📊</div>
              <h3 class="welcome-title">Welcome to TROPIC ADaM Metadata Viewer</h3>
              <p class="welcome-text">
                Select a dataset from the sidebar menu to view detailed subject-level definitions, variables, types, source origins, and SAS derivation methods.
              </p>
            </div>
            
            <!-- Dynamic Dataset Panels -->
            <xsl:for-each select="//def:ItemGroupDef">
              <xsl:variable name="dsName" select="@Name"/>
              <div class="dataset-panel" id="panel-{$dsName}">
                
                <!-- Dataset Overview Card -->
                <div class="card">
                  <div class="card-title">📦 Dataset Profile: <xsl:value-of select="$dsName"/></div>
                  <div class="grid-2">
                    <div class="meta-item">
                      <div class="meta-label">Description</div>
                      <div class="meta-value"><xsl:value-of select="@Label"/></div>
                    </div>
                    <div class="meta-item">
                      <div class="meta-label">Structure</div>
                      <div class="meta-value"><xsl:value-of select="@Structure"/></div>
                    </div>
                    <div class="meta-item">
                      <div class="meta-label">Role</div>
                      <div class="meta-value"><xsl:value-of select="@Role"/></div>
                    </div>
                    <div class="meta-item">
                      <div class="meta-label">Purpose</div>
                      <div class="meta-value"><xsl:value-of select="@Purpose"/></div>
                    </div>
                  </div>
                  <xsl:if test="def:Description">
                    <div style="margin-top: 16px; border-top: 1px solid #f1f5f9; padding-top: 16px;">
                      <div class="meta-label">Clinical Purpose</div>
                      <div class="meta-value" style="font-weight: normal; color: #475569;"><xsl:value-of select="def:Description"/></div>
                    </div>
                  </xsl:if>
                </div>
                
                <!-- Variables Definition Card -->
                <div class="card">
                  <div class="card-title">📝 Variable Definitions</div>
                  <table>
                    <thead>
                      <tr>
                        <th style="width: 15%;">Variable</th>
                        <th style="width: 25%;">Label</th>
                        <th style="width: 10%;">Type</th>
                        <th style="width: 8%;">Length</th>
                        <th style="width: 12%;">Origin</th>
                        <th style="width: 30%;">Source / Derivation Method</th>
                      </tr>
                    </thead>
                    <tbody>
                      <xsl:for-each select="def:ItemRef">
                        <xsl:variable name="itemOID" select="@ItemOID"/>
                        <xsl:variable name="itemDef" select="//def:ItemDef[@OID=$itemOID]"/>
                        <tr>
                          <td><span class="var-name"><xsl:value-of select="$itemDef/@Name"/></span></td>
                          <td><xsl:value-of select="$itemDef/@Label"/></td>
                          <td><span class="var-type"><xsl:value-of select="$itemDef/@DataType"/></span></td>
                          <td><xsl:value-of select="$itemDef/@Length"/></td>
                          <td>
                            <xsl:if test="$itemDef/def:Origin">
                              <xsl:variable name="origType" select="$itemDef/def:Origin/@Type"/>
                              <xsl:variable name="badgeClass">
                                <xsl:choose>
                                  <xsl:when test="$origType = 'Derived'">origin-derived</xsl:when>
                                  <xsl:when test="$origType = 'Collected'">origin-collected</xsl:when>
                                  <xsl:when test="$origType = 'Assigned'">origin-assigned</xsl:when>
                                  <xsl:when test="$origType = 'Protocol'">origin-protocol</xsl:when>
                                  <xsl:otherwise></xsl:otherwise>
                                </xsl:choose>
                              </xsl:variable>
                              <span class="origin-badge {$badgeClass}"><xsl:value-of select="$origType"/></span>
                            </xsl:if>
                          </td>
                          <td>
                            <xsl:choose>
                              <xsl:when test="@MethodOID">
                                <xsl:variable name="methodOID" select="@MethodOID"/>
                                <div class="method-desc">
                                  <xsl:value-of select="//def:MethodDef[@OID=$methodOID]/def:Description/def:TranslatedText"/>
                                </div>
                              </xsl:when>
                              <xsl:otherwise>
                                <div style="color: #94a3b8; font-style: italic; font-size: 12px;">Direct mapping / sponsor defined</div>
                              </xsl:otherwise>
                            </xsl:choose>
                          </td>
                        </tr>
                      </xsl:for-each>
                    </tbody>
                  </table>
                </div>
                
              </div>
            </xsl:for-each>
            
          </div>
        </div>
        
      </body>
    </html>
  </xsl:template>
</xsl:stylesheet>
