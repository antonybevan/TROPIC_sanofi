<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                xmlns:def="http://www.cdisc.org/ns/def/v2.1">
  <xsl:template match="/">
    <html>
      <head>
        <title>TROPIC ADaM Metadata Specification (Define-XML v2.1)</title>
        <style>
          body { font-family: 'Segoe UI', Arial, sans-serif; background-color: #f8f9fa; color: #333; margin: 40px; }
          h1 { color: #002d62; }
          .card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
          table { width: 100%; border-collapse: collapse; margin-top: 20px; }
          th, td { padding: 12px; border-bottom: 1px solid #ddd; text-align: left; }
          th { background-color: #002d62; color: white; }
        </style>
      </head>
      <body>
        <div class="card">
          <h1>TROPIC CDISC ADaM Define-XML Metadata</h1>
          <p>This interactive stylesheet displays the validated datasets and definitions of the re-analysis.</p>
          <table>
            <thead>
              <tr>
                <th>Dataset Name</th>
                <th>Label</th>
                <th>Role</th>
                <th>Structure</th>
              </tr>
            </thead>
            <tbody>
              <xsl:for-each select="//def:ItemGroupDef">
                <tr>
                  <td><strong><xsl:value-of select="@Name"/></strong></td>
                  <td><xsl:value-of select="@Label"/></td>
                  <td><xsl:value-of select="@Role"/></td>
                  <td><xsl:value-of select="@Structure"/></td>
                </tr>
              </xsl:for-each>
            </tbody>
          </table>
        </div>
      </body>
    </html>
  </xsl:template>
</xsl:stylesheet>
