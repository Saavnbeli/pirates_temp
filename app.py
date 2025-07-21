from flask import Flask, request, render_template_string, send_file, jsonify
import os
import tempfile
import threading
import time
import re
from datetime import datetime, timedelta

from Create_Trade_Summary import (
    pull_trade_package_data, 
    create_metric_comparison_table, 
    create_metric_comparison_html
)

app = Flask(__name__)

def extract_page_id(url_or_id):
    url_or_id = url_or_id.strip()
    if re.match(r'^[a-f0-9]{32}$', url_or_id.replace('-', '')):
        return url_or_id.replace('-', '')
    
    patterns = [
        r'notion\.so/.*?([a-f0-9]{32})',
        r'([a-f0-9]{32})'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url_or_id, re.IGNORECASE)
        if match:
            return match.group(1).replace('-', '')
    return None

@app.route('/')
def home():
    return render_template_string('''
<!DOCTYPE html>
<html>
<head>
    <title>Trade Analysis</title>
    <style>
        body { font-family: Arial; max-width: 600px; margin: 50px auto; padding: 20px; }
        input { width: 100%; padding: 10px; margin: 10px 0; font-size: 16px; }
        button { width: 100%; padding: 15px; background: #007bff; color: white; border: none; font-size: 16px; }
    </style>
</head>
<body>
    <h1>Trade Package Analysis</h1>
    <form id="form">
        <input type="text" id="url" placeholder="Paste Notion URL here" required>
        <button type="submit">Generate Report</button>
    </form>
    <div id="status"></div>
    
    <script>
        document.getElementById('form').onsubmit = function(e) {
            e.preventDefault();
            document.getElementById('status').innerHTML = 'Processing...';
            
            fetch('/analyze', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({url: document.getElementById('url').value})
            })
            .then(r => r.json())
            .then(data => {
                if (data.success) {
                    document.getElementById('status').innerHTML = 
                        '<a href="' + data.download_url + '" target="_blank">Download Report</a>';
                    window.open(data.download_url, '_blank');
                } else {
                    document.getElementById('status').innerHTML = 'Error: ' + data.error;
                }
            });
        };
    </script>
</body>
</html>
    ''')

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        data = request.get_json()
        notion_url = data.get('url', '').strip()
        
        page_id = extract_page_id(notion_url)
        if not page_id:
            return jsonify({"success": False, "error": "Invalid Notion URL"})
        
        pkg = pull_trade_package_data(page_id)
        if not pkg:
            return jsonify({"success": False, "error": "Could not get package data"})
        
        package_name = pkg["package"].get("name", "Unknown")
        df = create_metric_comparison_table(pkg, save_to_excel=False, output_html=False)
        html = create_metric_comparison_html(df, package_name=package_name, include_plots=True, package_data=pkg, plot_type="all")
        
        filename = f"{package_name.replace(' ', '_')}_Analysis.html"
        filepath = os.path.join(tempfile.gettempdir(), filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html)
        
        return jsonify({
            "success": True,
            "package_name": package_name,
            "download_url": f"/download/{filename}"
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/download/<filename>')
def download_file(filename):
    filepath = os.path.join(tempfile.gettempdir(), filename)
    if os.path.exists(filepath):
        return send_file(filepath, as_attachment=True)
    return "File not found", 404

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)