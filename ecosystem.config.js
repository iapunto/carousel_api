module.exports = {
    apps: [{
        name: "carousel-api",
        script: "wsgi.py",
        interpreter: "venv/Scripts/python.exe",
        instances: "1",
        autorestart: true,
        watch: false,
        max_memory_restart: "1G",
        env: {
            PORT: 5000,
            ENVIRONMENT: "production"
        }
    }]
};