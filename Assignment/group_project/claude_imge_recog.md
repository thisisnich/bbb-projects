# API Key should be set as environment variable: ANTHROPIC_API_KEY

curl https://api.anthropic.com/v1/messages \
        --header "x-api-key: YOUR_API_KEY_HERE" \
        --header "anthropic-version: 2023-06-01" \
        --header "content-type: application/json" \
        --data \
    '{
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 1024,
        "messages": [
            {"role": "user", "content": "Hello, world"}
        ]
    }'


# Basketball Court People Counter - Quick Start Guide

## Prerequisites

- Python 3.7+
- Anthropic API account

## Installation

```bash
pip install flask anthropic
```

## Setup

### 1. Get API Key
- Sign up at https://console.anthropic.com
- Navigate to API Keys section
- Create new API key
- Copy the key (starts with `sk-ant-api03-...`)

### 2. Set Environment Variable

**Linux/Mac:**
```bash
export ANTHROPIC_API_KEY='your-api-key-here'
```

**Windows (CMD):**
```cmd
set ANTHROPIC_API_KEY=your-api-key-here
```

**Windows (PowerShell):**
```powershell
$env:ANTHROPIC_API_KEY='your-api-key-here'
```

## Basic Implementation

### Minimal Server (app.py)

```python
from flask import Flask, request, jsonify, render_template_string
import anthropic
import base64
import json
import os

app = Flask(__name__)

# Initialize API client
client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

# Basic HTML (simplified version)
HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>Basketball Counter</title>
</head>
<body>
    <h1>Basketball Court People Counter</h1>
    <input type="file" id="imageInput" accept="image/*">
    <button onclick="countPeople()">Count People</button>
    <div id="result"></div>
    
    <script>
        let selectedFile;
        document.getElementById('imageInput').addEventListener('change', (e) => {
            selectedFile = e.target.files[0];
        });
        
        async function countPeople() {
            if (!selectedFile) return alert('Select an image first');
            
            const formData = new FormData();
            formData.append('image', selectedFile);
            
            const response = await fetch('/count', {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            document.getElementById('result').innerHTML = 
                `<h2>Count: ${data.count}</h2><p>${data.details}</p>`;
        }
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML)

@app.route('/count', methods=['POST'])
def count_people():
    try:
        file = request.files['image']
        image_data = base64.standard_b64encode(file.read()).decode('utf-8')
        
        message = client.messages.create(
            model='claude-sonnet-4-20250514',
            max_tokens=1000,
            messages=[{
                'role': 'user',
                'content': [
                    {
                        'type': 'image',
                        'source': {
                            'type': 'base64',
                            'media_type': file.content_type,
                            'data': image_data,
                        },
                    },
                    {
                        'type': 'text',
                        'text': 'Count people in this basketball court image. Return only JSON: {"count": <number>, "details": "<description>"}'
                    }
                ],
            }],
        )
        
        result = json.loads(message.content[0].text.strip().replace('```json', '').replace('```', ''))
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
```

## Run

```bash
python app.py
```

Open browser: **http://localhost:5000**

## Usage

1. Click "Choose File" and select a basketball court image
2. Click "Count People"
3. See the results displayed

## API Response Format

```json
{
  "count": 10,
  "details": "Basketball game in progress with players on court",
  "breakdown": "8 players, 2 referees"
}
```

## Cost Estimate

- Per image: ~$0.01 - $0.05
- Depends on image size and response detail

## Troubleshooting

**"API key not set" error:**
- Verify environment variable is set
- Restart terminal after setting variable

**"File too large" error:**
- Add to app.py: `app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024`

**"JSON decode error":**
- API response may include markdown formatting
- Code strips `\`\`\`json` automatically

## Production Checklist

- [ ] Never commit API key to git
- [ ] Add rate limiting
- [ ] Add file size validation
- [ ] Add proper error handling
- [ ] Use HTTPS
- [ ] Set `debug=False` in production

## Resources

- API Docs: https://docs.anthropic.com
- Pricing: https://www.anthropic.com/pricing
- Support: https://support.anthropic.com