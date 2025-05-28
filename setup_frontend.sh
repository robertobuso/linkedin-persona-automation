#!/bin/bash

# Setup script to create frontend files in the correct structure
echo "📁 Setting up frontend directory structure..."

# Create frontend directory
mkdir -p frontend

# Create the main HTML file
cat > frontend/index.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LinkedIn Automation MVP</title>
    <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🚀</text></svg>">
    
    <!-- Load configuration -->
    <script>
        window.APP_CONFIG = {
            API_BASE_URL: window.location.hostname === 'localhost' 
                ? 'http://localhost:8000/api/v1'
                : '/api/v1',
            APP_NAME: 'LinkedIn Automation MVP',
            VERSION: '1.0.0'
        };
    </script>
    
    <!-- React CDN -->
    <script src="https://unpkg.com/react@18/umd/react.production.min.js"></script>
    <script src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js"></script>
    <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
    
    <style>
        /* Include all the CSS from the artifact here */
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; }
        /* ... rest of the CSS ... */
    </style>
</head>
<body>
    <div id="root">
        <div style="display: flex; justify-content: center; align-items: center; height: 100vh; flex-direction: column; color: white;">
            <div style="width: 40px; height: 40px; border: 4px solid #f3f3f3; border-top: 4px solid #0077b5; border-radius: 50%; animation: spin 1s linear infinite;"></div>
            <p style="margin-top: 1rem;">Loading LinkedIn Automation...</p>
        </div>
    </div>

    <script type="text/babel">
        // Include all the React code from the artifact here
        // ... React components ...
    </script>
</body>
</html>
EOF

# Create nginx config
cat > frontend/nginx.conf << 'EOF'
server {
    listen 80;
    server_name localhost;
    root /usr/share/nginx/html;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://app:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        add_header Access-Control-Allow-Origin *;
        add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS";
        add_header Access-Control-Allow-Headers "Origin, X-Requested-With, Content-Type, Accept, Authorization";
    }

    location /health {
        proxy_pass http://app:8000/health;
    }
}
EOF

# Create frontend Dockerfile
cat > frontend/Dockerfile << 'EOF'
FROM nginx:alpine

COPY index.html /usr/share/nginx/html/
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
EOF

echo "✅ Frontend files created successfully!"
echo "📁 Files created:"
echo "   - frontend/index.html"
echo "   - frontend/nginx.conf" 
echo "   - frontend/Dockerfile"
echo ""
echo "🚀 Now run: chmod +x start_mvp.sh && ./start_mvp.sh"